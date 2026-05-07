#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <pi-ip-or-hostname>"
  echo "Example: $0 192.168.1.123"
  exit 1
fi

PI_HOST="tim@$1"
PI_APP_DIR="${PI_APP_DIR:-~/project/rpi-eink-dashboard}"
LOCAL_APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

rsync -av --delete \
  --exclude .git \
  --exclude .venv \
  --exclude venv \
  --exclude __pycache__ \
  --exclude '*.pyc' \
  "$LOCAL_APP_DIR/" \
  "$PI_HOST:$PI_APP_DIR/"

ssh "$PI_HOST" "cd $PI_APP_DIR && . venv/bin/activate && python main.py"
