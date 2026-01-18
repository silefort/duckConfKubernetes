FROM python:3.11-slim

WORKDIR /app

# Copier requirements et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Le reste des fichiers sera monté via volume

CMD ["python3", "app_controller.py"]
