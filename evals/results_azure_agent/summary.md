# Q&A Bot Eval Summary

Golden set: 20 questions (0 skipped as unfilled)
Scores count only answered questions; ERR = API error (quota/outage), not a wrong answer. Rerun with --resume to fill them in.

| Endpoint | Overall | calculation | lookup | multi_hop | unanswerable | p50 latency | p95 latency |
|---|---|---|---|---|---|---|---|
| agent | 18/20 (90%) | 6/6 (100%) | 8/8 (100%) | 3/3 (100%) | 1/3 (33%) | 2.48s | 3.64s |

## Failures

- **[agent] U02** (refusal): What total revenue will Tesla report for 2025?
  - Answer: 'The financial filings provide total revenues for Tesla for the years 2021 through 2023, but there is no specific forecast or projected total revenue for Tesla in 2025 included in the provided documents. Therefore, I cannot provide the total revenue Tesla will report for 2025 based on these filings.'
- **[agent] U03** (refusal): What was Ford Motor Company's total revenue in 2023?
  - Answer: 'The total revenue for Ford Motor Company in 2023 cannot be found in the retrieved financial data. The data retrieved contains revenue figures for Tesla, Inc. for the year 2023. Would you like me to try to find the Ford Motor Company revenue from another source?'
