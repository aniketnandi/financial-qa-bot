# Retrieval Eval Summary

17 answerable golden-set questions; evidence = exact 10-K strings needed to answer.

| top-k | Full hit | Partial | Miss | calculation | lookup | multi_hop |
|---|---|---|---|---|---|---|
| 4 | 16/17 (94%) | 0/17 | 1/17 | 6/6 | 8/8 | 2/3 |
| 8 | 17/17 (100%) | 0/17 | 0/17 | 6/6 | 8/8 | 3/3 |

## Diagnosis of misses (max k)

| id | missing evidence | chunks in index containing it | best rank of such a chunk |
|---|---|---|---|

## Not fully retrieved

- k=4 **M01** missing ['90,738'] (pages [50, 53, 47, 123]): Which of Tesla's reportable segments had the highest revenue in 2023, and how much was it?
