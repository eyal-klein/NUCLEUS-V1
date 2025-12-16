# NUCLEUS V2.0 - Agent Health Monitor Service
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared requirements
COPY backend/shared/requirements.txt /app/backend/shared/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/shared/requirements.txt

# Copy shared code
COPY backend/shared /app/backend/shared

# Copy service code
COPY backend/services/agent-health-monitor /app/backend/services/agent-health-monitor

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Run service
CMD ["python", "-m", "uvicorn", "backend.services.agent-health-monitor.main:app", "--host", "0.0.0.0", "--port", "8080"]
