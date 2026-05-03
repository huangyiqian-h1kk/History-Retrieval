import argparse
import json
from pathlib import Path
import pandas as pd

KEEP_COLS = [
    "sid", "text", "book", "bucket", "group",
    "file_rel", "line_no", "sent_no_in_line", "chars",
    "split"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_parquet", default="corpus_split.parquet")
    ap.add_argument("--out_dir", default="splits_jsonl")
    ap.add_argument("--min_chars", type=int, default=0, help="过滤太短句子（按 chars）")
    ap.add_argument("--dedup_sid", action="store_true", help="按 sid 去重（防万一）")
    args = ap.parse_args()

    df = pd.read_parquet(args.in_parquet)
    if "split" not in df.columns:
        raise SystemExit("ERROR: split column not found. Did you run split_books.py?")

    # 可选过滤短句
    if args.min_chars > 0 and "chars" in df.columns:
        df = df[df["chars"] >= args.min_chars].copy()

    # 可选去重
    if args.dedup_sid and "sid" in df.columns:
        df = df.drop_duplicates(subset=["sid"], keep="first")

    # 尽量稳定顺序（你数据里这些列基本都有）
    sort_cols = [c for c in ["book", "file_rel", "line_no", "sent_no_in_line"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, kind="mergesort")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 选择实际存在的列
    cols = [c for c in KEEP_COLS if c in df.columns]

    for sp in ["train", "dev", "test"]:
        sub = df[df["split"] == sp][cols].copy()
        out_path = out_dir / f"{sp}.jsonl"

        with out_path.open("w", encoding="utf-8") as f:
            for _, row in sub.iterrows():
                obj = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
                # 确保纯 Python 类型（避免 numpy/int64 之类）
                for k, v in list(obj.items()):
                    if hasattr(v, "item"):
                        obj[k] = v.item()
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")

        print(f"✅ saved: {out_path} (n={len(sub)})")

if __name__ == "__main__":
    main()
