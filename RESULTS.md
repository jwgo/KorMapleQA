# KorMapleQA results

Systems run so far. **doc@8** = a gold note in the top 8 (document-level, the
fairest cross-system number). Everything here is reproducible from this repo
or from the linked harness; add your own row with a PR.

> **Question set v2 (2026-07).** The questions were re-phrased to remove a
> monotony artifact: 72% used to end in the identical `~은 무엇인가?`. They now
> vary the interrogative by answer type (뭐야 / 뭐지 / 뭔가 / 무엇이지 / 몇이야 /
> 얼마인가 / 누구야 / 언제였지 / 알려줘 …), and typos land on the entity rather
> than the question word. **Every system below was re-measured on v2.** The
> phrasing change moved each system by less than ±2.5 doc@8 points versus v1,
> so the ranking and the story are unchanged. The one exception is the Gemini
> row (see its note).

Two things make a fair comparison hard, so they are labeled explicitly:
**question set** (the full 2,067 answerable questions vs a smaller sample or
subcorpus) and **setup** (local embedder / API embedder / an "as-shipped"
tool / a *class reproduction* using a tool's default model in a shared
runtime). Read the labels before ranking.

## Full corpus, full question set (2,067 answerable, 1,469-note corpus)

| system | doc@1 | doc@8 | latency (p50) | setup |
|---|---|---|---|---|
| hybrid (semantic + Korean BM25 + link graph), API embeddings | 0.664 | **0.906** | ~13 ms | Gemini `gemini-embedding-001`, **v1 phrasing*** |
| hybrid, local embedder (Harrier-0.6B Q8) | 0.612 | 0.853 | ~102 ms | Ollama, Microsoft Harrier (Qwen3-based multilingual), zero keys |
| hybrid, local embedder (MiniLM-384d) | 0.536 | 0.788 | ~18 ms | fastembed, zero keys, no daemon |
| **BM25** (`scripts/baseline_bm25.py`) | 0.374 | 0.741 | ~1 ms | pure Python, Hangul bigrams, in this repo |
| Smart-Connections *class* | 0.072 | 0.204 | ~15 ms | its default `bge-micro-v2`, cosine only, shared runtime |
| Omnisearch (Obsidian) | 0.111 | 0.148 | ~1 ms | real MiniSearch + its exact config, headless |
| dense vector only | 0.046 | 0.135 | ~1 ms | MiniLM-384d cosine, no lexical/graph |
| qmd `search` (BM25) | 0.054 | 0.091 | ~90 ms | tobi/qmd, AND semantics |
| MemPalace 3.5 | 0.016 | 0.031 | ~760 ms | `sqlite_exact` + bundled embeddinggemma |

\* The Gemini row is the only one still on v1 phrasing: refreshing it needs live
Gemini query embeddings and this project's API credits are depleted, so it could
not be re-run on v2. Every other system moved by <2.5 doc@8 points from v1→v2
(BM25 +2.0, hybrid-local +2.5, the rest within ±1.5), so read 0.906 as v1-exact
and v2-representative to about ±2 points, not as a refreshed v2 measurement.

Reading it: lexical-only tools (Omnisearch, qmd-search) return almost nothing
on natural-language and typo'd Korean questions; a small English-leaning dense
embedder (Smart-Connections class, MemPalace) collapses on Korean; the strong
rows are hybrids that combine a Korean-aware lexical leg with semantics and
the wikilink graph. The vector leg matters: the same hybrid goes 0.788
(fastembed MiniLM, instant, no daemon) to 0.853 (Harrier-0.6B via Ollama) to
0.906 (Gemini API) as the embedder gets stronger. Even the strong hybrids top
out around **0.18 on 2-hop
full-support** (both gold notes retrieved): the answer note is reachable only
through a link and carries little signal of its own. That axis is the open
challenge.

## Sampled / subcorpus (different protocol, do not compare across tables)

LLM-pipeline systems are billed or slow per query, so they were run on a
stratified sample or a smaller labeled subcorpus. These rows are on the **v1**
question phrasing (they predate v2 and were not re-run); numbers are only
comparable to the *matched* baseline shown beside them.

| system | doc@8 | n | note |
|---|---|---|---|
| qmd `query` (full local-LLM pipeline) | 0.769 | 329 | 59.5 s/query; matched hybrid on the same 329: 0.775 @ ~20 ms |
| qmd `vsearch` (local embedder) | 0.657 | 280 | 4.2 s/query |
| mem0 (Gemini backend) | 0.619 | 310 | 400-note subcorpus, 60 min LLM ingest; matched hybrid same subcorpus: 0.926 |

**cognee / supermemory / LightRAG / OpenKB / openwiki**: not yet run to
completion, their per-note LLM ingest needs an API budget (a LightRAG run
here stopped at 362/400 notes when a free key's credits ran out). A row will
be added when someone completes one; PRs welcome.

## Method notes

- **doc-level, title-matched.** A prediction is the ranked list of note
  titles; `evaluate.py` NFC-normalizes both sides.
- **Full support (2-hop):** both gold notes in the top 8. Reported inside the
  per-type breakdown from `evaluate.py`, not in the summary above.
- **Class reproductions** (Smart-Connections) run the tool's *default model*
  in this repo's fastembed runtime rather than the packaged plugin, so
  chunking is controlled; this favors the tool if anything.
- **Latency** is local retrieval compute; the query-embedding round-trip is
  excluded for every embedding-based system (identical across them).

## Submit a result

Run `evaluate.py` against your system (see the README), then open a PR adding
a row with: doc@1, doc@8, question set (full / sample n=…), and a one-line
setup description. Please link a reproducible harness or command.
