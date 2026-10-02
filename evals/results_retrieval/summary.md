# Retrieval Eval Summary

17 answerable golden-set questions; evidence = exact 10-K strings needed to answer.

| top-k | Full hit | Partial | Miss | calculation | lookup | multi_hop |
|---|---|---|---|---|---|---|
| 4 | 11/17 (65%) | 1/17 | 5/17 | 4/6 | 6/8 | 1/3 |
| 8 | 12/17 (71%) | 1/17 | 4/17 | 4/6 | 7/8 | 1/3 |

## Diagnosis of misses (max k)

| id | missing evidence | chunks in index containing it | best rank of such a chunk |
|---|---|---|---|
| L08 | 8,891 | 1 (pages [50]) | 129 |
| C03 | 8,891 | 1 (pages [50]) | 315 |
| C06 | 14,997 | 3 (pages [50, 52, 62]) | 27 |
| C06 | 12,556 | 4 (pages [50, 52, 62]) | 27 |
| M01 | 90,738 | 2 (pages [38, 93]) | 28 |
| M02 | 8,769 | 1 (pages [50]) | 219 |
| M02 | 7,197 | 1 (pages [50]) | 219 |

## Not fully retrieved

- k=4 **L06** missing ['energy generation and storage'] (pages [123, 2, 123, 90]): What reportable segments does Tesla disclose in its 2023 10-K?
- k=4 **L08** missing ['8,891'] (pages [50, 53, 123, 51]): What was Tesla's income from operations in 2023?
- k=4 **C03** missing ['8,891'] (pages [50, 123, 53, 2]): What was Tesla's operating margin in 2023?
- k=4 **C06** missing ['14,997', '12,556'] (pages [51, 123, 53, 50]): By what percentage did Tesla's net income attributable to common stockholders change from 2022 to 2023?
- k=4 **M01** missing ['90,738'] (pages [50, 123, 53, 51]): Which of Tesla's reportable segments had the highest revenue in 2023, and how much was it?
- k=4 **M02** missing ['8,769', '7,197'] (pages [50, 39, 53, 33]): Did Tesla's total operating expenses grow faster or slower than its total revenue from 2022 to 2023?
- k=8 **L08** missing ['8,891'] (pages [50, 53, 123, 51, 92, 13, 9, 113]): What was Tesla's income from operations in 2023?
- k=8 **C03** missing ['8,891'] (pages [50, 123, 53, 2, 6, 13, 113, 90]): What was Tesla's operating margin in 2023?
- k=8 **C06** missing ['14,997', '12,556'] (pages [51, 123, 53, 50, 92, 33, 52, 33]): By what percentage did Tesla's net income attributable to common stockholders change from 2022 to 2023?
- k=8 **M01** missing ['90,738'] (pages [50, 123, 53, 51, 39, 56, 47, 92]): Which of Tesla's reportable segments had the highest revenue in 2023, and how much was it?
- k=8 **M02** missing ['8,769', '7,197'] (pages [50, 39, 53, 33, 40, 41, 35, 6]): Did Tesla's total operating expenses grow faster or slower than its total revenue from 2022 to 2023?
