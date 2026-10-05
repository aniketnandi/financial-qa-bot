# Retrieval Eval Summary

17 answerable golden-set questions; evidence = exact 10-K strings needed to answer.

| retriever | top-k | Full hit | Partial | Miss | calculation | lookup | multi_hop |
|---|---|---|---|---|---|---|---|
| dense | 4 | 16/17 (94%) | 0/17 | 1/17 | 6/6 | 8/8 | 2/3 |
| dense | 8 | 17/17 (100%) | 0/17 | 0/17 | 6/6 | 8/8 | 3/3 |
| bm25 | 4 | 9/17 (53%) | 2/17 | 6/17 | 1/6 | 6/8 | 2/3 |
| bm25 | 8 | 11/17 (65%) | 2/17 | 4/17 | 2/6 | 6/8 | 3/3 |
| hybrid | 4 | 13/17 (76%) | 0/17 | 4/17 | 4/6 | 6/8 | 3/3 |
| hybrid | 8 | 16/17 (94%) | 0/17 | 1/17 | 6/6 | 7/8 | 3/3 |

## Diagnosis of misses (k=8)

| retriever | id | missing evidence | chunks in index containing it | best rank of such a chunk |
|---|---|---|---|---|
| bm25 | L01 | 96,773 | 4 (pages [38, 50, 56, 93]) | 21 |
| bm25 | L03 | 3,969 | 2 (pages [41, 50]) | 14 |
| bm25 | C01 | 96,773 | 4 (pages [38, 50, 56, 93]) | 14 |
| bm25 | C01 | 81,462 | 4 (pages [38, 50, 56, 93]) | 14 |
| bm25 | C02 | 96,773 | 4 (pages [38, 50, 56, 93]) | 10 |
| bm25 | C03 | 8,891 | 1 (pages [50]) | 45 |
| bm25 | C03 | 96,773 | 4 (pages [38, 50, 56, 93]) | 45 |
| bm25 | C05 | 96,773 | 4 (pages [38, 50, 56, 93]) | 17 |
| hybrid | L01 | 96,773 | 4 (pages [38, 50, 56, 93]) | 7 |

## Not fully retrieved

- dense k=4 **M01** missing ['90,738'] (pages [50, 53, 47, 123]): Which of Tesla's reportable segments had the highest revenue in 2023, and how much was it?
- bm25 k=4 **L01** missing ['96,773'] (pages [39, 40, 57, 92]): What was Tesla's total revenue in 2023?
- bm25 k=4 **L03** missing ['3,969'] (pages [88, 86, 110, 20]): How much did Tesla spend on research and development in 2023?
- bm25 k=4 **C01** missing ['96,773', '81,462'] (pages [39, 40, 38, 57]): What was Tesla's year-over-year total revenue growth from 2022 to 2023?
- bm25 k=4 **C02** missing ['96,773'] (pages [41, 40, 39, 39]): What was Tesla's gross margin in 2023?
- bm25 k=4 **C03** missing ['8,891', '96,773'] (pages [41, 40, 76, 39]): What was Tesla's operating margin in 2023?
- bm25 k=4 **C04** missing ['14,974', '96,773'] (pages [39, 40, 41, 62]): What was Tesla's net profit margin in 2023?
- bm25 k=4 **C05** missing ['96,773'] (pages [41, 86, 33, 88]): What percentage of total revenue did Tesla spend on research and development in 2023?
- bm25 k=4 **M02** missing ['8,769', '7,197'] (pages [92, 45, 40, 39]): Did Tesla's total operating expenses grow faster or slower than its total revenue from 2022 to 2023?
- bm25 k=8 **L01** missing ['96,773'] (pages [39, 40, 57, 92, 49, 57, 57, 59]): What was Tesla's total revenue in 2023?
- bm25 k=8 **L03** missing ['3,969'] (pages [88, 86, 110, 20, 110, 67, 35, 14]): How much did Tesla spend on research and development in 2023?
- bm25 k=8 **C01** missing ['96,773', '81,462'] (pages [39, 40, 38, 57, 33, 59, 40, 41]): What was Tesla's year-over-year total revenue growth from 2022 to 2023?
- bm25 k=8 **C02** missing ['96,773'] (pages [41, 40, 39, 39, 76, 72, 72, 65]): What was Tesla's gross margin in 2023?
- bm25 k=8 **C03** missing ['8,891', '96,773'] (pages [41, 40, 76, 39, 90, 34, 89, 39]): What was Tesla's operating margin in 2023?
- bm25 k=8 **C05** missing ['96,773'] (pages [41, 86, 33, 88, 59, 86, 110, 110]): What percentage of total revenue did Tesla spend on research and development in 2023?
- hybrid k=4 **L01** missing ['96,773'] (pages [39, 49, 92, 40]): What was Tesla's total revenue in 2023?
- hybrid k=4 **L06** missing ['energy generation and storage'] (pages [122, 123, 124, 47]): What reportable segments does Tesla disclose in its 2023 10-K?
- hybrid k=4 **C01** missing ['96,773', '81,462'] (pages [39, 38, 40, 41]): What was Tesla's year-over-year total revenue growth from 2022 to 2023?
- hybrid k=4 **C03** missing ['8,891', '96,773'] (pages [89, 39, 34, 55]): What was Tesla's operating margin in 2023?
- hybrid k=8 **L01** missing ['96,773'] (pages [39, 49, 92, 40, 38, 41, 88, 33]): What was Tesla's total revenue in 2023?
