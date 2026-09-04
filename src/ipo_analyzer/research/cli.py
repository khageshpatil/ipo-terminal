"""
Research CLI — entry point for all command-line research operations.

Usage:
    python -m ipo_analyzer.research.cli --help
    python -m ipo_analyzer.research.cli base-rate
    python -m ipo_analyzer.research.cli base-rate --input data/research/ipo_universe_confirmed_sample.csv
    python -m ipo_analyzer.research.cli base-rate --output-json results/base_rate.json
    python -m ipo_analyzer.research.cli baseline
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ipo_analyzer.data_sources.research_csv import load_research_csv
from ipo_analyzer.research.base_rate import BaseRateReport, compute_base_rate
from ipo_analyzer.strategy.apply_every_ipo import BaselineReport, run_apply_every_ipo

app = typer.Typer(
    name="ipo-research",
    help="IPO Listing-Gain Decision Engine — research commands",
    add_completion=False,
)
console = Console()

_DEFAULT_CSV = Path("data/research/ipo_universe_confirmed_sample.csv")


def _pct(val: float) -> str:
    return f"{val * 100:.1f}%"


def _ret(val: float) -> str:
    sign = "+" if val >= 0 else ""
    return f"{sign}{val * 100:.1f}%"


def _print_return_stats(stats: object, title: str, n_label: str = "") -> None:
    """Print a ReturnStats object as a Rich table."""
    from ipo_analyzer.research.base_rate import ReturnStats

    assert isinstance(stats, ReturnStats)

    t = Table(title=title, show_header=False, min_width=55)
    t.add_column("Metric", style="cyan", min_width=30)
    t.add_column("Value", justify="right")

    label = f"n={stats.n}"
    if n_label:
        label += f" {n_label}"

    t.add_row("Records", label)
    t.add_row("Positive listings", f"{stats.positive_count} ({_pct(stats.positive_rate)})")
    t.add_row("Negative listings", f"{stats.negative_count} ({_pct(stats.negative_rate)})")
    t.add_row("─" * 30, "─" * 10)
    t.add_row("Mean return", _ret(stats.mean))
    t.add_row("Median return", _ret(stats.median))
    t.add_row("Std deviation", f"{stats.std * 100:.1f}%")
    t.add_row("Min return", _ret(stats.min_val))
    t.add_row("Max return", _ret(stats.max_val))
    t.add_row("25th percentile", _ret(stats.p25))
    t.add_row("75th percentile", _ret(stats.p75))
    t.add_row("─" * 30, "─" * 10)
    t.add_row("Return > +5%", _pct(stats.pct_gt_5))
    t.add_row("Return > +10%", _pct(stats.pct_gt_10))
    t.add_row("Return > +15%", _pct(stats.pct_gt_15))
    t.add_row("Return > +20%", _pct(stats.pct_gt_20))
    t.add_row("Return < 0%", _pct(stats.pct_lt_0))
    t.add_row("Return < -5%", _pct(stats.pct_lt_neg5))
    t.add_row("Return < -10%", _pct(stats.pct_lt_neg10))
    t.add_row("Return < -20%", _pct(stats.pct_lt_neg20))

    if stats.quality_counts:
        t.add_row("─" * 30, "─" * 10)
        for q, cnt in stats.quality_counts.items():
            t.add_row(f"Quality: {q}", str(cnt))

    console.print(t)


@app.command("base-rate")
def base_rate_command(
    input_csv: Path = typer.Option(
        _DEFAULT_CSV,
        "--input", "-i",
        help="Path to the verified IPO research CSV.",
        show_default=True,
    ),
    output_json: Optional[Path] = typer.Option(
        None,
        "--output-json", "-o",
        help="If provided, write the full report as JSON to this path.",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show load report details."),
) -> None:
    """
    Compute base-rate statistics from the verified IPO research dataset.

    Outputs: overall stats, by-year breakdown, and mandatory bias warning.
    This is descriptive research only — not model performance.
    """
    console.rule("[bold blue]IPO Base-Rate Analysis[/bold blue]")

    # Load data
    rprint(f"[dim]Loading:[/dim] {input_csv}")
    dataset = load_research_csv(input_csv)

    if verbose:
        console.print(dataset.report.summary())
    else:
        console.print(
            f"[green]Loaded:[/green] {dataset.n_ipos} IPOs, "
            f"{dataset.n_with_outcome} with listing outcomes"
        )
        if dataset.report.has_errors:
            console.print(f"[yellow]Errors:[/yellow] {len(dataset.report.errors)} rows failed")

    # Compute base rate
    report = compute_base_rate(
        outcomes=dataset.outcomes,
        ipos_by_id=dataset.ipos_by_id(),
        dataset_description=str(input_csv),
        n_total_loaded=dataset.n_ipos,
        is_biased_sample=True,
    )

    # Print bias warning prominently
    if report.bias_warning:
        console.print(Panel(
            f"[bold yellow][!] SAMPLING BIAS WARNING[/bold yellow]\n\n{report.bias_warning}",
            border_style="yellow",
            expand=False,
        ))

    # Overall stats
    _print_return_stats(report.overall, "Overall Listing Return Statistics")

    # Year breakdown
    if report.by_year:
        console.rule("[dim]By Year[/dim]")
        for year, ystats in sorted(report.by_year.items()):
            _print_return_stats(ystats, f"Year {year}")

    # Exclusions
    if report.n_excluded > 0:
        console.print(
            f"[dim]Excluded {report.n_excluded} records "
            f"(quality below research threshold).[/dim]"
        )

    # JSON output
    if output_json:
        _write_json_report(report, output_json)
        rprint(f"[green]JSON report written:[/green] {output_json}")

    console.rule()


@app.command("baseline")
def baseline_command(
    input_csv: Path = typer.Option(
        _DEFAULT_CSV,
        "--input", "-i",
        help="Path to the verified IPO research CSV.",
        show_default=True,
    ),
    output_json: Optional[Path] = typer.Option(
        None, "--output-json", "-o", help="Write results as JSON.",
    ),
) -> None:
    """
    Run the Apply-Every-IPO baseline strategy.

    Computes: listing-return baseline + allotment-aware baseline (where data exists).
    This is descriptive research only.
    """
    console.rule("[bold blue]Apply-Every-IPO Baseline[/bold blue]")

    dataset = load_research_csv(input_csv)
    console.print(
        f"[green]Loaded:[/green] {dataset.n_ipos} IPOs, "
        f"{dataset.n_with_outcome} with listing outcomes"
    )

    report = run_apply_every_ipo(
        outcomes=dataset.outcomes,
        ipos_by_id=dataset.ipos_by_id(),
        dataset_description=str(input_csv),
    )

    console.print(Panel(
        f"[bold yellow][!] SAMPLING BIAS WARNING[/bold yellow]\n\n{report.bias_warning}",
        border_style="yellow",
        expand=False,
    ))

    t = Table(title="Apply-Every-IPO — Listing Return Baseline", show_header=False, min_width=55)
    t.add_column("Metric", style="cyan", min_width=30)
    t.add_column("Value", justify="right")
    t.add_row("Total IPOs", str(report.n_total))
    t.add_row("Positive listings", f"{report.n_positive} ({_pct(report.positive_rate)})")
    t.add_row("Negative listings", f"{report.n_negative} ({_pct(1.0 - report.positive_rate)})")
    t.add_row("Mean listing return", _ret(report.mean_listing_return))
    t.add_row("Median listing return", _ret(report.median_listing_return))
    console.print(t)

    if report.n_with_allotment_data > 0:
        ta = Table(title="Allotment-Aware Baseline (subset with subscription data)", show_header=False, min_width=55)
        ta.add_column("Metric", style="cyan", min_width=30)
        ta.add_column("Value", justify="right")
        ta.add_row("IPOs with allotment data", str(report.n_with_allotment_data))
        ta.add_row("IPOs without allotment data", str(report.n_without_allotment_data))
        if report.mean_expected_pnl is not None:
            ta.add_row("Mean expected P&L / application", f"₹{report.mean_expected_pnl:.0f}")
        if report.median_expected_pnl is not None:
            ta.add_row("Median expected P&L / application", f"₹{report.median_expected_pnl:.0f}")
        console.print(ta)
    else:
        console.print(
            "[dim]No allotment-aware results: "
            "retail_subscription_x not available for this sample "
            "(requires full historical subscription data).[/dim]"
        )

    if output_json:
        data = {
            "strategy": report.strategy_name,
            "version": report.strategy_version,
            "dataset": report.dataset_description,
            "n_total": report.n_total,
            "n_positive": report.n_positive,
            "positive_rate": report.positive_rate,
            "mean_listing_return": report.mean_listing_return,
            "median_listing_return": report.median_listing_return,
            "n_with_allotment_data": report.n_with_allotment_data,
        }
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(data, indent=2))
        rprint(f"[green]JSON written:[/green] {output_json}")

    console.rule()


def _write_json_report(report: BaseRateReport, path: Path) -> None:
    """Serialise a BaseRateReport to JSON."""

    def _stats_dict(s: object) -> dict:
        from ipo_analyzer.research.base_rate import ReturnStats
        assert isinstance(s, ReturnStats)
        return {
            "n": s.n,
            "positive_count": s.positive_count,
            "positive_rate": s.positive_rate,
            "mean": s.mean,
            "median": s.median,
            "std": s.std,
            "min": s.min_val,
            "max": s.max_val,
            "p25": s.p25,
            "p75": s.p75,
            "pct_gt_5": s.pct_gt_5,
            "pct_gt_10": s.pct_gt_10,
            "pct_gt_15": s.pct_gt_15,
            "pct_gt_20": s.pct_gt_20,
            "pct_lt_0": s.pct_lt_0,
            "pct_lt_neg5": s.pct_lt_neg5,
            "pct_lt_neg10": s.pct_lt_neg10,
            "pct_lt_neg20": s.pct_lt_neg20,
            "quality_counts": s.quality_counts,
        }

    data = {
        "dataset": report.dataset_description,
        "n_total_loaded": report.n_total_loaded,
        "n_with_outcome": report.n_with_outcome,
        "n_excluded": report.n_excluded,
        "bias_warning": report.bias_warning,
        "overall": _stats_dict(report.overall),
        "by_year": {str(yr): _stats_dict(s) for yr, s in report.by_year.items()},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    app()
