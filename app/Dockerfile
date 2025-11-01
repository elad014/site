# Use Python 3.8 slim image as base
FROM python:3.11-slim
# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the db module (dependency)
COPY db/ /app/db/

COPY utils/ /app/utils/

COPY ollama_services/ /app/ollama_services/

# Copy the application code
COPY app/ /app/

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash webapp && \
    chown -R webapp:webapp /app
USER webapp

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port 8080 (different from stock service on 5000)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Command to run the application with Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "run:app"]

