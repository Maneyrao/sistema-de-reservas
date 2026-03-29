# ============================================================
# Dockerfile — Backend FastAPI
# ============================================================
# Multi-stage: builder instala deps, runner es imagen mínima.

FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# ============================================================
# Stage final — imagen mínima de producción
# ============================================================
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copiar dependencias instaladas del stage builder
COPY --from=builder /root/.local /root/.local

# Copiar código fuente (excluye lo que está en .dockerignore)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
