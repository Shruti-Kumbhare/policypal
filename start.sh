#!/bin/bash
# HuggingFace Spaces runs this as the entrypoint

# Start FastAPI on port 7861 in background
uvicorn api.main:app --host 0.0.0.0 --port 7861 &

# Start Gradio on port 7860 (HF default) in foreground
python app.py
