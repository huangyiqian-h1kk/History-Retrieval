import os
import csv
import random
from pathlib import Path

# 你给的根目录
ROOT_DIR = Path("Classical-Modern-main/双语数据")

SEED = 42

# 按“目录数量”切分（总目录约 7304）
DEV_DIRS = 730
TEST_FULL_DIRS = 730
TEST_QUICK_DIRS = 73  # 从 test_full 再抽

# 轻量清洗
MIN_LEN = 0  # 太短过滤；不想过滤设为 0
COMPRESS_SPACES = True  # 压缩多余空格

# 输出目录
OUT_DIR = Path("splits")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def read_nonempty_lines(p: Path):
    lines = []
    with p.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            if COMPRESS_SPACES:
                ln = " ".join(ln.split())
            lines.append(ln)
    return lines

def find_pair_dirs(root: Path):
    pair_dirs = []
    for dirpath, _, filenames in os.walk(root):
        fn = set(filenames)
        if "source.txt" in fn and "target.txt" in fn:
            pair_dirs.append(Path(dirpath))
    return sorted(pair_dirs)

def write_dir_list(dir_list, out_txt: Path, root: Path):
    with out_txt.open("w", encoding="utf-8") as f:
        for d in dir_list:
            f.write(str(d.relative_to(root)) + "\n")

def export_csv(dir_list, out_csv: Path):
    total_pairs = 0
    skipped_dirs = 0
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["sent0", "sent1"])  # 两列：古文、现代文

        for d in dir_list:
            src = read_nonempty_lines(d / "source.txt")
            tgt = read_nonempty_lines(d / "target.txt")

            if len(src) != len(tgt):
                skipped_dirs += 1
                continue

            for s, t in zip(src, tgt):
                if MIN_LEN and (len(s) < MIN_LEN or len(t) < MIN_LEN):
                    continue
                w.writerow([s, t])
                total_pairs += 1

    return total_pairs, skipped_dirs

def main():
    root = ROOT_DIR.resolve()
    if not root.exists():
        raise FileNotFoundError(f"ROOT_DIR not found: {root}")

    pair_dirs = find_pair_dirs(root)
    n = len(pair_dirs)
    print(f"found_pair_dirs={n}  root={root}")

    if DEV_DIRS + TEST_FULL_DIRS >= n:
        raise ValueError("DEV_DIRS + TEST_FULL_DIRS 太大了，超过总目录数")

    rng = random.Random(SEED)
    rng.shuffle(pair_dirs)

    test_full_dirs = pair_dirs[:TEST_FULL_DIRS]
    dev_dirs = pair_dirs[TEST_FULL_DIRS:TEST_FULL_DIRS + DEV_DIRS]
    train_dirs = pair_dirs[TEST_FULL_DIRS + DEV_DIRS:]

    # test_quick 从 test_full 里抽
    if TEST_QUICK_DIRS > len(test_full_dirs):
        raise ValueError("TEST_QUICK_DIRS 大于 test_full 目录数")
    test_quick_dirs = rng.sample(test_full_dirs, k=TEST_QUICK_DIRS)

    # 输出目录清单（可复现）
    write_dir_list(train_dirs, OUT_DIR / "train_dirs.txt", root)
    write_dir_list(dev_dirs, OUT_DIR / "dev_dirs.txt", root)
    write_dir_list(test_full_dirs, OUT_DIR / "test_full_dirs.txt", root)
    write_dir_list(test_quick_dirs, OUT_DIR / "test_quick_dirs.txt", root)

    print(f"split_dirs: train={len(train_dirs)} dev={len(dev_dirs)} "
          f"test_full={len(test_full_dirs)} test_quick={len(test_quick_dirs)}")

    # 导出 CSV
    train_pairs, train_skipped = export_csv(train_dirs, OUT_DIR / "train.csv")
    dev_pairs, dev_skipped = export_csv(dev_dirs, OUT_DIR / "dev.csv")
    test_full_pairs, test_full_skipped = export_csv(test_full_dirs, OUT_DIR / "test_full.csv")
    test_quick_pairs, test_quick_skipped = export_csv(test_quick_dirs, OUT_DIR / "test_quick.csv")

    print(f"train.csv      pairs={train_pairs} skipped_dirs={train_skipped}")
    print(f"dev.csv        pairs={dev_pairs} skipped_dirs={dev_skipped}")
    print(f"test_full.csv  pairs={test_full_pairs} skipped_dirs={test_full_skipped}")
    print(f"test_quick.csv pairs={test_quick_pairs} skipped_dirs={test_quick_skipped}")
    print(f"[OK] outputs in: {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
