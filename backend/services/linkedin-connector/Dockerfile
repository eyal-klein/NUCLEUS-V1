FROM python:3.11-slim

WORKDIR /app

# Copy service files
COPY backend/services/linkedin-connector /app/backend/services/linkedin-connector

# Install dependencies
RUN pip install --no-cache-dir -r /app/backend/services/linkedin-connector/requirements.txt

# Set working directory to service
WORKDIR /app/backend/services/linkedin-connector

# Expose port
EXPOSE 8080

# Run the service
CMD ["python", "main.py"]
