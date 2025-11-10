# Usa una imagen base de Python
FROM python:3.11-slim

# Instala dependencias del sistema necesarias para LZ4 y otras librerías
RUN apt-get update && apt-get install -y \
    gcc \
    liblz4-dev \
    && rm -rf /var/lib/apt/lists/*

# Crea el directorio de trabajo
WORKDIR /app

# Copia los archivos de la aplicación
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Asegúrate de incluir lz4 en tus dependencias de Python
RUN pip install --no-cache-dir lz4 aiokafka

# Copia el resto del código
COPY . .

# Expone el puerto de FastAPI
EXPOSE 8000

# Comando para ejecutar FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
