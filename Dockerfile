# Utiliser une image Python officielle comme base
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste des fichiers du projet
COPY . .

# Créer les répertoires de données s'ils n'existent pas
RUN mkdir -p data/raw data/processed

# Exposer le port sur lequel Streamlit s'exécute
EXPOSE 8501

# Définir les variables d'environnement
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Commande pour démarrer l'application avec make run
CMD ["make", "run"] 