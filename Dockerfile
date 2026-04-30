FROM python:3.11-slim

# éviter les logs inutiles
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# installer dépendances système
RUN apt-get update && apt-get install -y gcc

# copier requirements
COPY requirements.txt .

# installer dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
     pip install --no-cache-dir -r requirements.txt

# copier le projet
COPY . .

# collect static
RUN python manage.py collectstatic --noinput

# lancer l'app
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]