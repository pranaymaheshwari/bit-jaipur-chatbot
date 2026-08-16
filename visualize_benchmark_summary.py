"""
Standalone visualization for the BIT Jaipur RAG benchmark results.

This does NOT read benchmark_results.csv -- the numbers below are typed
in directly from the analyze_results.py summary output you shared
(76 rows: 64 Gemma + 12 Llama, 0/76 human-reviewed so far). If you
re-run the benchmark and want updated charts, just edit the data
dictionaries below to match the new printed summary -- everything else
in this script stays the same.

For each metric (retrieval success, keyword match, hallucination rate,
latency, confidence) this produces two charts:
  - Model comparison  (Overall vs Gemma 4 e2b vs Llama 3.3-70b)
  - Category comparison (all 11 categories, all models combined)

Usage:
    python visualize_benchmark_summary.py
Requires: pip install matplotlib seaborn pandas
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path

OUTPUT_DIR = Path("benchmark_summary_plots")

# ══════════════════════════════════════════════════════════════════════════════════
# DATA -- typed in directly from your analyze_results.py output.
# Update these if you re-run the benchmark and want fresh charts.
# ══════════════════════════════════════════════════════════════════════════════════

OVERALL = {
    "n": 76, "retrieval_success": 84.3, "keyword_match": 92.1,
    "hallucination_rate": 18.4, "avg_latency": 78.9, "avg_confidence": 50.4,
}

BY_MODEL = {
    "Gemma 4 e2b": {"n": 64, "retrieval_success": 84.7, "keyword_match": 92.2,
                    "hallucination_rate": 17.2, "avg_latency": 90.2, "avg_confidence": 50.1},
    "Llama 3.3-70b": {"n": 12, "retrieval_success": 81.8, "keyword_match": 91.7,
                       "hallucination_rate": 25.0, "avg_latency": 18.4, "avg_confidence": 52.4},
}

# retrieval_success is None for "behavioral" -- those questions (greetings,
# refusals, etc.) don't have an expected source document, so retrieval
# isn't graded for them (matches the "N/A" in the printed summary).
BY_CATEGORY = {
    "about":        {"n": 7,  "retrieval_success": 100.0, "keyword_match": 100.0, "hallucination_rate": 0.0,  "avg_latency": 28.2,  "avg_confidence": 51.2},
    "academics":    {"n": 4,  "retrieval_success": 50.0,  "keyword_match": 100.0, "hallucination_rate": 75.0, "avg_latency": 70.9,  "avg_confidence": 60.9},
    "admissions":   {"n": 11, "retrieval_success": 100.0, "keyword_match": 90.9,  "hallucination_rate": 9.1,  "avg_latency": 114.6, "avg_confidence": 55.7},
    "behavioral":   {"n": 6,  "retrieval_success": None,  "keyword_match": 100.0, "hallucination_rate": 66.7, "avg_latency": 55.2,  "avg_confidence": 25.9},
    "campus_life":  {"n": 7,  "retrieval_success": 85.7,  "keyword_match": 85.7,  "hallucination_rate": 0.0,  "avg_latency": 59.0,  "avg_confidence": 43.4},
    "faculty":      {"n": 16, "retrieval_success": 75.0,  "keyword_match": 100.0, "hallucination_rate": 12.5, "avg_latency": 91.3,  "avg_confidence": 46.9},
    "faqs":         {"n": 4,  "retrieval_success": 100.0, "keyword_match": 100.0, "hallucination_rate": 0.0,  "avg_latency": 70.6,  "avg_confidence": 53.5},
    "fees":         {"n": 7,  "retrieval_success": 100.0, "keyword_match": 100.0, "hallucination_rate": 14.3, "avg_latency": 99.8,  "avg_confidence": 55.2},
    "placements":   {"n": 7,  "retrieval_success": 42.9,  "keyword_match": 42.9,  "hallucination_rate": 14.3, "avg_latency": 65.6,  "avg_confidence": 58.7},
    "policies":     {"n": 4,  "retrieval_success": 100.0, "keyword_match": 100.0, "hallucination_rate": 50.0, "avg_latency": 75.8,  "avg_confidence": 55.9},
    "student_life": {"n": 3,  "retrieval_success": 100.0, "keyword_match": 100.0, "hallucination_rate": 0.0,  "avg_latency": 101.7, "avg_confidence": 57.3},
}

METRICS = [
    ("retrieval_success", "Retrieval Success", "%", (0, 100)),
    ("keyword_match", "Keyword Match (correctness proxy)", "%", (0, 100)),
    ("hallucination_rate", "Hallucination Rate (proxy)", "%", (0, 100)),
    ("avg_latency", "Average Latency", "seconds", None),
    ("avg_confidence", "Average Retrieval Confidence", "%", (0, 100)),
]


def plot_model_comparison(metric_key, title, unit, ylim):
    """Overall vs Gemma vs Llama, for one metric."""
    labels = ["Overall"] + list(BY_MODEL.keys())
    values = [OVERALL[metric_key]] + [BY_MODEL[m][metric_key] for m in BY_MODEL]

    if any(v is None for v in values):
        print(f"⚠️  Skipping model comparison for {metric_key} -- missing data")
        return None

    df = pd.DataFrame({"group": labels, "value": values})
    fig, ax = plt.subplots(figsize=(7, 5))
    palette = ["#888888"] + sns.color_palette("deep", len(BY_MODEL))
    sns.barplot(data=df, x="group", y="value", hue="group", palette=palette, legend=False, ax=ax)

    for i, v in enumerate(values):
        ax.text(i, v + (1 if unit == "%" else max(values) * 0.02), f"{v:.1f}{'%' if unit == '%' else 's'}",
                ha="center", fontsize=10, fontweight="bold")

    if ylim:
        ax.set_ylim(*ylim)
    ax.set_ylabel(unit)
    ax.set_xlabel("")
    ax.set_title(f"{title} -- Model Comparison", fontsize=13, fontweight="bold")
    plt.tight_layout()
    return fig


def plot_category_comparison(metric_key, title, unit, ylim):
    """All 11 categories, all models combined, for one metric."""
    cats = list(BY_CATEGORY.keys())
    values = [BY_CATEGORY[c][metric_key] for c in cats]

    # Filter out categories where this metric is N/A (e.g. retrieval_success
    # for "behavioral"), rather than crashing or silently plotting 0.
    plot_cats = [c for c, v in zip(cats, values) if v is not None]
    plot_values = [v for v in values if v is not None]
    skipped = [c for c, v in zip(cats, values) if v is None]

    df = pd.DataFrame({"category": plot_cats, "value": plot_values}).sort_values("value")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.barplot(data=df, y="category", x="value", hue="category", legend=False, palette="viridis", ax=ax)

    for i, v in enumerate(df["value"]):
        ax.text(v + (1 if unit == "%" else max(plot_values) * 0.02), i, f"{v:.1f}{'%' if unit == '%' else 's'}",
                va="center", fontsize=9)

    if ylim:
        ax.set_xlim(*ylim)
    ax.set_xlabel(unit)
    ax.set_ylabel("")
    subtitle = f" (N/A for: {', '.join(skipped)})" if skipped else ""
    ax.set_title(f"{title} -- By Category{subtitle}", fontsize=12, fontweight="bold")
    plt.tight_layout()
    return fig


def main():
    sns.set_theme(style="whitegrid")
    OUTPUT_DIR.mkdir(exist_ok=True)

    saved = []
    for metric_key, title, unit, ylim in METRICS:
        fig = plot_model_comparison(metric_key, title, unit, ylim)
        if fig:
            path = OUTPUT_DIR / f"{metric_key}_by_model.png"
            fig.savefig(path, dpi=150)
            saved.append(path)

        fig = plot_category_comparison(metric_key, title, unit, ylim)
        if fig:
            path = OUTPUT_DIR / f"{metric_key}_by_category.png"
            fig.savefig(path, dpi=150)
            saved.append(path)

    print(f"\n📊 {len(saved)} charts saved to {OUTPUT_DIR.absolute()}/:")
    for p in saved:
        print(f"   {p.name}")

    plt.show()


if __name__ == "__main__":
    main()
