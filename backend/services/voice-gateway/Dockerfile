# NUCLEUS Voice Gateway Service
# Dockerfile for containerized deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY ../../shared /app/backend/shared

# Copy service code
COPY . /app/backend/services/voice-gateway

# Set Python path to include shared modules
ENV PYTHONPATH="/app/backend:/app/backend/services/voice-gateway:${PYTHONPATH}"

# Set working directory to service
WORKDIR /app/backend/services/voice-gateway

# Expose port
EXPOSE 8090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
