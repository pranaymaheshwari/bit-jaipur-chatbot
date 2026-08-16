"""
Runs BENCHMARK_QUESTIONS (see benchmark_questions.py) against the RAG
pipeline and records:
  - retrieval_success   : did the expected source document actually get
                           retrieved (anywhere in the returned chunks)?
  - keyword_match        : does the answer contain the expected keyword(s)?
                            A PROXY for correctness, not a real grade --
                            see human_verified_correct.
  - hallucination_flag   : automated proxy for ungrounded claims (see
                            grade_hallucination() docstring for exactly
                            what this does and doesn't catch).
  - latency_seconds       : wall-clock time for ask() to return
  - top_sources           : the actual filenames retrieved, for manual
                             source-attribution review
  - confidence_label/pct  : average retrieval similarity score, same
                             logic as the Streamlit app's confidence meter

DEFAULT BEHAVIOR (matches: Gemma is local/free, Llama costs quota):
  - Gemma (ollama): runs the FULL question set (all 64 by default)
  - Llama (groq):   runs a SMALLER STRATIFIED SAMPLE (12 by default) --
                     proportionally spread across every category rather
                     than just taking the first N, so it's still a fair
                     representative comparison, not a biased subset.

Writes benchmark_results.csv, appending each run (doesn't overwrite),
plus a blank human_verified_correct column for you to fill in after
reviewing answers.

Usage:
    python run_benchmark.py                        # Gemma: full set, Llama: 12-question sample
    python run_benchmark.py --groq-sample-size 15   # change the Llama sample size
    python run_benchmark.py --model ollama          # just Gemma, full set
    python run_benchmark.py --model groq             # just Llama, sampled
    python run_benchmark.py --model groq --full-groq # just Llama, ALL questions (burns more quota)
    python run_benchmark.py --limit 10               # quick smoke test override, first 10 questions for whichever model(s) run
"""

import argparse
import csv
import os
import sys
import time
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmark_questions import BENCHMARK_QUESTIONS

RESULTS_PATH = Path("benchmark_results.csv")
RESULTS_FIELDS = [
    "id", "category", "question", "model", "answer",
    "latency_seconds", "retrieval_success", "top_sources",
    "confidence_label", "confidence_pct", "keyword_match",
    "hallucination_flag",
    "expected_keywords", "expected_source_file", "notes",
    "human_verified_correct",  # left blank -- fill in manually after review
]

MODEL_LABELS = {"ollama": "Gemma 4 e2b", "groq": "Llama 3.3-70b"}

# Phrases that indicate the model is legitimately declining to answer
# rather than confidently asserting something -- used to distinguish
# "properly said it doesn't know" from "answered anyway with nothing to
# back it up".
REFUSAL_PHRASES = [
    "couldn't find", "could not find", "don't have this information",
    "do not have this information", "not available in", "not available in my",
    "i can only", "i'm here for serious college information",
    "i am here to provide", "please ask legitimate questions",
    "cannot provide", "unable to find", "no information",
]


def compute_confidence(chunks):
    if not chunks:
        return "No Match", 0.0
    scores = [c.get("score", 0) for c in chunks]
    avg = mean(scores)
    if avg >= 0.60:
        return "High", avg
    elif avg >= 0.45:
        return "Medium", avg
    else:
        return "Low", avg


def grade_retrieval(expected_source_file, chunks):
    """None means this question doesn't test retrieval (behavioral
    questions) -- returns 'N/A' rather than a pass/fail."""
    if expected_source_file is None:
        return "N/A"
    retrieved_files = [c.get("title", "") for c in chunks]
    return "PASS" if expected_source_file in retrieved_files else "FAIL"


def grade_keywords(answer, expected_keywords, match_type):
    if not expected_keywords:
        return "N/A"
    answer_lower = (answer or "").lower()
    hits = [kw for kw in expected_keywords if kw.lower() in answer_lower]
    if match_type == "all":
        return "PASS" if len(hits) == len(expected_keywords) else "FAIL"
    else:  # "any"
        return "PASS" if hits else "FAIL"


