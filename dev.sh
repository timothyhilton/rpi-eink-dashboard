#!/usr/bin/env bash
set -euo pipefail

rsync -av --delete \
  --exclude .git \
  --exclude .venv \
  --exclude venv \
  --exclude __pycache__ \
  --exclude '*.pyc' \
  "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/" \
  "tim@$1:~/project/rpi-eink-dashboard/"

# ssh tim@$1 "pkill -f 'python.*main\.py'"
ssh "tim@$1" "cd ~/project/rpi-eink-dashboard && . venv/bin/activate && python main.py"