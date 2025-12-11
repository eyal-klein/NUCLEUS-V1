FROM python:3.11-slim
WORKDIR /app
COPY backend/shared /app/backend/shared
COPY backend/services/realtime-health-monitor /app/backend/services/realtime-health-monitor
RUN pip install --no-cache-dir -r /app/backend/services/realtime-health-monitor/requirements.txt
WORKDIR /app/backend/services/realtime-health-monitor
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