def grade_hallucination(answer, chunks, expected_keywords):
    """Automated PROXY for ungrounded claims -- two heuristics, neither
    of which is a substitute for actually reading the answer:

    1. NO_CONTEXT_CONFIDENT_ANSWER: zero chunks were retrieved, but the
       answer doesn't contain any refusal-type phrasing. If there was
       nothing to ground an answer in, a substantive answer anyway is a
       strong hallucination signal.

    2. UNGROUNDED_CLAIM: chunks WERE retrieved, and the answer contains
       one of the expected_keywords (so it made a specific factual
       claim), but that keyword doesn't appear anywhere in the actual
       retrieved chunk CONTENT. This means the model asserted something
       its given context didn't actually say -- even if the claim
       happens to be true, it wasn't grounded in what it was given.

    Returns "GROUNDED" if neither heuristic fires, "N/A" if there are no
    expected_keywords to check against (can't run heuristic 2, and
    heuristic 1 alone is too weak to report confidently for those rows).

    LIMITATIONS: this will miss hallucinated claims that don't happen to
    involve one of the listed expected_keywords, and can false-positive
    if the model paraphrases a fact using different words than what's in
    the source text. Treat this column the same way as keyword_match --
    a first-pass filter to prioritize what to manually review, not a
    final verdict.
    """
    answer_lower = (answer or "").lower()

    if not expected_keywords:
        # No factual claims are expected here (e.g. behavioral/greeting
        # questions) -- not applicable regardless of whether chunks were
        # retrieved. Must be checked before the no-chunks heuristic below,
        # otherwise a normal greeting with no retrieval gets incorrectly
        # flagged as a hallucination just for not needing the knowledge base.
        return "N/A"

    if not chunks:
        is_refusal = any(phrase in answer_lower for phrase in REFUSAL_PHRASES)
        if not is_refusal and answer.strip():
            return "NO_CONTEXT_CONFIDENT_ANSWER"
        return "GROUNDED"

    combined_chunk_text = " ".join(c.get("content", "") for c in chunks).lower()
    keywords_in_answer = [kw for kw in expected_keywords if kw.lower() in answer_lower]

    if not keywords_in_answer:
        # answer didn't make any of the expected claims at all -- that's
        # a correctness/keyword_match problem, not a hallucination one
        return "GROUNDED"

    ungrounded = [kw for kw in keywords_in_answer if kw.lower() not in combined_chunk_text]
    if ungrounded:
        return "UNGROUNDED_CLAIM"
    return "GROUNDED"


def select_representative_sample(questions, n, seed=42):
    """Stratified sample: spread roughly proportionally across every
    category, so a small sample is still a fair representative slice
    rather than biased toward whichever categories happen to be listed
    first. Every category gets at least 1 if n >= number of categories."""
    by_category = defaultdict(list)
    for q in questions:
        by_category[q["category"]].append(q)

    rng = random.Random(seed)
    for cat in by_category:
        rng.shuffle(by_category[cat])

    categories = list(by_category.keys())
    n = min(n, len(questions))

    sample = []
    cat_idx = 0
    pointers = {cat: 0 for cat in categories}
    max_iters = len(categories) * (max(len(v) for v in by_category.values()) + 1)
    iters = 0
    while len(sample) < n and iters < max_iters:
        cat = categories[cat_idx % len(categories)]
        if pointers[cat] < len(by_category[cat]):
            sample.append(by_category[cat][pointers[cat]])
            pointers[cat] += 1
        cat_idx += 1
        iters += 1

    return sample


def run_one(ask_fn, question_obj, model_key):
    """Run a single question against a single model and return a
    results row dict. Isolated from argparse/file-writing so it's easy
    to unit test with a mock ask_fn."""
    os.environ["LLM_CHOICE"] = model_key

    start = time.time()
    try:
        result = ask_fn(
            question_obj["question"],
            conversation_history=None,
            verbose=False,
            timeout=600,
            show_streaming=False,
        )
        elapsed = time.time() - start
        answer = result.get("answer", "")
        chunks = result.get("chunks", [])
    except Exception as e:
        elapsed = time.time() - start
        answer = f"ERROR: {e}"
        chunks = []

    confidence_label, confidence_pct = compute_confidence(chunks)
    top_sources = [c.get("title", "?") for c in chunks]
    expected_keywords = question_obj.get("expected_keywords", [])

    return {
        "id": question_obj["id"],
        "category": question_obj["category"],
        "question": question_obj["question"],
        "model": MODEL_LABELS.get(model_key, model_key),
        "answer": answer,
        "latency_seconds": round(elapsed, 2),
        "retrieval_success": grade_retrieval(question_obj.get("expected_source_file"), chunks),
        "top_sources": " | ".join(top_sources),
        "confidence_label": confidence_label,
        "confidence_pct": round(confidence_pct, 3),
        "keyword_match": grade_keywords(answer, expected_keywords, question_obj.get("match_type", "any")),
        "hallucination_flag": grade_hallucination(answer, chunks, expected_keywords),
        "expected_keywords": ", ".join(expected_keywords),
        "expected_source_file": question_obj.get("expected_source_file") or "",
        "notes": question_obj.get("notes", ""),
        "human_verified_correct": "",  # fill in manually
    }


