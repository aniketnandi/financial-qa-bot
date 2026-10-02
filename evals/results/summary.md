# Q&A Bot Eval Summary

Golden set: 20 questions (0 skipped as unfilled)

| Endpoint | Overall | calculation | lookup | multi_hop | unanswerable | p50 latency | p95 latency |
|---|---|---|---|---|---|---|---|
| rag | 2/20 (10%) | 1/6 (17%) | 0/8 (0%) | 0/3 (0%) | 1/3 (33%) | 3.94s | 10.55s |
| agent | 0/20 (0%) | 0/6 (0%) | 0/8 (0%) | 0/3 (0%) | 0/3 (0%) | 0.00s | 0.00s |

## Failures

- **[rag] L01** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What was Tesla's total revenue in 2023?
  - Answer: ''
- **[rag] L02** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What was Tesla's net income in 2023?
  - Answer: ''
- **[rag] L03** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): How much did Tesla spend on research and development in 2023?
  - Answer: ''
- **[rag] L04** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What was Tesla's gross profit in 2023?
  - Answer: ''
- **[rag] L05** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What was Tesla's worldwide employee headcount as of December 31, 2023?
  - Answer: ''
- **[rag] L06** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What reportable segments does Tesla disclose in its 2023 10-K?
  - Answer: ''
- **[rag] L07** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): How does Tesla describe the competitive landscape of the automotive market in its 2023 10-K?
  - Answer: ''
- **[rag] L08** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What was Tesla's income from operations in 2023?
  - Answer: ''
- **[rag] C01** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What was Tesla's year-over-year total revenue growth from 2022 to 2023?
  - Answer: ''
- **[rag] C02** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What was Tesla's gross margin in 2023?
  - Answer: ''
- **[rag] C03** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What was Tesla's operating margin in 2023?
  - Answer: ''
- **[rag] C04** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What was Tesla's net profit margin in 2023?
  - Answer: ''
- **[rag] C06** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): By what percentage did Tesla's net income attributable to common stockholders change from 2022 to 2023?
  - Answer: ''
- **[rag] M01** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): Which of Tesla's reportable segments had the highest revenue in 2023, and how much was it?
  - Answer: ''
- **[rag] M02** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): Did Tesla's total operating expenses grow faster or slower than its total revenue from 2022 to 2023?
  - Answer: ''
- **[rag] M03** (numeric): Compare Tesla's gross margin in 2022 and 2023. Did it improve?
  - Answer: 'Based on the provided context, whether gross margin improved depends on the segment, but overall profitability/gross margin generally declined for its primary automotive segment:\n\n* **Total Automotive Gross Margin:** **Decreased** from 28.5% in 2022 to 19.4% in 2023 (did not improve).\n* **Energy Gen'
- **[rag] U01** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What is Tesla's stock price today?
  - Answer: ''
- **[rag] U02** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask): What total revenue will Tesla report for 2025?
  - Answer: ''
- **[agent] L01** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What was Tesla's total revenue in 2023?
  - Answer: ''
- **[agent] L02** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What was Tesla's net income in 2023?
  - Answer: ''
- **[agent] L03** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): How much did Tesla spend on research and development in 2023?
  - Answer: ''
- **[agent] L04** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What was Tesla's gross profit in 2023?
  - Answer: ''
- **[agent] L05** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What was Tesla's worldwide employee headcount as of December 31, 2023?
  - Answer: ''
- **[agent] L06** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What reportable segments does Tesla disclose in its 2023 10-K?
  - Answer: ''
- **[agent] L07** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): How does Tesla describe the competitive landscape of the automotive market in its 2023 10-K?
  - Answer: ''
- **[agent] L08** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What was Tesla's income from operations in 2023?
  - Answer: ''
- **[agent] C01** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What was Tesla's year-over-year total revenue growth from 2022 to 2023?
  - Answer: ''
- **[agent] C02** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What was Tesla's gross margin in 2023?
  - Answer: ''
- **[agent] C03** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What was Tesla's operating margin in 2023?
  - Answer: ''
- **[agent] C04** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What was Tesla's net profit margin in 2023?
  - Answer: ''
- **[agent] C05** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What percentage of total revenue did Tesla spend on research and development in 2023?
  - Answer: ''
- **[agent] C06** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): By what percentage did Tesla's net income attributable to common stockholders change from 2022 to 2023?
  - Answer: ''
- **[agent] M01** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): Which of Tesla's reportable segments had the highest revenue in 2023, and how much was it?
  - Answer: ''
- **[agent] M02** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): Did Tesla's total operating expenses grow faster or slower than its total revenue from 2022 to 2023?
  - Answer: ''
- **[agent] M03** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): Compare Tesla's gross margin in 2022 and 2023. Did it improve?
  - Answer: ''
- **[agent] U01** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What is Tesla's stock price today?
  - Answer: ''
- **[agent] U02** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What total revenue will Tesla report for 2025?
  - Answer: ''
- **[agent] U03** (500 Server Error: Internal Server Error for url: http://localhost:8000/ask_agent): What was Ford Motor Company's total revenue in 2023?
  - Answer: ''
