import pandas as pd
from matplotlib.figure import Figure


def create_sentiment_figure(summary: dict) -> Figure:

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

    df.to_csv(filepath, index=False, encoding="utf-8")
import pandas as pd
from matplotlib.figure import Figure

# Shared Dark Theme Palette
BG_CARD = "#1E293B"
TEXT_MAIN = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
GRID_COLOR = "#334155"


def _style_axes(ax):

    ax.set_facecolor(BG_CARD)
    ax.tick_params(colors=TEXT_MUTED, labelsize=9)
    ax.xaxis.label.set_color(TEXT_MUTED)
    ax.yaxis.label.set_color(TEXT_MUTED)
    ax.title.set_color(TEXT_MAIN)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(GRID_COLOR)


def create_sentiment_figure(summary: dict) -> Figure:

    fig = Figure(figsize=(8.2, 3.8), dpi=100, facecolor=BG_CARD)

    labels = ["Positive", "Neutral", "Negative"]
    values = [
        summary.get("Positive", 0),
        summary.get("Neutral", 0),
        summary.get("Negative", 0),
    ]
    colors = ["#10B981", "#F59E0B", "#F43F5E"]

    # Left subplot: Bar Chart
    ax1 = fig.add_subplot(121)
    _style_axes(ax1)
    bars = ax1.bar(labels, values, color=colors, width=0.52, zorder=3)
    ax1.set_title("Sentiment Distribution", fontsize=11, fontweight="bold", pad=12)
    ax1.set_ylabel("Review Count")
    ax1.grid(axis="y", linestyle="--", color=GRID_COLOR, alpha=0.6, zorder=0)

    max_val = max(values) if max(values) > 0 else 1
    ax1.set_ylim(0, max_val * 1.18)

    for bar in bars:
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            height + (max_val * 0.03),
            f"{int(height):,}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=TEXT_MAIN,
        )

    # Right subplot: Donut Chart
    ax2 = fig.add_subplot(122)
    ax2.set_facecolor(BG_CARD)
    total = sum(values)
    if total > 0:
        wedges, texts, autotexts = ax2.pie(
            values,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=140,
            pctdistance=0.76,
            wedgeprops={"width": 0.42, "edgecolor": BG_CARD, "linewidth": 2},
            textprops={"color": TEXT_MUTED, "fontsize": 9},
        )
        for autotext in autotexts:
            autotext.set_color(TEXT_MAIN)
            autotext.set_fontweight("bold")
            autotext.set_fontsize(8.5)
        ax2.text(
            0, 0, f"{total:,}\nReviews",
            ha="center", va="center",
            color=TEXT_MAIN, fontsize=10, fontweight="bold"
        )
    ax2.set_title("Sentiment Share", fontsize=11, fontweight="bold", color=TEXT_MAIN, pad=12)

    fig.tight_layout(pad=2.0)
    return fig


def create_drift_figure(monthly_drift: pd.Series) -> Figure:

    fig = Figure(figsize=(6.0, 3.8), dpi=100, facecolor=BG_CARD)
    ax = fig.add_subplot(111)
    _style_axes(ax)

    if monthly_drift.empty:
        ax.text(
            0.5, 0.5,
            "No valid date column found in CSV\nfor monthly drift analysis.",
            ha="center", va="center", fontsize=10, color=TEXT_MUTED,
        )
        ax.set_axis_off()
        return fig

    x = list(range(len(monthly_drift)))
    y = monthly_drift.values
    labels = list(monthly_drift.index)

    ax.plot(x, y, marker="o", color="#38BDF8", linewidth=2.4, markersize=5, zorder=3)
    ax.fill_between(x, y, min(0, float(y.min())), color="#38BDF8", alpha=0.15, zorder=2)
    ax.axhline(0, color="#64748B", linestyle=":", linewidth=1, zorder=1)

    ax.set_title("Monthly Average Sentiment (Drift)", fontsize=11, fontweight="bold", pad=12)
    ax.set_ylabel("Avg VADER Compound Score")
    ax.set_xlabel("Month")
    ax.grid(True, linestyle="--", color=GRID_COLOR, alpha=0.5, zorder=0)

    # Keep x-axis readable if there are many months
    step = max(1, len(labels) // 8)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(labels[::step], rotation=30, ha="right")

    fig.tight_layout(pad=1.8)
    return fig


def export_to_csv(df: pd.DataFrame, filepath: str) -> None:

    df.to_csv(filepath, index=False, encoding="utf-8")
