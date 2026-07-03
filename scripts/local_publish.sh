#!/usr/bin/env bash
set -euo pipefail

ARTICLE_PATH="${1:-content/daily/2026-07-03-daily-briefing.md}"
VENV_DIR="${VENV_DIR:-.venv}"

cd "$(dirname "$0")/.."

echo "==> Pull latest code"
git pull

echo "==> Create Python virtual environment"
python3 -m venv "$VENV_DIR"

if [ -f "$VENV_DIR/bin/activate" ]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
else
  echo "Virtual environment activation failed: $VENV_DIR/bin/activate not found"
  exit 1
fi

echo "==> Install dependencies"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "==> Generate missing PNG article images"
python scripts/generate_article_images.py "$ARTICLE_PATH"

if ! git diff --quiet -- assets/images content/daily; then
  echo "==> Commit generated images and markdown updates"
  git add assets/images content/daily
  git commit -m "Prepare daily briefing assets"
  git push
else
  echo "==> No image or markdown changes to commit"
fi

echo "==> Upload WeChat materials and create draft"
python scripts/push_wechat_draft.py "$ARTICLE_PATH"

echo "==> Done"
