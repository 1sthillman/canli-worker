FROM python:3.11-slim

WORKDIR /app

# Bağımlılıkları kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulamayı kopyala
COPY worker.py .

# Çalışma komutu
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--worker-class", "gthread", "--threads", "4", "worker:app"]
