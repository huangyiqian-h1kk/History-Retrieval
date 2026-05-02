import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple

import torch
from transformers import AutoTokenizer, AutoModel


# ===================== 配置（ =====================
MCQ_JSONL = Path("mcq_out/hard_0_10000.jsonl")  # 评测集
MODEL_NAME_OR_PATH = "SimCSE/outputs/Yuan_simptotrad_b32e3_to_b32e1_1gpu/checkpoint-24271"  
BATCH_SIZE = 64
MAX_LENGTH = 128            
POOLING = "cls"            
TOPK_LIST = [1, 2, 3]
DEVICE = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
# =================================================================


def load_mcq(path: Path) -> List[Dict[str, Any]]:
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


@torch.no_grad()
def encode_texts(
    texts: List[str],
    tokenizer: AutoTokenizer,
    model: AutoModel,
    batch_size: int,
    max_length: int,
    pooling: str,
    device: str,
) -> torch.Tensor:
    """
    返回 shape: [N, D] 的句向量（L2 normalize 后）
    """
    all_vecs = []
    model.eval()

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        inputs = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        outputs = model(**inputs)
        last_hidden = outputs.last_hidden_state  # [B, L, H]

        if pooling == "cls":
            vec = last_hidden[:, 0]  # [B, H]
        elif pooling == "mean":
            attn = inputs["attention_mask"].unsqueeze(-1)  # [B, L, 1]
            summed = (last_hidden * attn).sum(dim=1)
            denom = attn.sum(dim=1).clamp(min=1)
            vec = summed / denom
        else:
            raise ValueError("POOLING must be 'cls' or 'mean'")

        vec = torch.nn.functional.normalize(vec, p=2, dim=1)
        all_vecs.append(vec.detach().cpu())

    return torch.cat(all_vecs, dim=0)


def ranks_from_scores(scores: torch.Tensor, answer_index: int) -> int:
    """
    scores: [num_choices] 越大越相似
    返回正确答案的排名（1 表示第一名）
    """
    # argsort descending
    order = torch.argsort(scores, descending=True)
    # 找到 answer_index 在 order 中的位置
    rank0 = (order == answer_index).nonzero(as_tuple=False).item()
    return rank0 + 1


def evaluate_mcq(
    items: List[Dict[str, Any]],
    tokenizer: AutoTokenizer,
    model: AutoModel,
    batch_size: int,
    max_length: int,
    pooling: str,
    device: str,
    topk_list: List[int],
) -> Dict[str, float]:
    """
    逐题评测：
    - 对每题：encode(query) + encode(choices)
    - cosine similarity（因向量已 normalize，点积即 cosine）
    """
    topk_hits = {k: 0 for k in topk_list}
    mrr_sum = 0.0

    # 为了加速：先把所有 query 编码（一次性）
    queries = [it["query"] for it in items]
    q_vecs = encode_texts(queries, tokenizer, model, batch_size, max_length, pooling, device)

    # choices 不能一次性全编码（总量会很大），逐题做
    for idx, it in enumerate(items):
        choices = it["choices"]
        ans = int(it["answer_index"])

        c_vecs = encode_texts(choices, tokenizer, model, batch_size, max_length, pooling, device)
        qv = q_vecs[idx].unsqueeze(0)  # [1, D]

        # cosine similarity: [1,D] x [D,4] -> [4]
        scores = (qv @ c_vecs.T).squeeze(0)  # [num_choices]

        rank = ranks_from_scores(scores, ans)
        mrr_sum += 1.0 / rank

        for k in topk_list:
            if rank <= k:
                topk_hits[k] += 1

        if (idx + 1) % 200 == 0:
            print(f"progress: {idx+1}/{len(items)}")

    n = len(items)
    out = {f"Top@{k}": topk_hits[k] / n for k in topk_list}
    out["MRR"] = mrr_sum / n
    return out


def main():
    print(f"DEVICE={DEVICE}")
    print(f"MCQ={MCQ_JSONL}")
    print(f"MODEL={MODEL_NAME_OR_PATH}")
    print(f"POOLING={POOLING} MAX_LENGTH={MAX_LENGTH} BATCH_SIZE={BATCH_SIZE}")

    items = load_mcq(MCQ_JSONL)
    print(f"loaded_questions={len(items)}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME_OR_PATH, use_fast=True)
    model = AutoModel.from_pretrained(MODEL_NAME_OR_PATH)
    model.to(DEVICE)

    metrics = evaluate_mcq(
        items,
        tokenizer,
        model,
        batch_size=BATCH_SIZE,
        max_length=MAX_LENGTH,
        pooling=POOLING,
        device=DEVICE,
        topk_list=TOPK_LIST,
    )

    print("\n=== RESULTS ===")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}")


if __name__ == "__main__":
    main()
