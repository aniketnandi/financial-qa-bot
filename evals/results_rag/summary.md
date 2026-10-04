# Q&A Bot Eval Summary

Golden set: 20 questions (0 skipped as unfilled)
Scores count only answered questions; ERR = API error (quota/outage), not a wrong answer. Rerun with --resume to fill them in.

| Endpoint | Overall | calculation | lookup | multi_hop | unanswerable | p50 latency | p95 latency |
|---|---|---|---|---|---|---|---|
| rag | 15/19 (79%) +1 ERR | 4/6 (67%) | 7/8 (88%) | 2/3 (67%) | 2/2 (100%) +1 ERR | 7.23s | 47.70s |

## Failures

- **[rag] L06** (keywords): What reportable segments does Tesla disclose in its 2023 10-K?
  - Answer: 'I could not find this information in the provided documents.'
- **[rag] C02** (numeric): What was Tesla's gross margin in 2023?
  - Answer: "I could not find this information in the provided documents. \n\n*(Note: The provided Consolidated Statements of Operations includes Tesla's **Total revenues** of $96,773 million and **Gross profit** of $17,660 million for 2023, but it does not explicitly state a gross margin percentage.)*"
- **[rag] C04** (numeric): What was Tesla's net profit margin in 2023?
  - Answer: 'I could not find this information in the provided documents.'
- **[rag] M01** (numeric): Which of Tesla's reportable segments had the highest revenue in 2023, and how much was it?
  - Answer: 'Based on the provided Consolidated Statements of Operations, the **Total automotive revenues** segment had the highest revenue in 2023, totaling **$82,419 million** (with **Automotive sales** specifically generating $78,509 million). \n\nFor comparison, the other revenue categories in 2023 were:\n* **S'
- **[rag] U03** (HTTP 429: Model provider rate limit or quota exceeded. Try again later.): What was Ford Motor Company's total revenue in 2023?
  - Answer: ''
