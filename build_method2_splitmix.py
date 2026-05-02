#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import re
import argparse
from pathlib import Path
from typing import Tuple, List

# 你数据里常见的断句标点（可按需要增减）
PUNCTS = "，,、。；;：:！!？?"
PUNCT_RE = re.compile(rf"[{re.escape(PUNCTS)}]+")

def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

def first_punct_in_text(s: str) -> str:
    """从原句里找第一个出现的标点，作为 joiner。找不到就返回默认 '，'。"""
    for ch in s:
        if ch in PUNCTS:
            return "，" if ch == "," else ch
    return "，"

def split_once_by_punct(s: str, min_seg_len: int) -> Tuple[List[str], str]:
    """
    尝试“按标点只切一次”为两段。
    成功返回 ( [left, right], joiner )；joiner 用原句第一个标点（或默认 '，'）
    失败返回 ( [s], "" )
    """
    s0 = s
    s = normalize(s)

    for i, ch in enumerate(s):
        if ch in PUNCTS:
            left = normalize(s[:i])
            right = normalize(s[i+1:])
            if len(left) >= min_seg_len and len(right) >= min_seg_len:
                return [left, right], first_punct_in_text(s0)
            break
    return [s], ""

def split_once_mid(s: str, min_seg_len: int) -> Tuple[List[str], str]:
    """
    中间硬切一次为两段（不加 joiner）。
    如果太短切不了，返回 [s]。
    """
    s = normalize(s)
    if len(s) < 2 * min_seg_len:
        return [s], ""
    mid = len(s) // 2
    left = normalize(s[:mid])
    right = normalize(s[mid:])
    if len(left) >= min_seg_len and len(right) >= min_seg_len:
        return [left, right], ""
    return [s], ""

def smart_split_once(
    s: str,
    min_total_len_for_split: int,
    min_seg_len: int
) -> Tuple[List[str], str]:
    """
    足够长才尝试切：
    - 先标点切一次（成功则 joiner=标点）
    - 不行再 mid 切一次（joiner=""）
    - 仍不行：不切
    """
    s = normalize(s)
    if len(s) < min_total_len_for_split:
        return [s], ""

    parts, joiner = split_once_by_punct(s, min_seg_len=min_seg_len)
    if len(parts) == 2:
        return parts, joiner

    parts, joiner = split_once_mid(s, min_seg_len=min_seg_len)
    return parts, joiner  # len(parts) 可能是 1 或 2

def read_pairs_csv(path: Path):
    pairs = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        _ = next(r, None)  # skip header
        for row in r:
            if not row or len(row) < 2:
                continue
            hanwen = row[0].strip()
            modern = row[1].strip()
            if hanwen and modern:
                pairs.append((hanwen, modern))
    return pairs

def write_pairs_csv(path: Path, pairs):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["hanwen", "modern"])
        for a, b in pairs:
            w.writerow([a, b])

def make_s0_pair_one_row(
    hanwen: str,
    modern: str,
    min_total_len_for_split_hanwen: int,
    min_total_len_for_split_modern: int,
    min_seg_len: int,
) -> List[tuple]:
    """
    方案A / S0（你图里的那个）——每个原始pair只输出 1 行：

    如果两边都能切成两段：
      out_hanwen = C_top + (若标点切成功则加 joiner) + T_bottom
      out_modern = T_top + (若标点切成功则加 joiner) + C_bottom
      返回 [(out_hanwen, out_modern)]

    如果任意一边切不出两段：
      返回 [(C, T)]  （保底，保证总行数不变、不丢数据）
    """
    C0 = hanwen
    T0 = modern
    C = normalize(hanwen)
    T = normalize(modern)
    if not C or not T:
        return []

    c_parts, c_join = smart_split_once(C0, min_total_len_for_split_hanwen, min_seg_len)
    t_parts, t_join = smart_split_once(T0, min_total_len_for_split_modern, min_seg_len)

    if len(c_parts) < 2 or len(t_parts) < 2:
        return [(C, T)]

    C_top, C_bottom = c_parts[0], c_parts[1]
    T_top, T_bottom = t_parts[0], t_parts[1]

    # 标点切成功 joiner 才非空；mid 切 joiner=""
    out_left  = normalize(C_top + (c_join if c_join else "") + T_bottom)
    out_right = normalize(T_top + (t_join if t_join else "") + C_bottom)

    return [(out_left, out_right)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--out_csv", required=True)

    ap.add_argument("--min_total_len_for_split_hanwen", type=int, default=12)
    ap.add_argument("--min_total_len_for_split_modern", type=int, default=18)
    ap.add_argument("--min_seg_len", type=int, default=4)

    args = ap.parse_args()

    pairs = read_pairs_csv(Path(args.in_csv))
    out = []

    for hanwen, modern in pairs:
        out.extend(make_s0_pair_one_row(
            hanwen, modern,
            min_total_len_for_split_hanwen=args.min_total_len_for_split_hanwen,
            min_total_len_for_split_modern=args.min_total_len_for_split_modern,
            min_seg_len=args.min_seg_len,
        ))

    write_pairs_csv(Path(args.out_csv), out)
    print(f"[OK] in_pairs={len(pairs)} out_pairs={len(out)} wrote={args.out_csv}")

if __name__ == "__main__":
    main()
