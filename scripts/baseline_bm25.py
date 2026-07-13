#!/usr/bin/env python3
"""Reference BM25 baseline for KorMapleQA — a runnable sanity check.

Pure-Python BM25 over the note bodies with a Hangul character-bigram fallback
(Korean is agglutinative; whitespace tokenisation alone under-recalls). No
third-party dependencies. This is NOT a strong system; it exists so you can
(a) verify the corpus + evaluator work end to end, and (b) have a floor to
beat. Real hybrid systems score far higher on the paraphrase/typo/2-hop axes.

    python scripts/baseline_bm25.py            # unpacks corpus if needed, scores
"""
from __future__ import annotations

import math
import re
import unicodedata
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from evaluate import evaluate, load_questions  # noqa: E402

CORPUS = HERE / "data" / "corpus"
_HANGUL_RUN = re.compile(r"[가-힣]+")
_WORD = re.compile(r"[a-z0-9]+|[가-힣]+")


def ensure_corpus() -> Path:
    if not CORPUS.exists():
        tar = HERE / "data" / "corpus.tar.gz"
        print(f"unpacking {tar.name} -> {CORPUS} ...")
        CORPUS.mkdir(parents=True)
        subprocess.run(["tar", "xzf", str(tar), "-C", str(CORPUS)], check=True)
    return CORPUS


def tokenize(text: str) -> list[str]:
    text = text.lower()
    toks: list[str] = []
    for w in _WORD.findall(text):
        toks.append(w)
    # Hangul bigrams: '윤하준가' never matches '윤하준' under plain tokenisation
    for run in _HANGUL_RUN.findall(text):
        toks.extend(run[i:i + 2] for i in range(len(run) - 1))
    return toks


class BM25:
    def __init__(self, docs: dict[str, str], k1=1.5, b=0.75):
        self.titles = list(docs)
        self.tf = []
        self.len = []
        df: Counter = Counter()
        for t in self.titles:
            toks = tokenize(docs[t])
            c = Counter(toks)
            self.tf.append(c)
            self.len.append(sum(c.values()))
            df.update(c.keys())
        self.N = len(self.titles)
        self.avg = (sum(self.len) / self.N) if self.N else 0.0
        self.idf = {term: math.log(1 + (self.N - n + 0.5) / (n + 0.5))
                    for term, n in df.items()}
        self.k1, self.b = k1, b
        self.postings = defaultdict(list)
        for i, c in enumerate(self.tf):
            for term in c:
                self.postings[term].append(i)

    def search(self, query: str, k=8) -> list[str]:
        q = set(tokenize(query))
        scores: dict[int, float] = defaultdict(float)
        for term in q:
            idf = self.idf.get(term)
            if idf is None:
                continue
            for i in self.postings[term]:
                f = self.tf[i][term]
                denom = f + self.k1 * (1 - self.b + self.b * self.len[i] / (self.avg or 1))
                scores[i] += idf * f * (self.k1 + 1) / denom
        top = sorted(scores, key=lambda i: -scores[i])[:k]
        return [self.titles[i] for i in top]


def main():
    corpus = ensure_corpus()
    docs = {unicodedata.normalize("NFC", p.stem): p.read_text(encoding="utf-8", errors="replace")
            for p in corpus.glob("*.md")}
    print(f"corpus: {len(docs)} notes")
    bm = BM25(docs)
    read_note = lambda t: docs.get(t, "")
    evaluate(bm.search, k=8, read_note=read_note, questions=load_questions())


if __name__ == "__main__":
    main()
