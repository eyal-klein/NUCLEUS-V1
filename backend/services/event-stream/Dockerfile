FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy shared dependencies
COPY backend/shared /app/backend/shared

# Copy service code
COPY backend/services/event-stream /app/backend/services/event-stream

# Install shared requirements first
RUN pip install --no-cache-dir -r /app/backend/shared/requirements.txt

# Install service-specific requirements
RUN pip install --no-cache-dir -r /app/backend/services/event-stream/requirements.txt

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Run the service
CMD ["python", "-m", "uvicorn", "backend.services.event-stream.main:app", "--host", "0.0.0.0", "--port", "8080"]
