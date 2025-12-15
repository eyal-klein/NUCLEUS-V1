FROM python:3.11-slim

WORKDIR /app

# Copy shared modules
COPY backend/shared /app/backend/shared

# Copy service files
COPY backend/services/calendar-connector /app/backend/services/calendar-connector

# Install dependencies
RUN pip install --no-cache-dir -r /app/backend/services/calendar-connector/requirements.txt

# Set working directory to service
WORKDIR /app/backend/services/calendar-connector

# Expose port (Cloud Run uses PORT env var)
EXPOSE 8080

# Run the service using python to properly read PORT env var
CMD ["python", "main.py"]
