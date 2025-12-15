FROM python:3.11-slim

WORKDIR /app

# Copy shared modules
COPY backend/shared /app/backend/shared

# Copy service files
COPY backend/services/briefing-agent /app/backend/services/briefing-agent

# Install dependencies
RUN pip install --no-cache-dir -r /app/backend/services/briefing-agent/requirements.txt

# Set working directory to service
WORKDIR /app/backend/services/briefing-agent

# Expose port
EXPOSE 8080

# Run the service
CMD ["python", "main.py"]
