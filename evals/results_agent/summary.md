# Q&A Bot Eval Summary

Golden set: 9 questions (0 skipped as unfilled)
Scores count only answered questions; ERR = API error (quota/outage), not a wrong answer. Rerun with --resume to fill them in.

| Endpoint | Overall | calculation | multi_hop | p50 latency | p95 latency |
|---|---|---|---|---|---|
| agent | 5/6 (83%) +3 ERR | 4/5 (80%) +1 ERR | 1/1 (100%) +2 ERR | 9.27s | 16.06s |

## Failures

- **[agent] C04** (numeric): What was Tesla's net profit margin in 2023?
  - Answer: "According to Tesla's Consolidated Statements of Operations in its 2023 Form 10-K, the financial results for the year ended December 31, 2023 were:\n\n* **Total Revenues:** $96,773 million\n* **Net Income:** $14,974 million\n* **Net Income Attributable to Common Stockholders:** $14,997 million\n\n### Net P"
- **[agent] C06** (HTTP 429: Model provider rate limit or quota exceeded. Try again later.): By what percentage did Tesla's net income attributable to common stockholders change from 2022 to 2023?
  - Answer: ''
- **[agent] M01** (HTTP 429: Model provider rate limit or quota exceeded. Try again later.): Which of Tesla's reportable segments had the highest revenue in 2023, and how much was it?
  - Answer: ''
- **[agent] M03** (HTTP 429: Model provider rate limit or quota exceeded. Try again later.): Compare Tesla's gross margin in 2022 and 2023. Did it improve?
  - Answer: ''
