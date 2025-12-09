FROM python:3.11-slim

WORKDIR /app

# Copy shared libraries
COPY backend/shared /app/backend/shared

# Copy job code
COPY backend/jobs/research-engine /app/backend/jobs/research-engine

# Install dependencies
RUN pip install --no-cache-dir -r /app/backend/shared/requirements.txt

# Set environment
ENV PYTHONUNBUFFERED=1

# Run job
CMD ["python", "/app/backend/jobs/research-engine/main.py"]
