#!/usr/bin/env bash
set -e

echo "🔧 PERFECT-AGENT demo stack bootstrap"

if [ ! -f .env ]; then
  echo "⚠️ .env not found, copying from .env.example"
  cp .env.example .env
fi

python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -e . fastapi uvicorn gradio httpx pytest

echo "✅ Local env ready."

echo "🚀 Starting Docker Compose demo stack (API + UI)..."
docker compose up -d

echo
echo "API: http://localhost:${API_PORT:-8000}"
echo "UI : http://localhost:${UI_PORT:-7860}"
echo "✅ Demo stack is up."
