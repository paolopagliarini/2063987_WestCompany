# Dockerfile
FROM python:3.12-slim

WORKDIR /backend

# Si aggiorna la lista dei pacchetti e si installano le dipendenze necessarie.
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Si installano le dipendenze Python specificate nel file "requirements.txt".
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Si copiano i file nel container.
COPY src/ .

# Aggiorna il PYTHONPATH.
ENV PYTHONPATH=/backend

# Si avvia l'applicazione utilizzando uvicorn.
CMD ["python", "notification-service.py"]