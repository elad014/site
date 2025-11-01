# Use Python 3.8 slim image as base
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY stocks_data_collector/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the config module (dependency)
COPY stocks_data_collector/config.py /app/config.py

# Copy the stock data collector code
COPY stocks_data_collector/stock_data_collector_service.py /app/stock_data_collector_service.py

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash stockapi && \
    chown -R stockapi:stockapi /app
USER stockapi

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port 5000 (as per docker-compose)
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Command to run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "30", "stock_data_collector_service:app"]

