#!/usr/bin/env python3
"""最小侵入式迁移脚本：把根目录脚本迁移到 src/，并保留根目录兼容入口。"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_PREP = [
    "build_train_csv_from_source_target.py",
    "split_and_export.py",
    "export_split_jsonl.py",
    "build_method2_splitmix.py",
    "convert_train_to_trad.py",
    "convert_mcq_to_trad.py",
]

EVAL = [
    "build_mcq.py",
    "run_mcq_eval.py",
]


def ensure_pkg(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    init = path / "__init__.py"
    if not init.exists():
        init.write_text("", encoding="utf-8")


def write_stub(root_script: Path, module_path: str) -> None:
    stub = f'''#!/usr/bin/env python3
"""兼容入口（自动生成）。请优先使用: python -m {module_path}"""
import runpy

if __name__ == "__main__":
    runpy.run_module("{module_path}", run_name="__main__")
'''
    root_script.write_text(stub, encoding="utf-8")


def migrate(copy_only: bool, dry_run: bool) -> None:
    src_root = ROOT / "src"
    dp_dir = src_root / "data_prep"
    ev_dir = src_root / "eval"

    ensure_pkg(src_root)
    ensure_pkg(dp_dir)
    ensure_pkg(ev_dir)

    plan = []
    for fn in DATA_PREP:
        plan.append((ROOT / fn, dp_dir / fn, f"src.data_prep.{fn[:-3]}"))
    for fn in EVAL:
        plan.append((ROOT / fn, ev_dir / fn, f"src.eval.{fn[:-3]}"))

    for old_path, new_path, module in plan:
        if not old_path.exists():
            print(f"[SKIP] missing: {old_path.relative_to(ROOT)}")
            continue

        print(f"[PLAN] {old_path.relative_to(ROOT)} -> {new_path.relative_to(ROOT)}")
        if dry_run:
            continue

        new_path.parent.mkdir(parents=True, exist_ok=True)
        content = old_path.read_text(encoding="utf-8")
        new_path.write_text(content, encoding="utf-8")

        if not copy_only:
            write_stub(old_path, module)

    if not dry_run:
        (ROOT / "configs" / "README.md").write_text(
            "# configs\n\n放置 split/mcq/eval 的参数配置文件（YAML/JSON）。\n",
            encoding="utf-8",
        )

    print("\n[OK] migration finished")
    print("建议后续执行：")
    print("  1) python -m src.data_prep.split_and_export")
    print("  2) python -m src.eval.build_mcq")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--copy-only", action="store_true", help="仅复制到 src，不覆盖根目录脚本")
    ap.add_argument("--dry-run", action="store_true", help="仅打印迁移计划")
    args = ap.parse_args()
    migrate(copy_only=args.copy_only, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
