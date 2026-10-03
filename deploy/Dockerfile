FROM node:22-alpine AS frontend
WORKDIR /web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STATIC_DIR=/app/static \
    PORT=10000
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY api/requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt
COPY --chown=app:app api/app ./app
COPY --chown=app:app api/migrations ./migrations
COPY --chown=app:app api/scripts ./scripts
COPY --chown=app:app api/alembic.ini ./
COPY --from=frontend --chown=app:app /web/dist ./static
COPY --chmod=755 deploy/start.sh ./start.sh
USER app
EXPOSE 10000
CMD ["./start.sh"]
