# Q&A Bot Eval Summary

Golden set: 20 questions (0 skipped as unfilled)
Scores count only answered questions; ERR = API error (quota/outage), not a wrong answer. Rerun with --resume to fill them in.

| Endpoint | Overall | calculation | lookup | multi_hop | unanswerable | p50 latency | p95 latency |
|---|---|---|---|---|---|---|---|
| rag | 10/12 (83%) +8 ERR | 2/3 (67%) +3 ERR | 7/8 (88%) | - (3 ERR) | 1/1 (100%) +2 ERR | 10.56s | 47.70s |

## Failures

- **[rag] L06** (keywords): What reportable segments does Tesla disclose in its 2023 10-K?
  - Answer: 'I could not find this information in the provided documents.'
- **[rag] C02** (HTTP 500: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}): What was Tesla's gross margin in 2023?
  - Answer: ''
- **[rag] C04** (numeric): What was Tesla's net profit margin in 2023?
  - Answer: 'I could not find this information in the provided documents.'
- **[rag] C05** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What percentage of total revenue did Tesla spend on research and development in 2023?
  - Answer: ''
- **[rag] C06** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): By what percentage did Tesla's net income attributable to common stockholders change from 2022 to 2023?
  - Answer: ''
- **[rag] M01** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): Which of Tesla's reportable segments had the highest revenue in 2023, and how much was it?
  - Answer: ''
- **[rag] M02** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): Did Tesla's total operating expenses grow faster or slower than its total revenue from 2022 to 2023?
  - Answer: ''
- **[rag] M03** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): Compare Tesla's gross margin in 2022 and 2023. Did it improve?
  - Answer: ''
- **[rag] U02** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What total revenue will Tesla report for 2025?
  - Answer: ''
- **[rag] U03** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What was Ford Motor Company's total revenue in 2023?
  - Answer: ''
