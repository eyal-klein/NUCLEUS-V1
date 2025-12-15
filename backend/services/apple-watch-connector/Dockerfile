FROM python:3.11-slim
WORKDIR /app
COPY backend/shared /app/backend/shared
COPY backend/services/apple-watch-connector /app/backend/services/apple-watch-connector
RUN pip install --no-cache-dir -r /app/backend/services/apple-watch-connector/requirements.txt
WORKDIR /app/backend/services/apple-watch-connector
EXPOSE 8080
CMD ["python", "main.py"]
