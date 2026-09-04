"""
Point-in-time feature engine.

Core contract:
    get_features(ipo, decision_timestamp, subscription=None) -> FeatureSnapshot

Guarantees:
- Only features whose eligibility is satisfied at decision_timestamp are included.
- Features not yet eligible are listed in missing_features (not silently omitted).
- A LeakageError is raised if a post-listing feature is requested pre-listing
  and enforce_leakage_check=True (the default).

Usage:
    snapshot = get_features(
        ipo=my_ipo,
        decision_timestamp=datetime(2021, 7, 18, tzinfo=timezone.utc),  # after close
        subscription=my_sub_snapshot,
    )
    assert "retail_subscription_x" in snapshot.features
    assert "listing_price" not in snapshot.features  # not yet eligible
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from ipo_analyzer.domain.ipo import IPO
from ipo_analyzer.domain.observations import SubscriptionSnapshot
from ipo_analyzer.features.registry import (
    ALL_PHASE1_FEATURES,
    FEATURE_REGISTRY,
    EligibilityRule,
    FeatureDefinition,
)


class LeakageError(Exception):
    """
    Raised when a feature computation would introduce look-ahead bias.

    This error is a hard guard — it must never be silently caught.
    If you see this error it means an upstream data pipeline is passing
    a wrong decision_timestamp.
    """

    def __init__(self, feature_name: str, decision_ts: datetime, reason: str) -> None:
        super().__init__(
            f"LEAKAGE DETECTED: feature '{feature_name}' is not eligible "
            f"at decision_timestamp={decision_ts.isoformat()}. Reason: {reason}"
        )
        self.feature_name = feature_name
        self.decision_ts = decision_ts
        self.reason = reason


@dataclass
class FeatureSnapshot:
    """
    A feature vector computed for one IPO at one decision_timestamp.

    features:           name → value (None for present-but-missing features)
    ineligible_features: features that exist in the registry but are
                         not yet available at decision_timestamp
    missing_features:   features that are eligible but have no data
    feature_versions:   name → version string (for reproducibility)
    leakage_checked:    True if leakage guard was run
    """

    ipo_id: str
    decision_timestamp: datetime
    features: dict[str, Any] = field(default_factory=dict)
    ineligible_features: list[str] = field(default_factory=list)
    missing_features: list[str] = field(default_factory=list)
    feature_versions: dict[str, str] = field(default_factory=dict)
    leakage_checked: bool = False

    def get(self, name: str, default: Any = None) -> Any:
        """Get feature value, returning default if absent or None."""
        return self.features.get(name, default)

    def has(self, name: str) -> bool:
        """True if the feature is present and non-None."""
        return name in self.features and self.features[name] is not None


def get_features(
    ipo: IPO,
    decision_timestamp: datetime,
    subscription: Optional[SubscriptionSnapshot] = None,
    enforce_leakage_check: bool = True,
) -> FeatureSnapshot:
    """
    Compute a point-in-time feature snapshot for an IPO.

    Parameters
    ----------
    ipo:
        The IPO entity.
    decision_timestamp:
        The simulated or real time at which a decision is being made.
        Must be UTC-aware.
    subscription:
        Final subscription snapshot, if available.
        If decision_timestamp is before subscription close, this will
        be ignored and retail_subscription_x etc. will be ineligible.
    enforce_leakage_check:
        If True (default), raises LeakageError when a AFTER_LISTING
        feature is requested before listing. Set False only in tests
        that are explicitly testing the leakage detection mechanism.

    Returns
    -------
    FeatureSnapshot
        Contains only features that are eligible at decision_timestamp.
    """
    if decision_timestamp.tzinfo is None:
        raise ValueError("decision_timestamp must be UTC-aware")

    snapshot = FeatureSnapshot(
        ipo_id=ipo.ipo_id,
        decision_timestamp=decision_timestamp,
        leakage_checked=enforce_leakage_check,
    )

    terms = ipo.issue_terms

    for feat in ALL_PHASE1_FEATURES:
        eligible = feat.is_eligible(ipo, decision_timestamp)

        if not eligible:
            snapshot.ineligible_features.append(feat.name)
            continue

        # Leakage guard: AFTER_LISTING features must never be included
        # before the listing date (belt-and-suspenders on top of is_eligible)
        if enforce_leakage_check and feat.eligibility == EligibilityRule.AFTER_LISTING:
            from datetime import timedelta

            listing_safe = datetime(
                terms.listing_date.year,
                terms.listing_date.month,
                terms.listing_date.day,
                tzinfo=timezone.utc,
            ) + timedelta(days=1)
            if decision_timestamp < listing_safe:
                raise LeakageError(
                    feat.name,
                    decision_timestamp,
                    f"listing_date={terms.listing_date}; "
                    f"feature eligible only after {listing_safe.isoformat()}",
                )

        # --- Compute feature value ---
        value: Any = None

        if feat.name == "issue_price":
            value = float(terms.issue_price)

        elif feat.name == "lot_size":
            value = terms.lot_size  # may be None

        elif feat.name == "issue_size_cr":
            value = float(terms.issue_size_cr) if terms.issue_size_cr is not None else None

        elif feat.name == "ofs_fraction":
            f = terms.ofs_fraction
            value = float(f) if f is not None else None

        elif feat.name == "fresh_issue_fraction":
            f = terms.fresh_issue_fraction
            value = float(f) if f is not None else None

        elif feat.name == "sebi_nii_regime":
            value = ipo.sebi_nii_regime.value

        elif feat.name == "timeline_regime":
            value = ipo.timeline_regime.value

        elif feat.name == "retail_subscription_x":
            if subscription is not None and subscription.retail_subscription_x is not None:
                value = float(subscription.retail_subscription_x)

        elif feat.name == "nii_subscription_x":
            if subscription is not None and subscription.nii_subscription_x is not None:
                value = float(subscription.nii_subscription_x)

        elif feat.name == "qib_subscription_x":
            if subscription is not None and subscription.qib_subscription_x is not None:
                value = float(subscription.qib_subscription_x)

        elif feat.name == "total_subscription_x":
            if subscription is not None and subscription.total_subscription_x is not None:
                value = float(subscription.total_subscription_x)

        elif feat.name == "retail_allotment_prob":
            if subscription is not None and subscription.retail_subscription_x is not None:
                retail_x = float(subscription.retail_subscription_x)
                value = min(1.0, 1.0 / max(1.0, retail_x))

        # Track value
        snapshot.features[feat.name] = value
        snapshot.feature_versions[feat.name] = feat.version
        if value is None and not feat.nullable:
            # Non-nullable feature has no value — this is a data quality issue
            snapshot.missing_features.append(feat.name)
        elif value is None and feat.nullable:
            snapshot.missing_features.append(feat.name)

    return snapshot
