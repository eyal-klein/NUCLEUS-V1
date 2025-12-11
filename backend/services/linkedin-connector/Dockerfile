FROM python:3.11-slim

WORKDIR /app

# Copy service files
COPY backend/services/linkedin-connector /app/backend/services/linkedin-connector

# Install dependencies
RUN pip install --no-cache-dir -r /app/backend/services/linkedin-connector/requirements.txt

# Set working directory to service
WORKDIR /app/backend/services/linkedin-connector

# Expose port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
