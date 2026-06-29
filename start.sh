#!/bin/bash
# HuggingFace Spaces runs this as the entrypoint

# Start FastAPI on port 7861 in background, capture all output
uvicorn api.main:app --host 0.0.0.0 --port 7861 > /tmp/fastapi.log 2>&1 &

# Give it a moment, then print whatever it logged so far (visible in HF Spaces logs)
sleep 8
echo "===== FastAPI startup log ====="
cat /tmp/fastapi.log
echo "================================"

# Start Gradio on port 7860 (HF default) in foreground
python app.py
