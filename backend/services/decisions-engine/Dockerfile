# NUCLEUS V1.2 - Orchestrator Service Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared requirements
COPY backend/shared/requirements.txt /app/backend/shared/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/shared/requirements.txt

# Copy shared modules
COPY backend/shared /app/backend/shared

# Copy service code
COPY backend/services/decisions-engine /app/backend/services/decisions-engine

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Run the service
CMD ["python", "-m", "uvicorn", "backend.services.decisions-engine.main:app", "--host", "0.0.0.0", "--port", "8080"]
