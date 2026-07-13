#!/usr/bin/env python3
"""KorMapleQA evaluator - plug in any retrieval system, get the scorecard.

Self-contained: standard library only, no ML dependencies. You provide a
`retrieve(query) -> list[str]` that returns note titles (or paths) in ranked
order for a query; this computes the metrics. Or score a predictions file.

Usage
-----
1. As a library (recommended):

    from evaluate import evaluate
    def retrieve(query):
        # ...your RAG returns the top note TITLES, best first...
        return ["윌(메이플스토리)-보스 몬스터", ...]
    evaluate(retrieve, k=8)

2. From a predictions file (JSONL: {"id": "kmq-0001", "titles": [...]} per line):

    python evaluate.py --predictions preds.jsonl

Notes are matched by TITLE (the .md filename without extension). Gold titles
in questions.jsonl use the same convention. Answer-in-context needs the note
TEXT, so pass a `read_note(title) -> str` to score answer-level metrics too.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
QUESTIONS = HERE / "data" / "questions.jsonl"


def load_questions(path: Path = QUESTIONS) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _norm(s: str) -> str:
    return re.sub(r"[^\w가-힣]+", "", s.lower())


def _nfc(s: str) -> str:
    # macOS extracts Hangul filenames as NFD; questions.jsonl is NFC. Normalise
    # both sides so title matching is byte-exact regardless of the filesystem.
    return unicodedata.normalize("NFC", s)


def score(questions, predictions, k=8, read_note=None) -> dict:
    """predictions: {question_id: [ranked note titles]}. read_note optional,
    for answer-in-context metrics. Returns per-type and overall metrics."""
    per = defaultdict(lambda: {"doc1": 0, "doc8": 0, "fs": 0, "ans8": 0, "n": 0})
    abst = {"n": 0, "correct_empty": 0}
    for q in questions:
        titles = [_nfc(t) for t in list(predictions.get(q["id"], []))[:k]]
        tt = set(titles)
        if not q.get("answerable", True):
            abst["n"] += 1
            # a retrieval system "abstains" by returning nothing relevant;
            # we only score retrieval here (e2e abstention is a generator test)
            continue
        gold = [_nfc(g) for g in q["gold_notes"]]
        st = per[q["type"]]
        st["n"] += 1
        st["doc1"] += bool(titles and titles[0] in gold)
        st["doc8"] += any(t in gold for t in titles)
        st["fs"] += all(g in tt for g in gold)
        if read_note is not None and q.get("answers"):
            ans = _norm(q["answers"][0])
            hit = any(g in tt and ans in _norm(read_note(g) or "") for g in gold)
            st["ans8"] += bool(hit)

    out = {}
    tot = {"doc1": 0, "doc8": 0, "fs": 0, "ans8": 0, "n": 0}
    for t, st in sorted(per.items()):
        for key in tot:
            tot[key] += st[key]
        out[t] = {m: round(st[m] / st["n"], 4) if m != "n" else st["n"]
                  for m in ("doc1", "doc8", "fs", "ans8", "n")}
    out["all"] = {m: round(tot[m] / tot["n"], 4) if m != "n" else tot["n"]
                  for m in ("doc1", "doc8", "fs", "ans8", "n")}
    out["abstention"] = abst
    return out


def evaluate(retrieve, k=8, read_note=None, questions=None) -> dict:
    """Convenience wrapper: call `retrieve(query)` for every question."""
    questions = questions or load_questions()
    preds = {}
    for i, q in enumerate(questions):
        preds[q["id"]] = retrieve(q["q"])
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(questions)} queried", flush=True)
    result = score(questions, preds, k=k, read_note=read_note)
    _print(result)
    return result


def _print(result: dict) -> None:
    print("\nKorMapleQA scorecard (doc@1 / doc@8 / full-support / n)")
    print("-" * 56)
    order = ["all", "single", "masked", "twohop", "temporal", "kw", "casual", "typo"]
    for t in order:
        if t not in result:
            continue
        r = result[t]
        print(f"  {t:9s}  doc1={r['doc1']:.3f}  doc8={r['doc8']:.3f}  "
              f"fs={r['fs']:.3f}  n={r['n']}")
    a = result["abstention"]
    print(f"  abstention questions: {a['n']} (score in an e2e/generation test)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions", required=True,
                    help="JSONL, one {'id','titles':[...]} per question")
    ap.add_argument("-k", type=int, default=8)
    args = ap.parse_args()
    preds = {}
    for line in Path(args.predictions).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            preds[r["id"]] = r.get("titles", r.get("gold_notes", []))
    result = score(load_questions(), preds, k=args.k)
    _print(result)


if __name__ == "__main__":
    main()
