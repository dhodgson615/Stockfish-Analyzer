# Dockerfile for Stockfish-Analyzer
# Provides a complete environment for running the chess analysis tool

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Stockfish
RUN apt-get update && apt-get install -y \
    stockfish \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Create directory for Syzygy tablebases (optional)
RUN mkdir -p /app/syzygy

# Set environment variables
ENV PYTHONPATH=/app
ENV STOCKFISH_PATH=/usr/games/stockfish

# Create a non-root user for security
RUN useradd -m -u 1000 chessuser && chown -R chessuser:chessuser /app
USER chessuser

# Expose volumes for configuration and tablebases
VOLUME ["/app/config", "/app/syzygy"]

# Default command runs the application with example config
CMD ["python3", "src/main.py", "--config", "config/example_config.json"]