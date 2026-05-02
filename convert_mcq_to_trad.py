import json
import random
from opencc import OpenCC

# ===== 配置区 =====
input_file = "mcq_out/hard_0_10000.jsonl"
output_file = "mcq_out/hard_0_10000_trad50.jsonl"

# 转换比例
# 1.0 = 全繁体
# 0.5 = 50% 题目转繁体
convert_ratio = 0.5

# 随机种子，保证可复现
random_seed = 42

cc = OpenCC("s2t")
random.seed(random_seed)


def to_trad(x):
    if x is None:
        return x
    return cc.convert(str(x))


def convert_one_item(obj):
    if "query" in obj:
        obj["query"] = to_trad(obj["query"])

    if "choices" in obj and isinstance(obj["choices"], list):
        obj["choices"] = [to_trad(c) for c in obj["choices"]]

    return obj


def main():
    with open(input_file, "r", encoding="utf-8") as fin:
        data = [json.loads(line) for line in fin]

    total = len(data)
    convert_count = int(total * convert_ratio)

    # 全转
    if convert_ratio >= 1.0:
        chosen = set(range(total))
    # 全不转
    elif convert_ratio <= 0.0:
        chosen = set()
    else:
        chosen = set(random.sample(range(total), convert_count))

    with open(output_file, "w", encoding="utf-8") as fout:
        for i, obj in enumerate(data):
            if i in chosen:
                obj = convert_one_item(obj)
            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"已输出: {output_file}")
    print(f"总题数: {total}")
    print(f"转换题数: {len(chosen)}")
    print(f"实际转换比例: {len(chosen) / total:.4f}" if total > 0 else "空文件")


if __name__ == "__main__":
    main()