def print_summary(rows):
    print(f"\n{'='*80}\nBENCHMARK SUMMARY\n{'='*80}")

    for model_label in sorted(set(r["model"] for r in rows)):
        model_rows = [r for r in rows if r["model"] == model_label]
        retrieval_gradable = [r for r in model_rows if r["retrieval_success"] != "N/A"]
        keyword_gradable = [r for r in model_rows if r["keyword_match"] != "N/A"]
        halluc_gradable = [r for r in model_rows if r["hallucination_flag"] != "N/A"]

        retrieval_rate = (sum(1 for r in retrieval_gradable if r["retrieval_success"] == "PASS")
                           / len(retrieval_gradable) if retrieval_gradable else 0)
        keyword_rate = (sum(1 for r in keyword_gradable if r["keyword_match"] == "PASS")
                         / len(keyword_gradable) if keyword_gradable else 0)
        halluc_count = sum(1 for r in halluc_gradable if r["hallucination_flag"] in ("NO_CONTEXT_CONFIDENT_ANSWER", "UNGROUNDED_CLAIM"))
        halluc_rate = halluc_count / len(halluc_gradable) if halluc_gradable else 0
        avg_latency = mean(r["latency_seconds"] for r in model_rows)
        avg_confidence = mean(r["confidence_pct"] for r in model_rows)

        print(f"\n{model_label} ({len(model_rows)} questions):")
        print(f"  Retrieval success:   {retrieval_rate:.1%}  ({sum(1 for r in retrieval_gradable if r['retrieval_success']=='PASS')}/{len(retrieval_gradable)} gradable)")
        print(f"  Keyword match:       {keyword_rate:.1%}  ({sum(1 for r in keyword_gradable if r['keyword_match']=='PASS')}/{len(keyword_gradable)} gradable) -- PROXY for correctness, verify manually")
        print(f"  Hallucination rate:  {halluc_rate:.1%}  ({halluc_count}/{len(halluc_gradable)} gradable) -- PROXY, see grade_hallucination() docstring")
        print(f"  Avg latency:         {avg_latency:.1f}s")
        print(f"  Avg confidence:      {avg_confidence:.1%}")

        print(f"\n  By category:")
        for cat in sorted(set(r["category"] for r in model_rows)):
            cat_rows = [r for r in model_rows if r["category"] == cat]
            cat_kw_gradable = [r for r in cat_rows if r["keyword_match"] != "N/A"]
            cat_kw_rate = (sum(1 for r in cat_kw_gradable if r["keyword_match"] == "PASS")
                           / len(cat_kw_gradable)) if cat_kw_gradable else None
            rate_str = f"keyword_match={cat_kw_rate:.0%}" if cat_kw_rate is not None else "(not keyword-gradable)"
            print(f"    {cat:15} n={len(cat_rows):3}  {rate_str}")

    print(f"\n{'='*80}")
    print(f"Full results appended to {RESULTS_PATH.absolute()}")
    print("Fill in 'human_verified_correct' after reviewing answers --")
    print("keyword_match and hallucination_flag are proxies, not final ground truth.")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["ollama", "groq", "both"], default="both")
    parser.add_argument("--groq-sample-size", type=int, default=12,
                         help="Representative sample size for Llama/groq (default 12). Ignored for ollama, which runs the full set by default.")
    parser.add_argument("--full-groq", action="store_true",
                         help="Run ALL questions against Llama too, instead of the stratified sample (uses much more Groq quota).")
    parser.add_argument("--limit", type=int, default=None,
                         help="Override: cap every model's question list to the first N (quick smoke test).")
    args = parser.parse_args()

    from rag_pipeline_dual import ask

    models_to_run = ["ollama", "groq"] if args.model == "both" else [args.model]

    print(f"Models: {[MODEL_LABELS[m] for m in models_to_run]}")

    is_new = not RESULTS_PATH.exists()
    csv_file = open(RESULTS_PATH, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_file, fieldnames=RESULTS_FIELDS)
    if is_new:
        writer.writeheader()
        csv_file.flush()

    rows = []
    try:
        for model_key in models_to_run:
            if model_key == "ollama":
                questions = BENCHMARK_QUESTIONS
            else:
                questions = BENCHMARK_QUESTIONS if args.full_groq else select_representative_sample(BENCHMARK_QUESTIONS, args.groq_sample_size)

            if args.limit:
                questions = questions[:args.limit]

            print(f"\n--- {MODEL_LABELS[model_key]}: {len(questions)} questions ---")
            for i, q in enumerate(questions, 1):
                print(f"[{i}/{len(questions)}] {model_key:8} {q['id']:8} {q['question'][:60]}")
                row = run_one(ask, q, model_key)
                rows.append(row)

                # Write immediately -- don't wait for the whole run to
                # finish, both so you can watch progress in the CSV
                # live, and so a crash/timeout partway through doesn't
                # lose everything completed so far.
                writer.writerow(row)
                csv_file.flush()

                # Terminal preview so you can see what's happening
                # without opening the CSV at all
                preview = (row["answer"] or "")[:150].replace("\n", " ")
                print(f"    -> [{row['retrieval_success']}/{row['keyword_match']}/{row['hallucination_flag']}] {row['latency_seconds']}s  {preview}...")
    finally:
        csv_file.close()

    print_summary(rows)


if __name__ == "__main__":
    main()