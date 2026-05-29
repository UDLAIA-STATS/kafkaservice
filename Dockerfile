FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libpq-dev gcc bash netcat-traditional \
 && pip install --no-cache-dir -r /app/requirements.txt \
 && apt-get purge -y gcc \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

COPY . /app

# mismo puerto que usa el compose
EXPOSE 8060

CMD ["python", "manage.py", "runserver", "0.0.0.0:8060"]