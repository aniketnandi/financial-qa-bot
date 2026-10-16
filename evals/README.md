# Evals for the Financial Document Q&A Bot

Two evals, both driven by the same golden set:

1. **Retrieval eval** (`retrieval_eval.py`): does FAISS retrieval surface the 10-K evidence needed to answer each question? Runs locally, **no Gemini calls**.
2. **Answer eval** (`eval_qa.py`): does each API endpoint (`/ask` single-shot RAG, `/ask_agent` tool-calling agent) return the correct answer?

## Golden set

  `golden_set.jsonl` holds 20 questions over Tesla's FY2023 10-K (`data/tsla-20231231-gen.pdf`). Expected answers and evidence strings were taken from the filing itself (Consolidated Statements of Operations, segment note, Human Capital section), not from the bot.

| Category | Count | What it tests |
|---|---|---|
| `lookup` | 8 | Pulling a single figure or fact (revenue, net income, R&D, headcount, segments) |
| `calculation` | 6 | Growth % and margin %: where the agent's calculator tools should beat plain RAG |
| `multi_hop` | 3 | Combining figures across years or the segment note |
| `unanswerable` | 3 | Declining questions the filing can't answer (live stock price, future revenue, another company) |

  Each answerable item also has an `evidence` list: the exact strings from the 10-K needed to answer it (e.g. `"96,773"`, 2023 revenue in millions).

## Run the retrieval eval

From the project root (where `faiss_index/` lives). No API key or server needed:

```bash
python evals/retrieval_eval.py --k 4 8 --diagnose
```

- `--k`: one or more top-k values to compare (the API uses k=4).
- `--diagnose`: for each miss, reports whether the evidence exists anywhere in the index and the rank of the best chunk containing it.
- Output: `evals/results_retrieval/summary.md` (use `--out` to write elsewhere).

## Run the answer eval

Start the API (`uvicorn main:app`), then from the project root in a second terminal:

```bash
python evals/eval_qa.py --endpoint rag=/ask --endpoint agent=/ask_agent --golden evals/golden_set.jsonl --out evals/results --retries 2 --resume
```

Useful flags:
- `--endpoint name=/path`: one per endpoint to compare.
- `--ids C01,C02`: run only specific questions.
- `--resume`: keep finished results in `--out` and rerun only missing or errored items.
- `--retries` / `--backoff`: retry transient `503 UNAVAILABLE` errors (daily-quota `429`s are not retried).
- `--sleep`: pause between requests.
- `--base-url` / `--api-key`: run against a deployment, such as the Azure Container App, instead of localhost. The key is sent as `X-API-Key`.
- `--rescore`: re-score the saved answers in `--out` with the current checks, without calling the API.

**Gemini free-tier note:** the free tier allows a small number of requests per model per day, and the agent makes several Gemini calls per question. Run endpoints separately (e.g. `--endpoint rag=/ask --out evals/results_rag`), and use `--resume` across days to fill in errored items.

## Scoring

- Numbers pass within ±1% (dollars, counts) or ±0.5 percentage points (percents).
- Keyword checks are case-insensitive.
- Unanswerable items pass only if the bot declines.
- Scores count only answered questions; `ERR` (quota or outage) is reported separately, not as a wrong answer.

Failures are reviewed by hand: a fail can be a scoring miss rather than a wrong answer.

## Results

### Retrieval (17 answerable questions)

| Chunking (size / overlap) | Recall @ k=4 | Recall @ k=8 |
|---|---|---|
| 1000 / 150 (original) | 11/17 (65%) | 12/17 (71%) |
| 2000 / 300 (current) | 16/17 (94%) | 17/17 (100%) |

Diagnosis of the original misses: every missing figure was in the index, but income-statement rows (operating income, operating expenses) landed in a chunk of bare table numbers that ranked 129th to 315th of 564 chunks, beyond any reasonable k. Larger chunks kept the table together.

### Retrieval: dense vs. BM25 vs. hybrid (2000 / 300 index)

