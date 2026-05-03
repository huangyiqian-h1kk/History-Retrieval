CUDA_VISIBLE_DEVICES=0 python train.py \
  --model_name_or_path IEITYuan/Yuan-embedding-2.0-zh \
  --train_file /workspaces/que/workspaces/splits/train_trad_mix50.csv \
  --output_dir /workspaces/que/workspaces/SimCSE/outputs/Yuan_trad_b32_e3_1gpu \
  --do_train \
  --max_seq_length 128 \
  --pooler_type cls \
  --temp 0.05 \
  --learning_rate 3e-5 \
  --per_device_train_batch_size 32 \
  --bf16 \
  --logging_steps 20 \
  --save_steps 24271 \
  --save_total_limit 3 \
  --num_train_epochs 3 \
  --overwrite_output_dir

  CUDA_VISIBLE_DEVICES=1 python train.py \
  --model_name_or_path /workspaces/que/workspaces/SimCSE/outputs/checkpoint-48542_Yuan_pair_full_b32_e3_1gpu \
  --train_file /workspaces/que/workspaces/splits/train_trad_mix50.csv \
  --output_dir /workspaces/que/workspaces/SimCSE/outputs/Yuan_simptotrad_b32e3_to_b32e1_1gpu \
  --do_train \
  --max_seq_length 128 \
  --pooler_type cls \
  --temp 0.05 \
  --learning_rate 1e-5 \
  --per_device_train_batch_size 32 \
  --bf16 \
  --logging_steps 20 \
  --save_steps 24271 \
  --save_total_limit 3 \
  --num_train_epochs 1 \
  --overwrite_output_dir

TencentBAC/Conan-embedding-v1
IEITYuan/Yuan-embedding-2.0-zh
iampanda/zpoint_large_embedding_zh
richinfoai/ritrieve_zh_v1
lier007/xiaobu-embedding-v2
24271，12136, 6068

df -h
df -h /workspaces
df -i
du -sh /workspaces/que/workspaces/SimCSE/outputs/*


  python make_hard_mcq.py \
  --in_jsonl mcq_out/mcq_test_full_mixed50_easy.jsonl \
  --out_jsonl mcq_out/hard_00000_00020.jsonl \
  --model gpt-4o-mini \
  --start 0 \
  --end 20

IN="mcq_out/mcq_dev_mixed50_easy.jsonl" 
OUT_DIR="mcq_out"
mkdir -p "$OUT_DIR"

for s in $(seq 0 500 1500); do
  e=$((s+500))
  echo "== $s..$e =="
  PYTHONUNBUFFERED=1 python make_hard_mcq.py \
    --in_jsonl "$IN" \
    --out_jsonl "$OUT_DIR/hard_dev_${s}_${e}.jsonl" \
    --model gpt-4o-mini \
    --start "$s" --end "$e"
done

python build_method2_splitmix.py \
  --in_csv splits/train.csv \
  --out_csv splits/train_splitmix.csv \
  --min_total_len_for_split_hanwen 12 \
  --min_total_len_for_split_modern 18 \
  --min_seg_len 4



