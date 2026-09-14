FROM python:3.11-slim

# Install system-level audio dependencies for Discord voice
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libopus0 \
    libopus-dev \
    libffi-dev \
    libsodium-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and data
COPY . .

# Expose the health check port (Render sets PORT env var)
EXPOSE 10000

CMD ["python", "daily_scholarly_bot.py"]
