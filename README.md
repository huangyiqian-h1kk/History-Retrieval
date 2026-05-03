# History-Retrieval

这个仓库的目标是：围绕“古汉语 ↔ 现代汉语”句对数据，构建训练数据、切分评测集、生成多项选择检索题（MCQ），并对句向量模型进行检索评测。

> 当前仓库以“数据与一次性脚本”为主，工程化程度较低，但核心流程已经完整：
> 原始双语语料 → 切分 train/dev/test → 生成 MCQ → 评测检索模型。

---

## 1. 仓库内容总览（按功能）

## 数据目录

- `Classical-Modern-main/`：核心语料来源目录。
  - `双语数据/`：主要平行语料（每个子目录常见 `source.txt` 与 `target.txt`）。
  - `古文原文/`：古籍原文资源，按书名/卷/回细分。
- `mcq_out/`：已经生成好的 MCQ 评测集（JSONL），含 easy/hard、不同方向与繁简版本。
- `splits_books.json`：按“书目分组”定义 train/dev/test 的配置文件（较适合做“按书不泄漏”的划分）。

## 脚本目录（当前都在仓库根目录）

### A. 语料聚合与切分

- `build_train_csv_from_source_target.py`
  - 从 `Classical-Modern-main/双语数据` 递归查找目录。
  - 读取成对 `source.txt` / `target.txt`，按行对齐后导出 `train.csv`（2列）。
  - 可选对称扩增（`MAKE_SYMMETRIC=True` 时加入反向对）。

- `split_and_export.py`
  - 以“目录级别”随机切分 train/dev/test_full/test_quick（固定 `SEED` 可复现）。
  - 输出目录清单与对应 CSV 到 `splits/`。
  - 是当前最核心的数据切分脚本之一。

- `export_split_jsonl.py`
  - 将包含 `split` 字段的 parquet 进一步导出为 train/dev/test 三个 JSONL。
  - 支持最短长度过滤、按 `sid` 去重、稳定排序。

### B. 数据增强/数据变换

- `build_method2_splitmix.py`
  - 对句对做一次“拆分+交叉拼接”（S0方案）生成混合句对。
  - 优先按标点切一次，否则中点切；无法切分则保持原句。
  - 用于制造更有挑战的匹配样本。

- `convert_train_to_trad.py`
  - 用 OpenCC 将训练 CSV 的一部分样本转繁体（可配比例，默认 50%）。
  - 典型用途：构建简繁混合训练集。

- `convert_mcq_to_trad.py`
  - 用 OpenCC 将 MCQ 中 query/choices 按比例转繁体。
  - 可生成 50% 或 100% 繁体评测集。

### C. 评测集构建与评测

- `build_mcq.py`
  - 从切分后的 CSV 构建双向 MCQ：
    - `modern2hanwen`（现代文查询 → 古文候选）
    - `hanwen2modern`（古文查询 → 现代文候选）
  - 支持干扰项策略：
    - `easy`：随机负样本
    - `hardlex`：按字bigram相似度采样“词面更像”的干扰项
  - 输出两个方向和 `mixed50` 混合集。

- `run_mcq_eval.py`
  - 用 Transformer 编码 query 与 choices，按余弦相似度做检索。
  - 输出 Top@k 与 MRR。
  - 适用于评估 SimCSE 或同类句向量模型。

## 其他

- `SimCSE/`：模型训练/输出预留目录（当前基本为空）。
- `.devcontainer/`：开发容器配置。
- `.gitignore`：已屏蔽模型权重等大文件。

---

## 2. 当前“实际流水线”建议理解方式

可按下面顺序理解同事的工作：

1. 原始语料在 `Classical-Modern-main/双语数据`。
2. 用 `split_and_export.py` 做目录级切分，输出 `splits/train.csv`、`splits/dev.csv`、`splits/test_full.csv` 等。
3. （可选）用 `build_method2_splitmix.py` 做混合句构造，或 `convert_train_to_trad.py` 做简繁混训。
4. 用 `build_mcq.py` 从 dev/test 生成检索题。
5. 用 `run_mcq_eval.py` 在 MCQ 上评估模型（Top@k / MRR）。

