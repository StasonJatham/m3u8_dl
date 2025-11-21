# HLS Stream Downloader - Docker Image
# Pre-configured environment with all dependencies

FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install patchright Chrome browser
RUN patchright install chrome

# Copy application code
COPY m3u8_dl/ ./m3u8_dl/
COPY main.py .

# Create downloads directory
RUN mkdir -p /app/downloads

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV VERBOSE=true

# Default volume for downloads
VOLUME ["/app/downloads"]

# Set default working directory for downloads
WORKDIR /app/downloads

# Entry point
ENTRYPOINT ["python", "-m", "m3u8_dl"]

# Default command (can be overridden)
CMD ["--help"]
