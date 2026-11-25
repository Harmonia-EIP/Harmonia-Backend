FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Utilisateur sans privilèges pour faire tourner l'API
RUN useradd --create-home --uid 1000 app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=app:app . .
RUN chmod +x entrypoint.sh && mkdir -p uploads && chown app:app uploads

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)" || exit 1

# L'entrypoint démarre en root uniquement pour corriger les droits du volume
# d'uploads, puis lance tout le reste en tant que "app".
CMD ["./entrypoint.sh"]
