# Q&A Bot Eval Summary

Golden set: 20 questions (0 skipped as unfilled)
Scores count only answered questions; ERR = API error (quota/outage), not a wrong answer. Rerun with --resume to fill them in.

| Endpoint | Overall | calculation | lookup | multi_hop | unanswerable | p50 latency | p95 latency |
|---|---|---|---|---|---|---|---|
| rag | 18/20 (90%) | 6/6 (100%) | 7/8 (88%) | 2/3 (67%) | 3/3 (100%) | 1.86s | 3.45s |

## Failures

- **[rag] L06** (keywords): What reportable segments does Tesla disclose in its 2023 10-K?
  - Answer: 'I could not find this information in the provided documents.'
- **[rag] M01** (numeric): Which of Tesla's reportable segments had the highest revenue in 2023, and how much was it?
  - Answer: 'The reportable segment of Tesla with the highest revenue in 2023 was Automotive sales, with revenue of $78,509 million.'
