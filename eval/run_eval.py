"""Measure retrieval quality and dump answers for manual review.

Retrieval hit-rate is the headline number: did the expected chapter appear in
the top-k results? Out-of-scope questions pass when nothing is retrieved.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from rag.chain import answer_question
from rag.config import get_settings
from rag.retriever import retrieve

QUESTIONS_PATH = Path(__file__).parent / "questions.yaml"


def evaluate(with_answers: bool = False) -> dict:
    questions = yaml.safe_load(QUESTIONS_PATH.read_text(encoding="utf-8"))
    settings = get_settings()

    rows = []
    hits = 0

    for item in questions:
        question = item["question"]
        expected = item["expected_chapter"]
        chunks = retrieve(question)
        retrieved_chapters = [c.chapter_num for c in chunks]

        if expected is None:
            hit = len(chunks) == 0
        else:
            hit = expected in retrieved_chapters
        hits += int(hit)

        row = {
            "question": question,
            "expected_chapter": expected,
            "retrieved_chapters": retrieved_chapters,
            "top_score": round(chunks[0].score, 3) if chunks else None,
            "hit": hit,
        }

        if with_answers:
            result = answer_question(question)
            row["answer"] = result.answer
            row["citations"] = [c.label for c in result.citations]

        rows.append(row)

    return {
        "provider": settings.provider,
        "model": settings.model,
        "top_k": settings.top_k,
        "threshold": settings.score_threshold,
        "total": len(rows),
        "hits": hits,
        "hit_rate": round(hits / len(rows), 3) if rows else 0.0,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality.")
    parser.add_argument(
        "--with-answers",
        action="store_true",
        help="Also generate answers (costs API calls).",
    )
    parser.add_argument("--json", type=Path, help="Write full results to a JSON file.")
    args = parser.parse_args()

    results = evaluate(with_answers=args.with_answers)

    print(f"provider : {results['provider']} ({results['model']})")
    print(f"top_k    : {results['top_k']}, threshold: {results['threshold']}")
    print(f"hit rate : {results['hits']}/{results['total']} = {results['hit_rate']:.1%}\n")

    for row in results["rows"]:
        mark = "PASS" if row["hit"] else "FAIL"
        print(f"[{mark}] {row['question']}")
        print(f"        expected ch {row['expected_chapter']}, got {row['retrieved_chapters']}")
        if "answer" in row:
            print(f"        {row['answer'][:160]}")

    if args.json:
        args.json.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
