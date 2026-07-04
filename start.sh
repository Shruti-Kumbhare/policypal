#!/bin/bash

# Start FastAPI on port 7861 in background
uvicorn api.main:app --host 0.0.0.0 --port 7861 > /tmp/fastapi.log 2>&1 &

echo "===== FastAPI startup log ====="
cat /tmp/fastapi.log
echo "================================"

# Check if process is still running
if kill -0 $FASTAPI_PID 2>/dev/null; then
    echo "✅ FastAPI process is still running"
else
    echo "❌ FastAPI process has died"
fi

# Start Gradio
python app.py
2d966796-e701-4b2e-97f3-754f133c0a36


ck-BEPRSimdXk4ndjEYmh1cKhNYhgVjwVkSsnfra7PhK98B
chroma login --api-key ck-BEPRSimdXk4ndjEYmh1cKhNYhgVjwVkSsnfra7PhK98B