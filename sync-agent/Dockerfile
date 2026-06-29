# ============================================================
# Dockerfile — Sync Agent (FastAPI + Oracle Thick Mode)
# Multi-stage; reaproveita o padrão do app Streamlit (Instant Client 19.24).
# ============================================================

# ------------------------------------------------------------
# Stage 1: builder — baixa e extrai o Oracle Instant Client
# ------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends unzip wget ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ARG ORACLE_CLIENT_URL=https://download.oracle.com/otn_software/linux/instantclient/1924000/instantclient-basiclite-linux.x64-19.24.0.0.0dbru.zip
RUN mkdir -p /opt/oracle && \
    wget -q -O /tmp/instantclient.zip "${ORACLE_CLIENT_URL}" && \
    unzip -q /tmp/instantclient.zip -d /opt/oracle && \
    mv /opt/oracle/instantclient_* /opt/oracle/instantclient && \
    rm /tmp/instantclient.zip

# ------------------------------------------------------------
# Stage 2: runtime — imagem final enxuta
# ------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=America/Sao_Paulo \
    ORACLE_CLIENT_DIR=/opt/oracle/instantclient \
    LD_LIBRARY_PATH=/opt/oracle/instantclient

# libaio (runtime do Oracle Client) + tzdata (fuso de Brasília)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libaio1 tzdata && \
    ln -sf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && \
    echo "America/Sao_Paulo" > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/oracle /opt/oracle

# Bookworm usa libaio.so.1t64; o Oracle Client procura por libaio.so.1
RUN ln -sf /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /opt/oracle/instantclient/libaio.so.1 2>/dev/null || true

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
