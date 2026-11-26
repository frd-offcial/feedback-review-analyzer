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

    step = max(1, len(labels) // 8)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(labels[::step], rotation=30, ha="right")

    fig.tight_layout(pad=1.8)
    return fig


def export_to_csv(df: pd.DataFrame, filepath: str) -> None:

    df.to_csv(filepath, index=False, encoding="utf-8")
import pandas as pd
from matplotlib.figure import Figure

BG_CARD = "#11131A"
BG_PLOT = "#11131A"
TEXT_MAIN = "#F4F4F6"
TEXT_MUTED = "#8E92A4"
GRID_COLOR = "#1E2230"


def _style_axes(ax):
    """Applies clean, borderless commercial BI styling to Matplotlib axes."""
    ax.set_facecolor(BG_PLOT)
    ax.tick_params(colors=TEXT_MUTED, labelsize=8.5, length=0, pad=6)
    ax.xaxis.label.set_color(TEXT_MUTED)
    ax.yaxis.label.set_color(TEXT_MUTED)
    ax.title.set_color(TEXT_MAIN)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.spines["bottom"].set_linewidth(1.0)


def create_sentiment_figure(summary: dict) -> Figure:
    """Creates a modern Bar + Thin Donut Ring chart for the Bento Overview."""
    fig = Figure(figsize=(7.6, 3.7), dpi=100, facecolor=BG_CARD)

    labels = ["Positive", "Neutral", "Negative"]
    values = [
        summary.get("Positive", 0),
        summary.get("Neutral", 0),
        summary.get("Negative", 0),
    ]
    colors = ["#10B981", "#F59E0B", "#F43F5E"]

    # Left: Crisp Volume Bar Chart
    ax1 = fig.add_subplot(121)
    _style_axes(ax1)
    bars = ax1.bar(labels, values, color=colors, width=0.42, zorder=3)
    ax1.set_title("Volume Breakdown", fontsize=10.5, fontweight="bold", loc="left", pad=14)
    ax1.grid(axis="y", linestyle="-", color=GRID_COLOR, alpha=0.8, zorder=0)

    max_val = max(values) if max(values) > 0 else 1
    ax1.set_ylim(0, max_val * 1.22)

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

    # Right: Ultra-Thin Modern Donut Ring
    ax2 = fig.add_subplot(122)
    ax2.set_facecolor(BG_PLOT)
    total = sum(values)
    if total > 0:
        _, _, autotexts = ax2.pie(
            values,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=140,
            pctdistance=0.82,
            wedgeprops={"width": 0.28, "edgecolor": BG_CARD, "linewidth": 3},
            textprops={"color": TEXT_MUTED, "fontsize": 8.5, "fontweight": "bold"},
        )
        for autotext in autotexts:
            autotext.set_color(TEXT_MAIN)
            autotext.set_fontsize(8)
        ax2.text(
            0, 0.06, f"{total:,}", ha="center", va="center",
            color=TEXT_MAIN, fontsize=14, fontweight="bold"
        )
        ax2.text(
            0, -0.17, "REVIEWS", ha="center", va="center",
            color=TEXT_MUTED, fontsize=7, fontweight="bold"
        )
    ax2.set_title("Proportion Share", fontsize=10.5, fontweight="bold", color=TEXT_MAIN, pad=14)

    fig.tight_layout(pad=2.0)
    return fig


def create_drift_figure(monthly_drift: pd.Series) -> Figure:
    """Creates an annotated area-gradient Monthly Sentiment Drift line chart."""
    fig = Figure(figsize=(6.4, 3.8), dpi=100, facecolor=BG_CARD)
    ax = fig.add_subplot(111)
    _style_axes(ax)

    if monthly_drift.empty:
        ax.text(
            0.5, 0.5,
            "No valid date column detected in CSV\nfor monthly sentiment drift.",
            ha="center", va="center", fontsize=10, color=TEXT_MUTED,
        )
        ax.set_axis_off()
        return fig

    x = list(range(len(monthly_drift)))
    y = monthly_drift.values
    labels = list(monthly_drift.index)

    # Layered glow line + gradient fill
    ax.plot(x, y, color="#6366F1", linewidth=6, alpha=0.15, zorder=2)
    ax.plot(x, y, marker="o", color="#818CF8", linewidth=2.2, markersize=4.5, zorder=3)
    baseline = min(0.0, float(y.min()))
    ax.fill_between(x, y, baseline, color="#6366F1", alpha=0.12, zorder=1)
    ax.axhline(0, color="#3F445B", linestyle="--", linewidth=1, zorder=1)

    # Highlight lowest point (drift drop) if multiple months exist
    if len(y) > 2:
        min_idx = int(y.argmin())
        ax.scatter([min_idx], [y[min_idx]], color="#F43F5E", s=45, zorder=4)
        ax.annotate(
            f"Low: {y[min_idx]:+.2f}",
            xy=(min_idx, y[min_idx]),
            xytext=(0, -16),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            fontweight="bold",
            color="#FDA4AF",
        )

    ax.set_title("Monthly Sentiment Trajectory (VADER Compound)", fontsize=10.5, fontweight="bold", loc="left", pad=14)
    ax.set_ylabel("Avg Compound Score")
    ax.grid(axis="y", linestyle="-", color=GRID_COLOR, alpha=0.8, zorder=0)

    step = max(1, len(labels) // 8)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(labels[::step], rotation=28, ha="right")

    fig.tight_layout(pad=1.8)
    return fig


def export_to_csv(df: pd.DataFrame, filepath: str) -> None:
    """Exports the analyzed and redacted DataFrame to a CSV file."""
    df.to_csv(filepath, index=False, encoding="utf-8")
