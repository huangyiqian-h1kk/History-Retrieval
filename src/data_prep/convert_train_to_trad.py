import pandas as pd
import random
from opencc import OpenCC

input_csv = "splits/train.csv"
output_csv = "splits/train_trad_mix50.csv"
text_columns = ["sent0", "sent1"]

convert_ratio = 0.5
random_seed = 42
progress_step = 50000

cc = OpenCC("s2t")
random.seed(random_seed)


def convert_text(x):
    if pd.isna(x):
        return x
    return cc.convert(str(x))


def main():
    print("读取 CSV...")
    df = pd.read_csv(input_csv)

    for col in text_columns:
        if col not in df.columns:
            raise ValueError(f"列不存在: {col}")

    total = len(df)
    convert_count = int(total * convert_ratio)
    chosen_indices = random.sample(list(df.index), convert_count)

    print(f"总行数: {total}")
    print(f"需要转换的行数: {convert_count}")

    chosen_indices = sorted(chosen_indices)

    for col in text_columns:
        print(f"开始转换列: {col}")
        for start in range(0, convert_count, progress_step):
            end = min(start + progress_step, convert_count)
            batch_idx = chosen_indices[start:end]
            df.loc[batch_idx, col] = df.loc[batch_idx, col].apply(convert_text)
            print(f"{col}: {end}/{convert_count} 已完成")

    print("开始写出 CSV...")
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"完成: {output_csv}")


if __name__ == "__main__":
    main()