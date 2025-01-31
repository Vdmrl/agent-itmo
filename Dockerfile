FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn main:app --workers 8 --worker-class uvicorn.workers.UvicornWorker --backlog 2048 --worker-connections 1000 --keep-alive 5 --timeout 300 --bind 0.0.0.0:8080
