# NUCLEUS V2.0 - Master Prompt Engine Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Copy shared requirements and install
COPY backend/shared/requirements.txt /app/backend/shared/requirements.txt
# Install system dependencies for pgvector
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /app/backend/shared/requirements.txt

# Copy shared code
COPY backend/shared /app/backend/shared

# Copy job code
COPY backend/jobs/master-prompt-engine /app/backend/jobs/master-prompt-engine

# Set Python path
ENV PYTHONPATH=/app

# Run the job
CMD ["python", "/app/backend/jobs/master-prompt-engine/main.py"]
