#!/usr/bin/env bash
set -euo pipefail

# 小样本可跑通流水线：split -> mcq -> eval(lexical)

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p splits mcq_out

if [[ ! -f splits/dev.csv ]]; then
  echo "[1/4] splits/dev.csv 不存在，尝试执行切分..."
  if [[ -d "Classical-Modern-main/双语数据" ]]; then
    python -m src.data_prep.split_and_export
  else
    echo "[WARN] 未找到 Classical-Modern-main/双语数据，写入内置 demo 数据集到 splits/dev.csv"
    python - <<'PY'
import csv
from pathlib import Path
rows = [
    ("学而时习之，不亦说乎。", "学习并且按时温习，不也很快乐吗。"),
    ("温故而知新，可以为师矣。", "温习旧知识并获得新理解，就可以做老师了。"),
    ("知之为知之，不知为不知，是知也。", "知道就是知道，不知道就是不知道，这才是明智。"),
    ("三人行，必有我师焉。", "几个人同行，其中必有值得我学习的人。"),
]
Path("splits").mkdir(parents=True, exist_ok=True)
with Path("splits/dev.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerow(["sent0", "sent1"])
    w.writerows(rows)
print("[OK] wrote splits/dev.csv demo rows=", len(rows))
PY
  fi
else
  echo "[1/4] 复用已有 splits/dev.csv"
fi

echo "[2/4] 构建小样本 dev_small.csv"
python - <<'PY'
import csv
from pathlib import Path
src = Path('splits/dev.csv')
out = Path('splits/dev_small.csv')
rows = []
with src.open('r', encoding='utf-8-sig', newline='') as f:
    r = csv.reader(f)
    header = next(r)
    for i, row in enumerate(r):
        if i >= 200:
            break
        rows.append(row)
with out.open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerow(header)
    w.writerows(rows)
print(f"[OK] wrote {out} rows={len(rows)}")
PY

echo "[3/4] 生成 MCQ（每方向 20 题）"
INPUT_CSV="splits/dev_small.csv" \
OUT_DIR="mcq_out" \
N_QUESTIONS="20" \
DISTRACTOR_STRATEGY="easy" \
python -m src.eval.build_mcq

echo "[4/4] 词面基线评测"
python scripts/eval_mcq_lexical.py --mcq mcq_out/mcq_dev_small_mixed50_easy.jsonl

echo "[DONE] pipeline finished"
