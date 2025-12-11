# Intelligent Agent Factory Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared models and dependencies
COPY backend/shared /app/shared

# Copy service files
COPY backend/services/intelligent-agent-factory /app/service

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9 \
    openai==1.54.3 \
    pydantic==2.5.2

# Set working directory to service
WORKDIR /app/service

# Expose port
EXPOSE 8080

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
