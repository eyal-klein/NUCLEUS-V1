FROM python:3.11-slim
WORKDIR /app
COPY backend/shared /app/backend/shared
COPY backend/services/wellness-dashboard /app/backend/services/wellness-dashboard
RUN pip install --no-cache-dir -r /app/backend/services/wellness-dashboard/requirements.txt
WORKDIR /app/backend/services/wellness-dashboard
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
