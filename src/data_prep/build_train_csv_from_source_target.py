import os
import csv

ROOT_DIR = "Classical-Modern-main/双语数据"  # 你的书名/卷名/... 根目录
OUT_CSV = "train.csv"

MIN_LEN = 0  # 太短过滤（想不过滤就改成 0）
MAKE_SYMMETRIC = False  # 生成 (古文,现代文) + (现代文,古文)；建议 True

def read_nonempty_lines(p: str):
    lines = []
    with open(p, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            # 压缩多余空格（可选但建议）
            ln = " ".join(ln.split())
            lines.append(ln)
    return lines

pairs = []
scanned_dirs = 0
skipped_dirs = 0

for dirpath, _, filenames in os.walk(ROOT_DIR):
    if "source.txt" in filenames and "target.txt" in filenames:
        scanned_dirs += 1
        src_path = os.path.join(dirpath, "source.txt")
        tgt_path = os.path.join(dirpath, "target.txt")

        src = read_nonempty_lines(src_path)
        tgt = read_nonempty_lines(tgt_path)

        if len(src) != len(tgt):
            print(f"[WARN] 行数不一致，跳过：{dirpath}  source={len(src)} target={len(tgt)}")
            skipped_dirs += 1
            continue

        for s, t in zip(src, tgt):
            if MIN_LEN and (len(s) < MIN_LEN or len(t) < MIN_LEN):
                continue
            pairs.append((s, t))
            if MAKE_SYMMETRIC:
                pairs.append((t, s))

print(f"scanned_dirs={scanned_dirs}, skipped_dirs={skipped_dirs}, pairs={len(pairs)}")

with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    # 注意：SimCSE 这份代码按“列数”判断任务类型，所以训练CSV只留两列
    w.writerow(["sent0", "sent1"])
    w.writerows(pairs)

print(f"[OK] wrote: {OUT_CSV}")
