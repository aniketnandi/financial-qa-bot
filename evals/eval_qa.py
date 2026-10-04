#!/usr/bin/env python3
"""
Eval harness for the Financial Document Q&A Bot.

Runs a golden set of questions against one or more endpoints of the running
FastAPI app and scores each answer with deterministic checks:
  - numeric:  a number in the answer matches the expected value within tolerance
  - keywords: the answer contains all required keywords (case-insensitive)
  - refusal:  the bot declines questions the 10-Ks can't answer
  - source:   (optional) a returned source matches the expected filing/section

Usage:
  python eval_qa.py --base-url http://localhost:8000 \
      --endpoint rag=/ask --endpoint agent=/ask_agent \
      --golden golden_set.jsonl --out results
"""
import argparse, json, re, statistics, sys, time
from collections import defaultdict
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

SCALE = {"trillion": 1e12, "tn": 1e12, "billion": 1e9, "bn": 1e9, "b": 1e9,
         "million": 1e6, "mm": 1e6, "m": 1e6, "thousand": 1e3, "k": 1e3}
NUM_RE = re.compile(
    r"(-?\$?\(?-?\d[\d,]*\.?\d*\)?)\s*(%|percent|trillion|tn|billion|bn|million|mm|thousand|[bmk])?(?![a-z])",
    re.IGNORECASE)
REFUSAL_PHRASES = ["not found", "not available", "not mentioned", "not provided", "not disclosed",
                   "don't have", "do not have", "cannot find", "can't find", "could not find", "couldn't find", "unable to",
                   "no information", "not in the", "does not contain", "doesn't contain",
                   "not contain", "outside the scope", "i don't know"]


def extract_numbers(text):
    """Return list of (value, kind) where kind is 'percent' or 'amount'."""
    out = []
    for raw, unit in NUM_RE.findall(text):
        neg = raw.startswith("-") or ("(" in raw and ")" in raw)
        clean = re.sub(r"[^\d.]", "", raw)
        if not clean or clean == ".":
            continue
        try:
            v = float(clean)
        except ValueError:
            continue
        v = -v if neg else v
        u = (unit or "").lower()
        if u in ("%", "percent"):
            out.append((v, "percent"))
        elif u in SCALE:
            out.append((v * SCALE[u], "amount"))
        else:
            # Bare number: 10-K tables are usually "in millions"/"in thousands",
            # so try those scalings too.
            out.extend((v * s, "amount_bare") for s in (1, 1e3, 1e6, 1e9))
    return out


def check_numeric(answer, exp):
    target, unit = float(exp["value"]), exp.get("unit", "usd")
    nums = extract_numbers(answer)
    if unit == "percent":
        tol = float(exp.get("abs_tol", 0.5))  # percentage points
        return any(k == "percent" and abs(v - target) <= tol for v, k in nums)
    tol = float(exp.get("rel_tol", 0.01))
    return any(k != "percent" and target and abs(v - target) / abs(target) <= tol for v, k in nums)


def is_refusal(answer):
    a = answer.lower()
    return any(p in a for p in REFUSAL_PHRASES)


def score(item, answer, sources):
    checks = {}
    exp = item.get("expected", {})
    if item["category"] == "unanswerable":
        checks["refusal"] = is_refusal(answer)
    if "numeric" in exp:
        checks["numeric"] = check_numeric(answer, exp["numeric"])
    if "keywords" in exp:
        a = answer.lower()
        checks["keywords"] = all(k.lower() in a for k in exp["keywords"])
    if "source_contains" in exp and sources is not None:
        blob = json.dumps(sources).lower()
        checks["source"] = exp["source_contains"].lower() in blob
    return checks, (all(checks.values()) if checks else False)


def get_field(obj, dotted):
    for part in dotted.split("."):
        if isinstance(obj, dict) and part in obj:
            obj = obj[part]
        else:
            return None
    return obj


PLACEHOLDER_RE = re.compile(r"FILL_ME|<[A-Z_]+(?:[+-]\d+)?>")


