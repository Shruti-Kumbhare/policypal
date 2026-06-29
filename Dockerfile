FROM python:3.13-slim

WORKDIR /app

# Install system dependencies if needed (curl for healthchecks, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

EXPOSE 7860

CMD ["bash", "start.sh"]
