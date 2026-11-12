FROM python:3.12-slim

# FFmpeg 是视频合成核心依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg fonts-noto-cjk && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 8501

CMD ["python", "run.py"]
