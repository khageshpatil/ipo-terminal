"""
Data lineage entities — tracking where data came from and when.

These are system-level records, not domain objects. They support
reproducibility, auditability, and research integrity.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class DataSourceType(str, Enum):
    RESEARCH_CSV = "RESEARCH_CSV"
    NSE_BHAV_COPY = "NSE_BHAV_COPY"
    BSE_BHAV_COPY = "BSE_BHAV_COPY"
    AGGREGATOR_SCRAPE = "AGGREGATOR_SCRAPE"
    MANUAL_ENTRY = "MANUAL_ENTRY"
    SEBI_FILING = "SEBI_FILING"
    PAID_DATABASE = "PAID_DATABASE"


class DataSource(BaseModel):
    """Registry of all data providers used in the system."""

    source_id: str
    name: str
    source_type: DataSourceType
    base_url: Optional[str] = None
    access_method: str  # e.g., "free_download", "paid_api", "manual"
    requires_auth: bool = False
    is_primary_source: bool = False
    notes: Optional[str] = None


class IngestionRun(BaseModel):
    """
    Records one batch of data ingestion.
    Every record loaded into the system must reference an IngestionRun.
    """

    run_id: str
    source_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_attempted: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    error_summary: Optional[str] = None

    @field_validator("started_at", "completed_at")
    @classmethod
    def must_be_utc(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is None:
            raise ValueError("IngestionRun datetimes must be UTC-aware")
        return v


class BacktestRun(BaseModel):
    """
    Records one execution of a backtest or research analysis.
    Results must be reproducible given the same run_id.
    """

    run_id: str
    strategy_name: str
    strategy_version: str
    dataset_description: str
    """Human-readable description of the dataset used (e.g., '35-record confirmed sample')."""
    started_at: datetime
    completed_at: Optional[datetime] = None
    n_ipos: int = 0
    n_ipos_with_outcome: int = 0
    parameters: dict[str, str] = {}

    @field_validator("started_at", "completed_at")
    @classmethod
    def must_be_utc(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is None:
            raise ValueError("BacktestRun datetimes must be UTC-aware")
        return v


# Built-in data sources for Phase 1
RESEARCH_CSV_SOURCE = DataSource(
    source_id="research_csv_v1",
    name="Verified Research Sample CSV (35 records)",
    source_type=DataSourceType.RESEARCH_CSV,
    access_method="local_file",
    requires_auth=False,
    is_primary_source=False,
    notes=(
        "35 individually confirmed Indian Mainboard IPO records (2018-2024). "
        "All prices are SECONDARY_VERIFIED approximations from named news sources. "
        "Must not be used as primary training labels. "
        "Full primary dataset requires NSE Bhav Copy or IPOMatrix subscription."
    ),
)
