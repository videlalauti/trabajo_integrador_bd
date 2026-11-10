
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN useradd --system --uid 10001 --create-home apiuser

USER apiuser

EXPOSE 8000

# PORT: lo asigna el proveedor (Render usa 10000 por defecto); 8000 en local.
# --workers 1: cada proceso abre su propio pool; un solo proceso mantiene el
# total de conexiones en DB_POOL_MAX aunque el proveedor defina WEB_CONCURRENCY.
# Encabezados X-Forwarded-*: se usa el valor por defecto de uvicorn (solo se
# confía en 127.0.0.1). La API no depende de la IP ni del esquema del cliente;
# no se confía en encabezados reenviados desde cualquier origen.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
