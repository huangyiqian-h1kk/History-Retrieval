import csv
import json
import os
import random
from pathlib import Path

# ========== 配置 ==========
INPUT_CSV = Path(os.getenv("INPUT_CSV", "splits/dev.csv"))   # 改成 splits/test_full.csv 就生成 full
OUT_DIR = Path(os.getenv("OUT_DIR", "mcq_out"))
SEED = int(os.getenv("SEED", "42"))

N_CHOICES = int(os.getenv("N_CHOICES", "4"))              # 1 correct + 3 distractors
N_QUESTIONS = int(os.getenv("N_QUESTIONS", "2000"))       # 每个方向生成多少题；0 或 None 表示全量（不建议）
DISTRACTOR_STRATEGY = os.getenv("DISTRACTOR_STRATEGY", "easy")   # "easy" 或 "hardlex"
HARDLEX_CANDIDATE_POOL = int(os.getenv("HARDLEX_CANDIDATE_POOL", "200"))   # hardlex: 候选池越大越难、也越慢
# ==========================

def read_pairs(csv_path: Path):
    pairs = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        _ = next(r, None)  # skip header
        for row in r:
            if not row or len(row) < 2:
                continue
            a = row[0].strip()
            b = row[1].strip()
            if a and b:
                pairs.append((a, b))
    return pairs

def char_bigrams(s: str):
    s = s.strip()
    if len(s) < 2:
        return {s} if s else set()
    return {s[i:i+2] for i in range(len(s) - 1)}

def jaccard(a_set, b_set):
    if not a_set and not b_set:
        return 0.0
    inter = len(a_set & b_set)
    union = len(a_set | b_set)
    return inter / union if union else 0.0

def pick_distractors_easy(rng, all_candidates, correct, k):
    picked = set()
    while len(picked) < k:
        c = rng.choice(all_candidates)
        if c != correct:
            picked.add(c)
    return list(picked)

def pick_distractors_hardlex(rng, all_candidates, correct, k, pool_size, correct_fp, fps):
    if pool_size < k:
        pool_size = k

    idxs = [rng.randrange(len(all_candidates)) for _ in range(pool_size)]
    scored = []
    for idx in idxs:
        c = all_candidates[idx]
        if c == correct:
            continue
        sim = jaccard(correct_fp, fps[idx])
        scored.append((sim, c))

    scored.sort(key=lambda x: x[0], reverse=True)

    picked = []
    used = set()
    for _, c in scored:
        if c != correct and c not in used:
            used.add(c)
            picked.append(c)
        if len(picked) >= k:
            break

    if len(picked) < k:
        needed = k - len(picked)
        extra = pick_distractors_easy(rng, all_candidates, correct, needed)
        for e in extra:
            if e != correct and e not in used:
                used.add(e)
                picked.append(e)
            if len(picked) >= k:
                break

    return picked[:k]

def build_mcq(pairs, direction, strategy, rng):
    """
    direction:
      - "modern2hanwen": query=modern, choices=hanwen
      - "hanwen2modern": query=hanwen, choices=modern
    """
    items = []

    if direction == "modern2hanwen":
        queries = [t for _, t in pairs]
        candidates = [s for s, _ in pairs]
        fp_list = [char_bigrams(x) for x in candidates] if strategy == "hardlex" else None
        query_type = "modern"
        choice_type = "hanwen"
    elif direction == "hanwen2modern":
        queries = [s for s, _ in pairs]
        candidates = [t for _, t in pairs]
        fp_list = [char_bigrams(x) for x in candidates] if strategy == "hardlex" else None
        query_type = "hanwen"
        choice_type = "modern"
    else:
        raise ValueError("unknown direction")

    # ---- 只抽取固定数量的问题（可复现）----
    idxs = list(range(len(queries)))
    rng.shuffle(idxs)

    if N_QUESTIONS is None or N_QUESTIONS == 0:
        use_idxs = idxs
    else:
        use_idxs = idxs[:min(N_QUESTIONS, len(idxs))]

    for i in use_idxs:
        q = queries[i]
        correct = candidates[i]

        if strategy == "easy":
            distractors = pick_distractors_easy(rng, candidates, correct, N_CHOICES - 1)
        elif strategy == "hardlex":
            distractors = pick_distractors_hardlex(
                rng,
                candidates,
                correct,
                N_CHOICES - 1,
                HARDLEX_CANDIDATE_POOL,
                fp_list[i],
                fp_list,
            )
        else:
            raise ValueError("unknown strategy")

        options = [correct] + distractors
        rng.shuffle(options)
        answer_index = options.index(correct)

        items.append({
            "id": f"{direction}_{i}",
            "direction": direction,
            "query_type": query_type,
            "choice_type": choice_type,
            "query": q,
            "choices": options,
            "answer_index": answer_index
        })

    return items

def write_jsonl(items, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

def main():
    rng = random.Random(SEED)
    pairs = read_pairs(INPUT_CSV)
    print(f"loaded_pairs={len(pairs)} from {INPUT_CSV}")

    # 两个方向各生成 N_QUESTIONS
    m2h = build_mcq(pairs, "modern2hanwen", DISTRACTOR_STRATEGY, rng)
    h2m = build_mcq(pairs, "hanwen2modern", DISTRACTOR_STRATEGY, rng)

    tag = INPUT_CSV.stem  # test_quick / test_full
    out1 = OUT_DIR / f"mcq_{tag}_modern2hanwen_{DISTRACTOR_STRATEGY}.jsonl"
    out2 = OUT_DIR / f"mcq_{tag}_hanwen2modern_{DISTRACTOR_STRATEGY}.jsonl"
    write_jsonl(m2h, out1)
    write_jsonl(h2m, out2)

    # ====== mixed50：各取一半，总题数仍然 = N_QUESTIONS ======
    # 如果 N_QUESTIONS 太大/为全量，这里也会跟着变很大；建议保持 N_QUESTIONS 有限
    half = min(len(m2h), len(h2m)) // 2
    mixed = m2h[:half] + h2m[:half]
    rng.shuffle(mixed)
    out3 = OUT_DIR / f"mcq_{tag}_mixed50_{DISTRACTOR_STRATEGY}.jsonl"
    write_jsonl(mixed, out3)

    print("[OK] wrote:")
    print(" ", out1)
    print(" ", out2)
    print(" ", out3)
    print(f"counts: m2h={len(m2h)} h2m={len(h2m)} mixed50={len(mixed)}")

if __name__ == "__main__":
    main()