| Retriever | Recall @ k=4 | Recall @ k=8 |
|---|---|---|
| dense (FAISS, used by the API) | 16/17 (94%) | 17/17 (100%) |
| bm25 | 9/17 (53%) | 11/17 (65%) |
| hybrid (RRF) | 13/17 (76%) | 16/17 (94%) |

BM25 underperforms because key figures such as `96,773` appear in 4 different chunks (MD&A, the income statement, segment notes), so keyword matching often ranks the wrong page first. Fusing it with dense retrieval brings that noise into the dense ranking.

### Answers: Gemini (`gemini-3.6-flash`, free tier, run locally)

| Endpoint | Overall | lookup | calculation | multi_hop | unanswerable |
|---|---|---|---|---|---|
| `rag` (`/ask`) | 16/20 (80%) | 7/8 | 4/6 | 2/3 | 3/3 |
| `agent` (`/ask_agent`), calc + multi-hop only | 6/6 answered (100%), 3 pending | | 5/5 | 1/1 | |

- `rag`: 3 of 4 failures were refusals ("I could not find this information") where retrieval *did* surface the evidence but the answer needed arithmetic (gross margin, net margin) or a segment table. These are the cases the agent's calculator tools target.
- `agent`: answered every scored calculation and multi-hop question correctly, including both margin questions that RAG refused. C04 was first scored as a fail: the answer was correct (15.47%) but formatted in LaTeX (`15.47\%`), which the number parser missed. The parser was fixed and the saved answers re-scored with `--rescore` (no API calls). 3 items are pending because of the free-tier quota.

### Answers: Azure OpenAI (`gpt-4.1-mini`, deployed on Azure Container Apps)

Run from Azure Cloud Shell against the live deployment, all 20 questions per endpoint. Azure has no daily quota, so nothing is pending. Same index, prompts, tools and scorer as the Gemini runs.

| Endpoint | Auto-scored | After manual review | lookup | calculation | multi_hop | unanswerable | p50 / p95 latency |
|---|---|---|---|---|---|---|---|
| `rag` (`/ask`) | 18/20 | **18/20 (90%)** | 7/8 | 6/6 | 2/3 | 3/3 | 1.86 s / 3.45 s |
| `agent` (`/ask_agent`) | 20/20 | **18/20 (90%)** | 8/8 | 5/6 | 2/3 | 3/3 | 2.48 s / 3.64 s |

Manual review of every scored answer:

- **Two scorer misses, now fixed.** Agent U02 and U03 were correct refusals ("I cannot provide…", "…cannot be found in the retrieved financial data") that the first scoring marked as fails, because those phrasings weren't in the refusal list. The phrases were added with a regression test and the saved answers re-scored. Gemini results were unchanged by this.
- **Two false passes, kept as failures above.** The scorer passes them, but they are wrong:
  - agent C06 answered 18.96%, the growth of *total* net income, instead of net income *attributable to common stockholders* (19.44%). The gap is within the ±0.5 pp tolerance.
  - agent M03 has the right figures (25.60% → 18.25%) and concludes the margin decreased, but its first sentence says "improved".

  Tightening the tolerance or adding a contradiction check would catch these, but it would also risk rejecting correct answers. They're documented here instead.
- **Genuine RAG failures.** L06 refused although the segment note was retrieved. M01 named "Automotive sales $78,509M" (a revenue line) instead of the Automotive segment's $90,738M. The agent got both right.

**Gemini vs Azure OpenAI.** With `gpt-4.1-mini`, single-shot RAG answers the margin questions it previously refused (calculation 6/6 vs 4/6), so the agent's advantage narrows to the segment questions. Latency is also much lower (p50 under 2.5 s vs 7.9 s), but that compares different models and service tiers (paid Azure deployment vs Gemini free tier), not just providers.

Raw outputs: `results_retrieval/` (dense, 2000/300), `results_retrieval_hybrid/` (retriever comparison), `results_rag/`, `results_agent/` (Gemini), `results_azure_rag/`, `results_azure_agent/` (Azure OpenAI). The 1000/150 baseline can be reproduced with `python ingest.py --chunk-size 1000 --chunk-overlap 150 --index-dir faiss_index_1000`, then `python evals/retrieval_eval.py --index faiss_index_1000 --k 4 8`.
