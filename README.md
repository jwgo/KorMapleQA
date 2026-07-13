# KorMapleQA

**A hard, verifiable Korean RAG / retrieval benchmark over a real namuwiki
domain.** 2,075 questions over 1,469 real MapleStory wiki documents
(33k+ chunks), 100% code-generated and machine-verified, reproducible with
zero API keys. Plug in your retrieval or RAG system and get a scorecard.

Most Korean retrieval benchmarks (KorQuAD and friends) ask questions written
*while looking at the passage*, so vocabulary overlap is total and plain BM25
is hard to beat. KorMapleQA is built the other way: it tests how people
actually ask: paraphrases, terse keywords, 반말/slang, typos, entity-masked
references, and two-hop questions that reach the answer only through a
wikilink. It also includes verified-absent questions to test abstention.

## What's here

```
data/questions.jsonl     2,075 questions (see schema below)
data/corpus.tar.gz       1,469 markdown notes (14 MB; the searchable corpus)
evaluate.py              self-contained scorer, plug in your retrieve()
scripts/baseline_bm25.py runnable pure-Python BM25 reference (no deps)
scripts/generate.py      the deterministic generator (how the QA was made)
```

## Question types (2,075)

| type | n | what it tests |
|---|---|---|
| `single` | 981 | an infobox / bullet fact ("윌의 테마곡은 무엇인가?") |
| `masked` | 215 | the entity referenced by a unique property, not its name (defeats title matching) ("테마곡이 'Diffraction'인 보스의 제한 시간은?") |
| `twohop` | 128 | A's infobox links to B; the answer is a fact in B and is **verified absent from A** (no shortcut) |
| `temporal` | 83 | release / debut dates |
| `kw` | 220 | terse keyword form of a `single` question |
| `casual` | 220 | 반말 + game slang form ("스우 브금 뭐야?") |
| `typo` | 220 | seeded syllable-transposition typos |
| `abstention` | 8 | content added after the 2021-03 dump: the corpus genuinely lacks the answer |

Every answerable question satisfies machine-checked invariants: the answer
appears in the gold note(s), a masked question's identifier is unique across
the whole corpus, and a 2-hop answer is provably absent from the bridge note.
See `scripts/generate.py`.

## Quickstart

```bash
# 1. unpack the corpus
mkdir -p data/corpus && tar xzf data/corpus.tar.gz -C data/corpus

# 2. run the reference BM25 baseline (pure Python, no dependencies)
python scripts/baseline_bm25.py
```

### Score your own system

```python
from evaluate import evaluate

def retrieve(query: str) -> list[str]:
    # return your top note TITLES (the .md filename without extension),
    # best first. Titles are matched NFC-normalized, so macOS NFD is fine.
    return my_rag.search(query, k=8)

# optional: pass read_note(title)->str to also score answer-in-context
evaluate(retrieve, k=8)
```

or score a predictions file (`{"id": "kmq-0001", "titles": [...]}` per line):

```bash
python evaluate.py --predictions my_preds.jsonl
```

## Metrics

- **doc@1 / doc@8**, a gold note is at rank 1 / in the top 8. Document-level, so it compares fairly against systems that only rank documents.
- **full-support**, for 2-hop, both gold notes are retrieved (the
  precondition for actually answering).
- **answer-in-context@8**, a retrieved gold chunk actually contains the
  answer string (needs `read_note`).
- **abstention**, the 8 unanswerable questions are a generation/e2e test
  (does your system say "I don't know" rather than hallucinate?), reported
  separately.

## Reference scores

A fuller cross-system comparison (BM25, dense-only, hybrids, qmd, MemPalace,
Smart-Connections-class, mem0) with methodology and how-to-submit is in
[RESULTS.md](RESULTS.md). Quick version (doc@8, full 2,067 answerable):

| system | doc@8 | notes |
|---|---|---|
| BM25 (this repo's `baseline_bm25.py`) | 0.741 | pure-Python floor, Hangul bigrams |
| dense vector only (MiniLM-384d) | 0.135 | Korean is hard for a small English-leaning embedder |
| a strong hybrid (semantic + Korean BM25 + link graph), local MiniLM | 0.79 | zero keys, no daemon, instant |
| the same hybrid, local Harrier-0.6B (Q8, Ollama) | 0.85 | zero keys, stronger multilingual embedder |
| the same hybrid with Gemini embeddings | 0.91 | API |

2-hop full-support is ~0.14–0.19 for everything measured, including
LLM-pipeline systems: the answer note carries almost no signal of its own
and is reachable only via the link. That axis is an open challenge; beating
it is the point of publishing this.

## Reproduce the corpus and questions

The corpus is derived from the public **namuwiki 2021-03-01 dump**
(archive.org/details/namuwikidumps): every document categorized under
메이플스토리 (867k docs scanned → 1,469 kept). `data/corpus.tar.gz` is that
build, shipped for convenience. To rebuild from scratch or regenerate the
questions, see `scripts/generate.py` (deterministic, seed-fixed, no LLM, no
API key).

## License

- **Code** (evaluate.py, scripts/): MIT.
- **Corpus and questions**: the underlying text is from namuwiki under
  **CC BY-NC-SA 2.0 KR**. Questions are code-generated from that text and are
  redistributed under the same license. Non-commercial research use; keep the
  attribution. Game names are trademarks of their owners.

If you use KorMapleQA, a link back is appreciated. Issues and additional
system results (open a PR adding a row to the reference table) are welcome.
