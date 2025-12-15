FROM python:3.11-slim

WORKDIR /app

# Copy shared modules
COPY backend/shared /app/backend/shared

# Copy service files
COPY backend/services/health-wellness-engine /app/backend/services/health-wellness-engine

# Install dependencies
RUN pip install --no-cache-dir -r /app/backend/services/health-wellness-engine/requirements.txt

# Set working directory to service
WORKDIR /app/backend/services/health-wellness-engine

# Expose port
EXPOSE 8080

# Run the service
CMD ["python", "main.py"]
