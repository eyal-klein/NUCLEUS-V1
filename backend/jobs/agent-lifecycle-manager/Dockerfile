# Agent Lifecycle Manager Job Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared models and dependencies
COPY backend/shared /app/shared

# Copy job files
COPY backend/jobs/agent-lifecycle-manager /app/job

# Install Python dependencies
RUN pip install --no-cache-dir \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9 \
    openai==1.54.3 \
    pydantic==2.5.2

# Set working directory to job
WORKDIR /app/job

# Run the job
CMD ["python", "main.py"]