def has_placeholder(item):
    return bool(PLACEHOLDER_RE.search(json.dumps(item)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--endpoint", action="append", required=True,
                    help="name=/path, repeatable (e.g. rag=/ask agent=/ask_agent)")
    ap.add_argument("--golden", default="golden_set.jsonl")
    ap.add_argument("--out", default="results")
    ap.add_argument("--question-field", default="question", help="request JSON key for the question")
    ap.add_argument("--answer-field", default="answer", help="response key (dot path) for the answer")
    ap.add_argument("--sources-field", default="sources", help="response key (dot path) for sources, if any")
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--sleep", type=float, default=0,
                    help="seconds to wait between requests (avoids Gemini free-tier 429s)")
    ap.add_argument("--retries", type=int, default=3, help="retries on transient 503 errors (429 quota errors are not retried)")
    ap.add_argument("--backoff", type=float, default=30, help="base wait (s) between rate-limit retries")
    ap.add_argument("--resume", action="store_true",
                    help="keep finished (non-ERR) results in --out and only rerun missing/ERR items")
    ap.add_argument("--ids", default="", help="comma-separated item ids to run (e.g. L01,C02)")
    args = ap.parse_args()

    items = [json.loads(l) for l in Path(args.golden).read_text().splitlines() if l.strip()]
    skipped = [i["id"] for i in items if has_placeholder(i)]
    items = [i for i in items if not has_placeholder(i)]
    if skipped:
        print(f"Skipping {len(skipped)} items with unfilled placeholders (FILL_ME / <COMPANY> / <FY>): {', '.join(skipped)}")
    if args.ids:
        wanted = {i.strip() for i in args.ids.split(",") if i.strip()}
        items = [i for i in items if i["id"] in wanted]
    if not items:
        sys.exit("No filled-in items to run. Fill in golden_set.jsonl first.")

    endpoints = dict(e.split("=", 1) for e in args.endpoint)
    out = Path(args.out); out.mkdir(exist_ok=True)
    rows, done = [], set()
    if args.resume and (out / "results.jsonl").exists():
        for l in (out / "results.jsonl").read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                if not r.get("error") and r["endpoint"] in endpoints:
                    rows.append(r); done.add((r["endpoint"], r["id"]))
        print(f"Resuming: keeping {len(rows)} finished results, rerunning the rest")

    for name, path in endpoints.items():
        url = args.base_url.rstrip("/") + path
        for item in items:
            if (name, item["id"]) in done:
                continue
            answer, sources, error = "", None, None
            for attempt in range(args.retries + 1):
                t0 = time.perf_counter()
                error = None
                try:
                    r = requests.post(url, json={args.question_field: item["question"]}, timeout=args.timeout)
                    if r.status_code >= 400:
                        try:
                            detail = r.json().get("detail", r.text)
                        except ValueError:
                            detail = r.text
                        error = f"HTTP {r.status_code}: {str(detail)[:300]}"
                    else:
                        body = r.json()
                        answer = str(get_field(body, args.answer_field) or "")
                        sources = get_field(body, args.sources_field)
                except Exception as e:
                    error = str(e)[:300]
                daily_quota = error and ("RESOURCE_EXHAUSTED" in error or "quota" in error.lower())
                transient = error and ("503" in error or "UNAVAILABLE" in error)
                rate_limited = transient or (error and "429" in error and not daily_quota)
                if not rate_limited or attempt == args.retries:
                    break
                m = re.search(r"retry in ([\d.]+)s", error, re.IGNORECASE) or re.search(r"retryDelay.{0,5}?(\d+)s", error)
                wait = float(m.group(1)) + 1 if m else args.backoff * (attempt + 1)
                print(f"    rate-limited on {item['id']}, waiting {wait:.0f}s (retry {attempt + 1}/{args.retries})")
                time.sleep(wait)
            latency = time.perf_counter() - t0
            if args.sleep:
                time.sleep(args.sleep)
            checks, passed = score(item, answer, sources) if not error else ({}, False)
            rows.append({"endpoint": name, "id": item["id"], "category": item["category"],
                         "question": item["question"], "answer": answer, "checks": checks,
                         "passed": passed, "latency_s": round(latency, 3), "error": error})
            mark = "PASS" if passed else ("ERR " if error else "FAIL")
            print(f"[{name}] {mark} {item['id']:<8} {latency:5.2f}s  {item['question'][:60]}")
            if error:
                print(f"    -> {error[:200]}")

    order = {i["id"]: n for n, i in enumerate(items)}
    rows.sort(key=lambda r: (list(endpoints).index(r["endpoint"]), order.get(r["id"], 999)))
    (out / "results.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    # Summary
    lines = ["# Q&A Bot Eval Summary", "",
             f"Golden set: {len(items)} questions ({len(skipped)} skipped as unfilled)",
             "Scores count only answered questions; ERR = API error (quota/outage), not a wrong answer. Rerun with --resume to fill them in.", ""]
    cats = sorted({r["category"] for r in rows})
    header = "| Endpoint | Overall | " + " | ".join(cats) + " | p50 latency | p95 latency |"
    lines += [header, "|" + "---|" * (len(cats) + 4)]
    for name in endpoints:
        rs = [r for r in rows if r["endpoint"] == name]
        def rate(sub):
            ans = [r for r in sub if not r["error"]]
            if not ans:
                return f"- ({len(sub)} ERR)" if sub else "-"
            p = sum(r["passed"] for r in ans)
            errs = len(sub) - len(ans)
            return f"{p}/{len(ans)} ({100*p/len(ans):.0f}%)" + (f" +{errs} ERR" if errs else "")
        lats = sorted(r["latency_s"] for r in rs if not r["error"]) or [0]
        p95 = lats[min(len(lats) - 1, int(round(0.95 * (len(lats) - 1))))]
        cells = [rate([r for r in rs if r["category"] == c]) for c in cats]
        lines.append(f"| {name} | {rate(rs)} | " + " | ".join(cells) +
                     f" | {statistics.median(lats):.2f}s | {p95:.2f}s |")
    fails = [r for r in rows if not r["passed"]]
    if fails:
        lines += ["", "## Failures", ""]
        for r in fails:
            why = r["error"] or ", ".join(k for k, v in r["checks"].items() if not v) or "no checks defined"
            lines.append(f"- **[{r['endpoint']}] {r['id']}** ({why}): {r['question']}")
            lines.append(f"  - Answer: {r['answer'][:300]!r}")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    h = next(n for n, l in enumerate(lines) if l.startswith("| Endpoint"))
    print("\n" + "\n".join(lines[h:h + 2 + len(endpoints)]))
    print(f"\nWrote {out/'results.jsonl'} and {out/'summary.md'}")


if __name__ == "__main__":
    main()
