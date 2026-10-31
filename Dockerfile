FROM node:24-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=production DB_PATH=/app/data/mood.sqlite
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && pip check && useradd --uid 10001 --create-home app
COPY app.py ./
COPY backend/ ./backend/
COPY models/ ./models/
COPY logic/ ./logic/
COPY scripts/ ./scripts/
COPY --from=frontend /build/dist/ ./frontend/dist/
RUN mkdir -p data && chown -R app:app /app
USER app
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=6s --start-period=15s CMD ["python","scripts/healthcheck.py"]
CMD ["gunicorn","--preload","--bind","0.0.0.0:5000","--workers","2","--threads","4","--worker-tmp-dir","/tmp","--timeout","30","--graceful-timeout","15","--access-logfile","-","app:create_app()"]
