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

### Answers (in progress, current index)

- `rag` (`/ask`): 10/12 answered questions correct so far, 8 pending (API quota). Both failures were refusals ("I could not find this information") on questions where retrieval *did* surface the evidence: net profit margin (needs a calculation) and reportable segments.
- `agent` (`/ask_agent`): pending.

Raw outputs: `results_retrieval/`, `results_retrieval_2000/`, `results_rag/`.