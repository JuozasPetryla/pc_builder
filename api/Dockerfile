FROM python:3.13-slim AS dependencies

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app \
    && adduser --system --ingroup app app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt

FROM dependencies AS test-dependencies

RUN pip install --no-cache-dir --requirement requirements-dev.txt

FROM test-dependencies AS test

COPY --chown=app:app . .

USER app

CMD ["pytest", "-q"]

FROM dependencies AS runtime

COPY --chown=app:app . .

USER app

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
