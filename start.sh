#!/bin/bash

# Start FastAPI on port 7861 in background
uvicorn api.main:app --host 0.0.0.0 --port 7861 > /tmp/fastapi.log 2>&1 &
FASTAPI_PID=$!

# Start Gradio in background, logging to file
python app.py > /tmp/gradio.log 2>&1 &
GRADIO_PID=$!

# Wait then print startup logs
sleep 20
echo "===== FastAPI startup log ====="
cat /tmp/fastapi.log
echo "================================"

echo "===== Gradio startup log ====="
cat /tmp/gradio.log
echo "================================"

if kill -0 $FASTAPI_PID 2>/dev/null; then
    echo "✅ FastAPI running"
else
    echo "❌ FastAPI died"
fi

if kill -0 $GRADIO_PID 2>/dev/null; then
    echo "✅ Gradio running"
else
    echo "❌ Gradio died"
fi

# Continuously tail both logs so all runtime output is visible
tail -f /tmp/fastapi.log /tmp/gradio.log &

# Keep container alive
wait $GRADIO_PID