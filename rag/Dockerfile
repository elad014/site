FROM python:3.11-slim
# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for PDFs and cache
RUN mkdir -p /app/pdf_storage /app/.cache

# Expose port
EXPOSE 5002

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/.cache
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache

# Pre-download model will happen on first run (~30 seconds)
# Model will be cached in volume for subsequent runs

# Run the Flask application
CMD ["python", "rag_app.py"]

