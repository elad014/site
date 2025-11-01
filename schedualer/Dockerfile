# Use Python 3.8 slim image as base
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY schedualer/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the db module and utils (dependencies)
COPY db/ /app/db/

COPY utils/ /app/utils/

# Copy the scheduler code
COPY schedualer/ /app/

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash scheduler && \
    chown -R scheduler:scheduler /app
USER scheduler

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Command to run the scheduler
CMD ["python", "scheduler.py"]

