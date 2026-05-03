#!/usr/bin/env python3
import argparse, json
from pathlib import Path


def char_bigrams(s: str):
    s = s.strip()
    if len(s) < 2:
        return {s} if s else set()
    return {s[i:i+2] for i in range(len(s)-1)}


def jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mcq", required=True)
    args = ap.parse_args()

    items = [json.loads(x) for x in Path(args.mcq).read_text(encoding='utf-8').splitlines() if x.strip()]
    top1 = top3 = 0
    mrr = 0.0
    for it in items:
        qfp = char_bigrams(it["query"])
        scores = [jaccard(qfp, char_bigrams(c)) for c in it["choices"]]
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        rank = order.index(int(it["answer_index"])) + 1
        if rank <= 1:
            top1 += 1
        if rank <= 3:
            top3 += 1
        mrr += 1.0 / rank

    n = max(1, len(items))
    print(f"mcq={args.mcq}")
    print(f"count={len(items)}")
    print(f"Top@1={top1/n:.4f}")
    print(f"Top@3={top3/n:.4f}")
    print(f"MRR={mrr/n:.4f}")


if __name__ == '__main__':
    main()
