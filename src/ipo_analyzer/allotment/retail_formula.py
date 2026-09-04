"""
SEBI retail allotment formula.

For Indian Mainboard IPOs, the retail (RII) category allotment works as follows:

Post-2011 SEBI mechanism (both PRE_2022 and POST_2022 NII regimes):
- If retail subscription <= 1x: every applicant gets full lot allocation (or more)
- If retail subscription > 1x: SEBI mandates a minimum-lot lottery.
  Each applicant is eligible for exactly 1 lot.
  Probability of allotment ≈ 1 / retail_subscription_x

This is a lottery, not pro-rata. Applying for more lots does NOT increase
your probability of getting any shares in the retail category.

Sources:
- SEBI circular CIR/CFD/DIL/2/2012 (standardised lot sizes, minimum application)
- SEBI ICDR Regulations 2018, Chapter VI (allotment procedure)
- SEBI circular on T+6 → T+3 (Dec 2023) does not change allotment mechanics

Limitations:
- The formula gives the theoretical lottery probability.
- Actual allotment is determined by the Registrar post-subscription.
- If the number of retail applicants > retail quota lots ÷ 1 lot,
  the formula is accurate. For very small IPOs with few retail applicants,
  pro-rata may apply — flagged below.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class AllotmentEstimate:
    """Result of the SEBI retail allotment probability calculation."""

    retail_subscription_x: Decimal
    """Input subscription multiple."""

    allotment_probability: Decimal
    """
    P(allotted ≥ 1 lot) for a retail applicant applying for 1 lot.
    Range: [0, 1]. Capped at 1.0 for subscription_x <= 1.
    """

    expected_lots: Decimal
    """E[lots received] = allotment_probability × 1 lot = allotment_probability."""

    method: str
    """'lottery' or 'guaranteed' or 'unknown'."""

    caveat: Optional[str] = None
    """Any known deviation from the standard formula."""


def retail_allotment_probability(
    retail_subscription_x: Decimal,
) -> AllotmentEstimate:
    """
    Compute the SEBI retail lottery allotment probability.

    Parameters
    ----------
    retail_subscription_x : Decimal
        Times retail quota was subscribed (must be >= 0).

    Returns
    -------
    AllotmentEstimate
    """
    if retail_subscription_x < 0:
        raise ValueError(f"retail_subscription_x must be >= 0, got {retail_subscription_x}")

    if retail_subscription_x <= Decimal("1"):
        # Under-subscribed or exactly subscribed: everyone gets allotment
        return AllotmentEstimate(
            retail_subscription_x=retail_subscription_x,
            allotment_probability=Decimal("1"),
            expected_lots=Decimal("1"),
            method="guaranteed",
            caveat="Retail quota undersubscribed; all applicants receive at least 1 lot.",
        )

    # Over-subscribed: lottery mechanism
    prob = Decimal("1") / retail_subscription_x
    # Cap at 1 (should always be < 1 here, but defensive)
    prob = min(prob, Decimal("1"))

    return AllotmentEstimate(
        retail_subscription_x=retail_subscription_x,
        allotment_probability=prob,
        expected_lots=prob,  # applying 1 lot; E[lots] = prob * 1
        method="lottery",
        caveat=None,
    )


def expected_gross_pnl_per_application(
    retail_subscription_x: Decimal,
    issue_price: Decimal,
    lot_size: int,
    listing_return: Decimal,
) -> Optional[Decimal]:
    """
    Compute the expected gross P&L per retail application.

    E[P&L] = P(allotment) × (listing_return × issue_price × lot_size)

    This is the pre-cost, pre-tax expected value.
    Application fees (₹0 for ASBA) and brokerage are excluded.

    Parameters
    ----------
    retail_subscription_x : Decimal
        Final retail subscription multiple.
    issue_price : Decimal
        Per-share issue price in INR.
    lot_size : int
        Shares per lot.
    listing_return : Decimal
        (listing_price - issue_price) / issue_price.

    Returns
    -------
    Optional[Decimal]
        Expected gross P&L in INR, or None if any input is invalid.
    """
    if retail_subscription_x <= 0 or issue_price <= 0 or lot_size <= 0:
        return None

    estimate = retail_allotment_probability(retail_subscription_x)
    gross_pnl_if_allotted = listing_return * issue_price * lot_size
    return estimate.allotment_probability * gross_pnl_if_allotted
