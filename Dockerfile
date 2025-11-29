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

# Install patchright Chrome browser and system dependencies
RUN patchright install chromium && patchright install-deps chromium

# Copy application code
COPY m3u8_dl/ ./m3u8_dl/

# Create downloads directory
RUN mkdir -p /app/downloads

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV VERBOSE=true
ENV PYTHONPATH=/app

# Default volume for downloads
VOLUME ["/app/downloads"]

# Expose server port
EXPOSE 8000

# Entry point
ENTRYPOINT ["python"]

# Default command runs the server
CMD ["-m", "m3u8_dl.server"]
