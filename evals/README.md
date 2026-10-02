# Eval harness for the Financial Document Q&A Bot

Scores the bot against a golden set of questions with known answers, so you can report accuracy (and compare the single-shot RAG endpoint against the tool-calling agent) instead of eyeballing outputs.

## 1. Golden set

`golden_set.jsonl` holds 20 questions over Tesla's FY2023 10-K (`data/tsla-20231231-gen.pdf`), with expected answers taken from the filing itself (Consolidated Statements of Operations, segment note, and Human Capital section):

| Category | Count | What it tests |
|---|---|---|
| `lookup` | 8 | Pulling a single figure or fact (revenue, net income, R&D, headcount, segments) |
| `calculation` | 6 | Growth % and margin %: where the agent's calculator tools should beat plain RAG |
| `multi_hop` | 3 | Combining figures across years or the segment note |
| `unanswerable` | 3 | Declining questions the filing can't answer (live stock price, future revenue, another company) |

To add questions, copy a line and change it. Dollar values are full dollars (10-K tables are "in millions"), percentages are in points.

## 2. Run it

Start the FastAPI app, then:

```bash
pip install requests
python eval_qa.py --base-url http://localhost:8000 \
    --endpoint rag=/ask --endpoint agent=/ask_agent \
    --golden golden_set.jsonl --out results --sleep 4
```

Adjust to match your API:
- `--endpoint name=/path`: one per endpoint you want to compare (use your real routes).
- `--question-field`: request JSON key (default `question`).
- `--answer-field` / `--sources-field`: response keys; dot paths work, e.g. `data.answer`.

## 3. Read the results

- `results/summary.md`: pass rate per endpoint and category, p50/p95 latency, and every failure with the bot's answer.
- `results/results.jsonl`: per-question detail.

Scoring rules: numbers pass within ±1% (dollars/counts) or ±0.5 percentage points (percents); keyword checks are case-insensitive; unanswerable items pass only if the bot declines.

**Check the failures by hand before you trust the number.** A "fail" can be a scoring miss (e.g. the bot said "$394 billion" when you set a tight tolerance) rather than a wrong answer. Fix the golden item or tolerance if so, then rerun.

## 4. Use it

Once you have real numbers, a resume bullet can look like:

> Built an eval harness with a 20-question golden set (lookups, margin/growth calculations, unanswerable prompts); the tool-calling agent scored X% vs. Y% for single-shot RAG on calculation questions

Only use the numbers your run actually produced.