---

## 3. 快速开始（建议）

> 依赖（最低）：`python>=3.9`，并按脚本需要安装 `pandas`、`pyarrow`、`opencc`、`torch`、`transformers`。

示例流程：

```bash
# 1) 切分语料（输出到 splits/）
python split_and_export.py

# 2) 生成 MCQ（先在脚本里确认 INPUT_CSV 与参数）
python build_mcq.py

# 3) 评测模型（先在脚本里确认 MCQ_JSONL 与 MODEL_NAME_OR_PATH）
python run_mcq_eval.py
```

---

## 4. 当前结构问题

1. **脚本全部堆在根目录**：职责边界不清晰。
2. **大量参数硬编码在脚本内**：复现实验成本高。
3. **同类产物散落**：`splits/`、`mcq_out/`、中间文件缺统一规范。
4. **缺统一 README / docs**：新成员难上手。
5. **数据与代码耦合过紧**：无法轻松替换数据源或评测配置。

---

## 5. 推荐重组方案（不改算法，先改可维护性）

建议先做“轻量重组”而不是大改：

```text
History-Retrieval/
  README.md
  pyproject.toml / requirements.txt
  src/
    data_prep/
      build_train_csv.py
      split_and_export.py
      export_split_jsonl.py
      splitmix.py
      convert_trad.py
    eval/
      build_mcq.py
      run_mcq_eval.py
  configs/
    split.yaml
    mcq_easy.yaml
    mcq_hardlex.yaml
    eval_default.yaml
  data/
    raw/            # Classical-Modern-main (或软链接)
    processed/
      splits/
      mcq/
  outputs/
    models/
    reports/
  scripts/
    run_pipeline.sh
```

### 重组原则

- **代码入 `src/`，数据入 `data/`，结果入 `outputs/`**。
- 所有脚本参数迁移到 `configs/*.yaml`，避免改代码调参。
- 保留旧脚本入口一段时间（兼容同事习惯），逐步迁移。
- 加 `Makefile` 或 `scripts/run_pipeline.sh` 固化流程。

---

## 6. 给你的落地建议（下一步可执行）

1. 先把本 README 合并，统一“项目地图”。
2. 第二步只做“文件搬家 + import path 修正”，不改功能。
3. 第三步再做参数配置化（YAML + argparse）。
4. 第四步补最小验证：
   - 小样本跑通 split → mcq → eval。
   - 把结果写到 `outputs/reports/`。

---

## 7. 备注

- 仓库中 `Classical-Modern-main/古文原文` 体量很大，主要是语料资产，不建议与脚本逻辑混在同层浏览。
- `splits_books.json` 看起来是更“学术严谨”的书目级切分方案，但当前根脚本主要采用“目录随机切分”；后续建议二选一并固化到配置中。

---

## 8. 最小侵入式重组：迁移脚本（已提供）

仓库已提供：`scripts/migrate_to_src_layout.py`

用途：
- 把根目录现有脚本复制到 `src/data_prep/` 与 `src/eval/`。
- 同时把根目录脚本替换为兼容入口（stub），保持你原来的命令仍可执行。

### 使用方式

```bash
# 仅预览迁移计划
python scripts/migrate_to_src_layout.py --dry-run

# 执行迁移（默认：复制到 src + 根目录生成兼容入口）
python scripts/migrate_to_src_layout.py

# 仅复制，不改根目录脚本
python scripts/migrate_to_src_layout.py --copy-only
```

迁移后推荐新入口：

```bash
python -m src.data_prep.split_and_export
python -m src.eval.build_mcq
python -m src.eval.run_mcq_eval
```

### 一条命令小样本跑通

```bash
bash scripts/run_pipeline.sh
```

该脚本会：
1. 若缺少 `splits/dev.csv` 则自动运行切分；
2. 生成 `splits/dev_small.csv`（前200行）；
3. 生成小样本 MCQ（每方向20题）；
4. 用 `scripts/eval_mcq_lexical.py` 做轻量评测并输出 Top@1/Top@3/MRR。
