"""
Computes metrics from benchmark_results.csv -- both the automated proxy
metrics (retrieval_success, keyword_match, hallucination_flag) and, if
you've filled any of them in, TRUE accuracy from your own manual review
in the human_verified_correct column.

Workflow:
    1. Run run_benchmark.py -- produces benchmark_results.csv
    2. Open benchmark_results.csv in Excel/Google Sheets/etc, read the
       "answer" column, and fill in "human_verified_correct" for each
       row with one of: correct / incorrect / partial
       (You don't have to review every row -- this script reports
       accuracy over whatever you've reviewed so far, plus how many
       rows are still unreviewed, so you always know your coverage.)
    3. Save the CSV (keep it as .csv, not .xlsx, when saving from Excel)
    4. Run: python analyze_results.py
       Re-run this anytime after adding more reviews -- it doesn't touch
       the models at all, so it's instant and free.

This also prints automated-vs-human agreement, so you can see how much
you can actually trust keyword_match/hallucination_flag as a stand-in
for real correctness on YOUR specific data -- if they diverge a lot from
your manual judgments, lean more on manual review going forward.
"""

import argparse
import csv
from pathlib import Path
from statistics import mean

RESULTS_PATH = Path("benchmark_results.csv")

VERDICT_SCORES = {"correct": 1.0, "incorrect": 0.0, "partial": 0.5}


def load_rows(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def is_reviewed(row):
    v = (row.get("human_verified_correct") or "").strip().lower()
    return v in VERDICT_SCORES


def human_score(row):
    v = (row.get("human_verified_correct") or "").strip().lower()
    return VERDICT_SCORES.get(v)


def rate(rows, predicate):
    gradable = [r for r in rows if predicate(r) is not None]
    if not gradable:
        return None, 0
    passed = sum(1 for r in gradable if predicate(r))
    return passed / len(gradable), len(gradable)


def analyze_group(rows, label):
    n = len(rows)
    reviewed = [r for r in rows if is_reviewed(r)]
    unreviewed_count = n - len(reviewed)

    print(f"\n{label} (n={n}):")

    if reviewed:
        human_acc = mean(human_score(r) for r in reviewed)
        print(f"  Human-verified accuracy:  {human_acc:.1%}  ({len(reviewed)}/{n} reviewed, {unreviewed_count} still blank)")
    else:
        print(f"  Human-verified accuracy:  not available yet -- 0/{n} rows have human_verified_correct filled in")

    retrieval_rate, retrieval_n = rate(rows, lambda r: None if r["retrieval_success"] == "N/A" else r["retrieval_success"] == "PASS")
    keyword_rate, keyword_n = rate(rows, lambda r: None if r["keyword_match"] == "N/A" else r["keyword_match"] == "PASS")
    halluc_rate, halluc_n = rate(rows, lambda r: None if r["hallucination_flag"] == "N/A" else r["hallucination_flag"] in ("NO_CONTEXT_CONFIDENT_ANSWER", "UNGROUNDED_CLAIM"))

    if retrieval_rate is not None:
        print(f"  Retrieval success:        {retrieval_rate:.1%}  ({retrieval_n} gradable)")
    if keyword_rate is not None:
        print(f"  Keyword match (proxy):    {keyword_rate:.1%}  ({keyword_n} gradable)")
    if halluc_rate is not None:
        print(f"  Hallucination rate (proxy): {halluc_rate:.1%}  ({halluc_n} gradable)")

    latencies = [float(r["latency_seconds"]) for r in rows if r.get("latency_seconds")]
    if latencies:
        print(f"  Avg latency:              {mean(latencies):.1f}s  (min={min(latencies):.1f}s, max={max(latencies):.1f}s)")

    confidences = [float(r["confidence_pct"]) for r in rows if r.get("confidence_pct")]
    if confidences:
        print(f"  Avg confidence:           {mean(confidences):.1%}")

    # How well does the automated keyword_match proxy actually agree
    # with your manual judgment, on the rows where both exist?
    both = [r for r in reviewed if r["keyword_match"] != "N/A"]
    if both:
        agree = sum(1 for r in both if (r["keyword_match"] == "PASS") == (human_score(r) >= 0.5))
        print(f"  keyword_match vs human agreement: {agree/len(both):.1%}  ({len(both)} rows with both)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(RESULTS_PATH))
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"❌ {path} not found -- run run_benchmark.py first.")
        return

    rows = load_rows(path)
    if not rows:
        print(f"❌ {path} is empty.")
        return

    print(f"Loaded {len(rows)} rows from {path.absolute()}")

    print(f"\n{'='*80}\nOVERALL\n{'='*80}")
    analyze_group(rows, "All models combined")

    print(f"\n{'='*80}\nBY MODEL\n{'='*80}")
    for model in sorted(set(r["model"] for r in rows)):
        analyze_group([r for r in rows if r["model"] == model], model)

    print(f"\n{'='*80}\nBY CATEGORY (all models combined)\n{'='*80}")
    for cat in sorted(set(r["category"] for r in rows)):
        analyze_group([r for r in rows if r["category"] == cat], cat)

    total_unreviewed = sum(1 for r in rows if not is_reviewed(r))
    if total_unreviewed:
        print(f"\n{'='*80}")
        print(f"⚠️  {total_unreviewed}/{len(rows)} rows still need human_verified_correct filled in")
        print(f"    for a real accuracy number. Automated metrics above are proxies only.")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
