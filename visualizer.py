import pandas as pd
from matplotlib.figure import Figure


def create_sentiment_figure(summary: dict) -> Figure:
    """Creates a Matplotlib bar chart of Positive, Neutral, and Negative counts."""
    fig = Figure(figsize=(5.5, 3.8), dpi=100)
    ax = fig.add_subplot(111)

    labels = ["Positive", "Neutral", "Negative"]
    values = [summary.get("Positive", 0), summary.get("Neutral", 0), summary.get("Negative", 0)]
    colors = ["#00897B", "#78909C", "#E53935"]

    bars = ax.bar(labels, values, color=colors, width=0.5)
    ax.set_title("Sentiment Counts", fontsize=12, fontweight="bold")
    ax.set_ylabel("Number of Reviews")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{int(height):,}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    fig.tight_layout()
    return fig


def create_drift_figure(monthly_drift: pd.Series) -> Figure:
    """Creates a Matplotlib line chart of monthly average sentiment (drift)."""
    fig = Figure(figsize=(5.5, 3.8), dpi=100)
    ax = fig.add_subplot(111)

    if monthly_drift.empty:
        ax.text(
            0.5,
            0.5,
            "No valid date column found in CSV\nfor monthly drift analysis.",
            ha="center",
            va="center",
            fontsize=10,
            color="gray",
        )
        ax.set_axis_off()
        return fig

    ax.plot(
        monthly_drift.index,
        monthly_drift.values,
        marker="o",
        color="#1E88E5",
        linewidth=2,
    )
    ax.set_title("Monthly Average Sentiment (Drift)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Avg VADER Compound Score")
    ax.set_xlabel("Month")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.tick_params(axis="x", rotation=35)

    fig.tight_layout()
    return fig


def export_to_csv(df: pd.DataFrame, filepath: str) -> None:
    """Exports the analyzed and redacted DataFrame to a CSV file."""
    df.to_csv(filepath, index=False, encoding="utf-8")
