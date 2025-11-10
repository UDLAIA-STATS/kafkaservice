# Dockerfile
FROM python:3.11-slim

# Evitar buffers en logs
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Dependencias del sistema (si necesitas librerías nativas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y código
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Variables de entorno por defecto (puedes sobrescribir en docker-compose)
ENV KAFKA_BOOTSTRAP=broker1:9092
ENV KAFKA_TOPIC=videos

# Si el contenedor es un service, espera a la entrada CMD
CMD ["python", "consumer.py"]
