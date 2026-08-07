FROM python:3.10-slim

# Install system dependencies (ffmpeg required for yt-dlp clipping)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose Render's standard port
EXPOSE 10000

# Standard execution
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
