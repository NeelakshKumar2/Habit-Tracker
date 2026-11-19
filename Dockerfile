FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 GRIT_ENV=production GRIT_DB=/data/grit.db PORT=8000
RUN useradd --create-home --uid 10001 grit && mkdir /data && chown grit /data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=grit server ./server
COPY --chown=grit web ./web
COPY --chown=grit deploy ./deploy
COPY --chown=grit tools ./tools
COPY --chown=grit wsgi.py .
USER grit
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:%s/api/ready'%os.getenv('PORT','8000'),timeout=2)"
CMD ["gunicorn", "-c", "deploy/gunicorn.conf.py", "wsgi:app"]
