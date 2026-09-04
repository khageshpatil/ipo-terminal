"""
Data quality and provenance types.

Every observation and derived value in the system carries a DataQuality
flag so that downstream consumers know how much to trust it.
"""

from enum import Enum


class DataQuality(str, Enum):
    """
    Quality classification for every field or observation in the system.

    The classification is ordered from most to least trustworthy:
    PRIMARY_VERIFIED > SECONDARY_VERIFIED > DERIVED > UNVERIFIED > CONFLICTING > MISSING
    """

    PRIMARY_VERIFIED = "PRIMARY_VERIFIED"
    """
    Sourced directly from an authoritative primary source
    (e.g., NSE/BSE Bhav Copy, SEBI regulatory filing).
    No intermediary; timestamp of original data is known.
    """

    SECONDARY_VERIFIED = "SECONDARY_VERIFIED"
    """
    Sourced from a named, credible secondary source that is itself
    consistent with other independent sources (e.g., price confirmed
    by 2+ financial news outlets, not directly from exchange).
    May be approximate (marked with ~ in research CSVs).
    Must NOT be used as a training label without upgrade to PRIMARY_VERIFIED.
    """

    DERIVED = "DERIVED"
    """
    Computed deterministically from one or more verified observations
    (e.g., listing_return derived from issue_price and listing_price,
    or retail_allotment_prob derived from retail_subscription_x via SEBI formula).
    Quality of derived value inherits the lowest quality of its inputs.
    """

    UNVERIFIED = "UNVERIFIED"
    """
    From a single, unnamed, or uncorroborated source.
    Do not use in model training. Document in data quality report.
    """

    CONFLICTING = "CONFLICTING"
    """
    Two or more sources provide materially different values.
    Both values must be preserved. The field must not be silently resolved.
    Requires manual investigation before use.
    """

    MISSING = "MISSING"
    """
    The field is known to be absent. This is not a null — it explicitly
    documents that the value was sought but not found.
    Never impute a MISSING value without changing quality to DERIVED or UNVERIFIED.
    """

    def is_usable_for_training(self) -> bool:
        """
        Returns True only if this quality level is suitable as a model
        training label or feature. Secondary-verified approximate prices
        are explicitly excluded.
        """
        return self == DataQuality.PRIMARY_VERIFIED

    def is_usable_for_research(self) -> bool:
        """
        Returns True if this quality is sufficient for descriptive
        research statistics (base rate, distribution). Secondary-verified
        values are acceptable here but must be flagged in output.
        """
        return self in (DataQuality.PRIMARY_VERIFIED, DataQuality.SECONDARY_VERIFIED)

    def is_usable_as_feature(self) -> bool:
        """
        Returns True if this quality is sufficient as an input feature
        (not label) in a model. Derived features from verified inputs are
        acceptable; unverified or conflicting are not.
        """
        return self in (
            DataQuality.PRIMARY_VERIFIED,
            DataQuality.SECONDARY_VERIFIED,
            DataQuality.DERIVED,
        )
