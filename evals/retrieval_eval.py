#!/usr/bin/env python3
"""
Retrieval-only eval for the Financial Document Q&A Bot. Uses NO Gemini calls.

For each golden-set question with an "evidence" list (the exact strings from
the 10-K needed to answer it, e.g. "96,773" for 2023 revenue in millions), this
runs the same retrieval code the bot uses (retrieval.py) and checks whether the
top-k retrieved chunks contain that evidence.

  hit      = every evidence string appears in the top-k chunks
  partial  = some but not all appear (e.g. found 2023 revenue but not 2022)

Compare retrievers (dense FAISS, BM25, hybrid RRF) side by side:
  python evals/retrieval_eval.py --retriever dense bm25 hybrid --k 4 8 --diagnose
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # project root, for retrieval.py


def norm(text):
    """Lowercase and collapse whitespace, so PDF line breaks don't split phrases."""
    return re.sub(r"\s+", " ", text).lower()


def score_item(item, chunks):
    blob = norm(" ".join(chunks))
    found = [e for e in item["evidence"] if norm(e) in blob]
    return {"found": found, "missing": [e for e in item["evidence"] if e not in found],
            "hit": len(found) == len(item["evidence"]), "partial": 0 < len(found) < len(item["evidence"])}


def main():
    from retrieval import MODES, Retriever, load_store

    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default="evals/golden_set.jsonl")
    ap.add_argument("--index", default="faiss_index")
    ap.add_argument("--retriever", nargs="+", choices=MODES, default=["dense"],
                    help="one or more retrievers to compare, e.g. --retriever dense bm25 hybrid")
    ap.add_argument("--k", type=int, nargs="+", default=[4], help="one or more top-k values, e.g. --k 4 8")
    ap.add_argument("--out", default="evals/results_retrieval")
    ap.add_argument("--diagnose", action="store_true",
                    help="for misses, report whether the evidence exists anywhere in the index and at what rank")
    args = ap.parse_args()

    store = load_store(args.index)
    retrievers = {m: Retriever(store, mode=m) for m in args.retriever}
    all_docs = list(store.docstore._dict.values())

    items = [json.loads(l) for l in Path(args.golden).read_text(encoding="utf-8").splitlines() if l.strip()]
    items = [i for i in items if i.get("evidence")]
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    cats = sorted({i["category"] for i in items})
    lines = ["# Retrieval Eval Summary", "",
             f"{len(items)} answerable golden-set questions; evidence = exact 10-K strings needed to answer.", "",
             "| retriever | top-k | Full hit | Partial | Miss | " + " | ".join(cats) + " |",
             "|" + "---|" * (5 + len(cats))]
    rows = []
    for mode, retriever in retrievers.items():
        for k in args.k:
            res = []
            for item in items:
                docs = retriever.search(item["question"], k=k)
                s = score_item(item, [d.page_content for d in docs])
                s.update({"retriever": mode, "k": k, "id": item["id"], "category": item["category"],
                          "question": item["question"], "pages": [d.metadata.get("page") for d in docs]})
                res.append(s)
                mark = "HIT " if s["hit"] else ("PART" if s["partial"] else "MISS")
                print(f"[{mode} k={k}] {mark} {item['id']:<4} pages={s['pages']}  missing={s['missing']}")
            rows += res
            n = len(res)
            hits, parts = sum(r["hit"] for r in res), sum(r["partial"] for r in res)
            cat_cells = []
            for c in cats:
                sub = [r for r in res if r["category"] == c]
                cat_cells.append(f"{sum(r['hit'] for r in sub)}/{len(sub)}")
            lines.append(f"| {mode} | {k} | {hits}/{n} ({100*hits/n:.0f}%) | {parts}/{n} | {n-hits-parts}/{n} | "
                         + " | ".join(cat_cells) + " |")
    table_end = len(lines)

    if args.diagnose:
        kmax = max(args.k)
        lines += ["", f"## Diagnosis of misses (k={kmax})", "",
                  "| retriever | id | missing evidence | chunks in index containing it | best rank of such a chunk |",
                  "|---|---|---|---|---|"]
        print("\nDiagnosis:")
        for r in [r for r in rows if r["k"] == kmax and not r["hit"]]:
            item = next(i for i in items if i["id"] == r["id"])
            ranked = retrievers[r["retriever"]].search(item["question"], k=len(all_docs))
            for e in r["missing"]:
                holders = [d for d in all_docs if norm(e) in norm(d.page_content)]
                pages = sorted({d.metadata.get("page") for d in holders}, key=str)
                rank = next((n + 1 for n, d in enumerate(ranked) if norm(e) in norm(d.page_content)), None)
                print(f"  [{r['retriever']}] {r['id']} '{e}': in {len(holders)} chunk(s) (pages {pages}), "
                      f"best rank {rank} of {len(all_docs)}")
                lines.append(f"| {r['retriever']} | {r['id']} | {e} | {len(holders)} (pages {pages}) | "
                             f"{rank if rank else 'not in index'} |")

    misses = [r for r in rows if not r["hit"]]
    if misses:
        lines += ["", "## Not fully retrieved", ""]
        lines += [f"- {r['retriever']} k={r['k']} **{r['id']}** missing {r['missing']} (pages {r['pages']}): "
                  f"{r['question']}" for r in misses]
    (out / "results.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines[4:table_end]))
    print(f"\nWrote {out/'summary.md'}")


if __name__ == "__main__":
    main()
