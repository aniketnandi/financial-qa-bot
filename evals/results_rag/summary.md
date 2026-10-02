# Q&A Bot Eval Summary

Golden set: 20 questions (0 skipped as unfilled)

| Endpoint | Overall | calculation | lookup | multi_hop | unanswerable | p50 latency | p95 latency |
|---|---|---|---|---|---|---|---|
| rag | 1/20 (5%) | 0/6 (0%) | 1/8 (12%) | 0/3 (0%) | 0/3 (0%) | 15.89s | 15.89s |

## Failures

- **[rag] L02** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What was Tesla's net income in 2023?
  - Answer: ''
- **[rag] L03** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): How much did Tesla spend on research and development in 2023?
  - Answer: ''
- **[rag] L04** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What was Tesla's gross profit in 2023?
  - Answer: ''
- **[rag] L05** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What was Tesla's worldwide employee headcount as of December 31, 2023?
  - Answer: ''
- **[rag] L06** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What reportable segments does Tesla disclose in its 2023 10-K?
  - Answer: ''
- **[rag] L07** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): How does Tesla describe the competitive landscape of the automotive market in its 2023 10-K?
  - Answer: ''
- **[rag] L08** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What was Tesla's income from operations in 2023?
  - Answer: ''
- **[rag] C01** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What was Tesla's year-over-year total revenue growth from 2022 to 2023?
  - Answer: ''
- **[rag] C02** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What was Tesla's gross margin in 2023?
  - Answer: ''
- **[rag] C03** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What was Tesla's operating margin in 2023?
  - Answer: ''
- **[rag] C04** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What was Tesla's net profit margin in 2023?
  - Answer: ''
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
- **[rag] U01** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What is Tesla's stock price today?
  - Answer: ''
- **[rag] U02** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What total revenue will Tesla report for 2025?
  - Answer: ''
- **[rag] U03** (HTTP 500: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ): What was Ford Motor Company's total revenue in 2023?
  - Answer: ''
