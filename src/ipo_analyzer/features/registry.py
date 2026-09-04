"""
Feature registry — metadata for every feature in the system.

Each feature declares:
- its name and type
- which source observation it depends on
- its eligibility rule: the rule that determines whether it can be
  included in a feature snapshot at a given decision_timestamp.

The eligibility rule is the primary point-in-time leakage guard.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from ipo_analyzer.domain.ipo import IPO


class EligibilityRule(str, Enum):
    """When is this feature available relative to the IPO timeline?"""

    ALWAYS = "ALWAYS"
    """Available at any decision_timestamp (e.g., issue price from DRHP)."""

    AFTER_CLOSE = "AFTER_CLOSE"
    """
    Available only after the subscription window closes (close_date + ~5PM IST).
    This covers final subscription data.
    """

    AFTER_LISTING = "AFTER_LISTING"
    """
    Available only after listing day. Used for post-listing features.
    These must NEVER appear in pre-listing feature snapshots.
    """


@dataclass(frozen=True)
class FeatureDefinition:
    """
    Metadata contract for a single feature.

    name:             Unique feature identifier (snake_case).
    description:      Human-readable explanation.
    eligibility:      When this feature becomes available.
    source:           Where the underlying data comes from.
    dtype:            Expected Python type of the feature value.
    nullable:         If True, the feature can legally be None (missing data).
                      Callers must handle None explicitly.
    version:          Incremented when the computation logic changes.
    """

    name: str
    description: str
    eligibility: EligibilityRule
    source: str
    dtype: type
    nullable: bool = True
    version: str = "1"

    def is_eligible(self, ipo: IPO, decision_timestamp: datetime) -> bool:
        """
        Return True if this feature can be included in a snapshot
        at decision_timestamp for the given IPO.

        This is the leakage gate. A feature is NOT eligible if
        its underlying observation would not yet have been available
        at decision_timestamp.
        """
        from datetime import timezone

        from ipo_analyzer.domain.ipo import TimelineRegime

        if self.eligibility == EligibilityRule.ALWAYS:
            return True

        if self.eligibility == EligibilityRule.AFTER_CLOSE:
            # Subscription close is ~17:00 IST (11:30 UTC) on close_date.
            # We use midnight UTC on close_date + 1 day as a conservative
            # safe-harbour to avoid timezone edge cases.
            import datetime as dt

            close_safe_harbour = datetime(
                ipo.issue_terms.close_date.year,
                ipo.issue_terms.close_date.month,
                ipo.issue_terms.close_date.day,
                tzinfo=timezone.utc,
            ) + dt.timedelta(days=1)
            return decision_timestamp >= close_safe_harbour

        if self.eligibility == EligibilityRule.AFTER_LISTING:
            import datetime as dt

            listing_safe_harbour = datetime(
                ipo.issue_terms.listing_date.year,
                ipo.issue_terms.listing_date.month,
                ipo.issue_terms.listing_date.day,
                tzinfo=timezone.utc,
            ) + dt.timedelta(days=1)
            return decision_timestamp >= listing_safe_harbour

        return False  # pragma: no cover


# ---------------------------------------------------------------------------
# Phase 1 feature registry
# ---------------------------------------------------------------------------
# Only features that can be computed from the 35-record sample are included.
# Do NOT add speculative features here.

ISSUE_PRICE = FeatureDefinition(
    name="issue_price",
    description="Per-share IPO issue price in INR.",
    eligibility=EligibilityRule.ALWAYS,
    source="IssueTerms.issue_price",
    dtype=float,
    nullable=False,
)

LOT_SIZE = FeatureDefinition(
    name="lot_size",
    description="Minimum application lot size (shares per lot).",
    eligibility=EligibilityRule.ALWAYS,
    source="IssueTerms.lot_size",
    dtype=int,
    nullable=True,
)

ISSUE_SIZE_CR = FeatureDefinition(
    name="issue_size_cr",
    description="Total IPO issue size in INR crore.",
    eligibility=EligibilityRule.ALWAYS,
    source="IssueTerms.issue_size_cr",
    dtype=float,
    nullable=True,
)

OFS_FRACTION = FeatureDefinition(
    name="ofs_fraction",
    description=(
        "Fraction of total issue that is Offer-for-Sale (0–1). "
        "Higher OFS fraction may signal promoter exit pressure."
    ),
    eligibility=EligibilityRule.ALWAYS,
    source="IssueTerms.ofs_cr / IssueTerms.issue_size_cr",
    dtype=float,
    nullable=True,
)

FRESH_ISSUE_FRACTION = FeatureDefinition(
    name="fresh_issue_fraction",
    description=(
        "Fraction of total issue that is fresh capital (0–1). "
        "Complement of ofs_fraction."
    ),
    eligibility=EligibilityRule.ALWAYS,
    source="IssueTerms.fresh_issue_cr / IssueTerms.issue_size_cr",
    dtype=float,
    nullable=True,
)

RETAIL_SUBSCRIPTION_X = FeatureDefinition(
    name="retail_subscription_x",
    description=(
        "Final retail investor subscription multiple. "
        "Eligible only after subscription window closes."
    ),
    eligibility=EligibilityRule.AFTER_CLOSE,
    source="SubscriptionSnapshot.retail_subscription_x",
    dtype=float,
    nullable=True,
)

NII_SUBSCRIPTION_X = FeatureDefinition(
    name="nii_subscription_x",
    description="Final NII/HNI subscription multiple (after close).",
    eligibility=EligibilityRule.AFTER_CLOSE,
    source="SubscriptionSnapshot.nii_subscription_x",
    dtype=float,
    nullable=True,
)

QIB_SUBSCRIPTION_X = FeatureDefinition(
    name="qib_subscription_x",
    description=(
        "Final QIB subscription multiple (after close). "
        "May or may not include anchor investors — check qib_includes_anchor."
    ),
    eligibility=EligibilityRule.AFTER_CLOSE,
    source="SubscriptionSnapshot.qib_subscription_x",
    dtype=float,
    nullable=True,
)

TOTAL_SUBSCRIPTION_X = FeatureDefinition(
    name="total_subscription_x",
    description="Overall subscription multiple across all categories (after close).",
    eligibility=EligibilityRule.AFTER_CLOSE,
    source="SubscriptionSnapshot.total_subscription_x",
    dtype=float,
    nullable=True,
)

RETAIL_ALLOTMENT_PROB = FeatureDefinition(
    name="retail_allotment_prob",
    description=(
        "Estimated probability of retail allotment (at least 1 lot). "
        "Derived from retail_subscription_x via SEBI lottery formula: "
        "min(1.0, 1.0 / max(1.0, retail_subscription_x)). "
        "Eligible only after subscription close."
    ),
    eligibility=EligibilityRule.AFTER_CLOSE,
    source="DERIVED from SubscriptionSnapshot.retail_subscription_x",
    dtype=float,
    nullable=True,
)

SEBI_NII_REGIME = FeatureDefinition(
    name="sebi_nii_regime",
    description=(
        "SEBI NII allotment regime in effect for this IPO. "
        "'PRE_2022' or 'POST_2022'. Derived from close_date."
    ),
    eligibility=EligibilityRule.ALWAYS,
    source="DERIVED from IssueTerms.close_date",
    dtype=str,
    nullable=False,
)

TIMELINE_REGIME = FeatureDefinition(
    name="timeline_regime",
    description=(
        "Settlement timeline regime: 'T3' or 'T6'. "
        "Affects capital blocking duration."
    ),
    eligibility=EligibilityRule.ALWAYS,
    source="DERIVED from IssueTerms.close_date",
    dtype=str,
    nullable=False,
)


# The complete Phase 1 feature set
ALL_PHASE1_FEATURES: list[FeatureDefinition] = [
    ISSUE_PRICE,
    LOT_SIZE,
    ISSUE_SIZE_CR,
    OFS_FRACTION,
    FRESH_ISSUE_FRACTION,
    RETAIL_SUBSCRIPTION_X,
    NII_SUBSCRIPTION_X,
    QIB_SUBSCRIPTION_X,
    TOTAL_SUBSCRIPTION_X,
    RETAIL_ALLOTMENT_PROB,
    SEBI_NII_REGIME,
    TIMELINE_REGIME,
]

FEATURE_REGISTRY: dict[str, FeatureDefinition] = {f.name: f for f in ALL_PHASE1_FEATURES}
