#!/usr/bin/env bash
export CUDA_VISIBLE_DEVICES="${LOCAL_RANK}"
exec /usr/bin/python train.py "$@"
