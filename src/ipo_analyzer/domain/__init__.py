"""
ipo_analyzer.domain — canonical domain model.

Import the most commonly used entities from this package directly.
"""

from ipo_analyzer.domain.ipo import (
    Exchange,
    IPO,
    IssueTerms,
    IssueType,
    NiiRegime,
    Segment,
    TimelineRegime,
)
from ipo_analyzer.domain.lineage import (
    BacktestRun,
    DataSource,
    DataSourceType,
    IngestionRun,
    RESEARCH_CSV_SOURCE,
)
from ipo_analyzer.domain.observations import (
    GMPSnapshot,
    MarketSnapshot,
    Observation,
    SubscriptionSnapshot,
)
from ipo_analyzer.domain.outcomes import AllotmentOutcome, ListingOutcome
from ipo_analyzer.domain.quality import DataQuality

__all__ = [
    # Quality
    "DataQuality",
    # IPO core
    "Exchange",
    "IPO",
    "IssueTerms",
    "IssueType",
    "NiiRegime",
    "Segment",
    "TimelineRegime",
    # Observations
    "GMPSnapshot",
    "MarketSnapshot",
    "Observation",
    "SubscriptionSnapshot",
    # Outcomes
    "AllotmentOutcome",
    "ListingOutcome",
    # Lineage
    "BacktestRun",
    "DataSource",
    "DataSourceType",
    "IngestionRun",
    "RESEARCH_CSV_SOURCE",
]
