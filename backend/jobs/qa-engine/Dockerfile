FROM python:3.11-slim

WORKDIR /app

# Copy shared libraries
COPY backend/shared /app/backend/shared

# Copy job code
COPY backend/jobs/qa-engine /app/backend/jobs/qa-engine

# Install dependencies
# Install system dependencies for pgvector
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /app/backend/shared/requirements.txt

# Set environment
ENV PYTHONUNBUFFERED=1

# Run job
CMD ["python", "/app/backend/jobs/qa-engine/main.py"]
