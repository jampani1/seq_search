# ============================================
# Bioinformatics Hub - Backend Dockerfile
# ============================================
#
# Multi-stage build para imagem otimizada:
# - Stage 1: Instala dependências
# - Stage 2: Imagem final mínima
#
# Build: docker build -t biohub-backend .
# Run:   docker run -p 8000:8000 biohub-backend

# ============================================
# STAGE 1: Builder
# ============================================
FROM python:3.11-slim as builder

# Variáveis de ambiente para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# STAGE 2: Runtime
# ============================================
FROM python:3.11-slim as runtime

# Labels
LABEL maintainer="Mauricio Jampani <mjampani@usp.br>"
LABEL description="Bioinformatics Hub - Backend API"
LABEL version="0.1.0"

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Diretório da aplicação
    APP_HOME=/app

WORKDIR $APP_HOME

# Instalar dependências de runtime + ferramentas bioinformáticas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    # BLAST+ suite
    ncbi-blast+ \
    # Ferramentas auxiliares
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Instalar DIAMOND (mais rápido que BLASTP para grandes bancos)
# Versão 2.1.8 (última estável)
RUN wget -q https://github.com/bbuchfink/diamond/releases/download/v2.1.8/diamond-linux64.tar.gz \
    && tar xzf diamond-linux64.tar.gz \
    && mv diamond /usr/local/bin/ \
    && rm diamond-linux64.tar.gz \
    && chmod +x /usr/local/bin/diamond

# Copiar dependências instaladas do builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Criar usuário não-root (segurança)
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --gid 1001 appuser

# Criar diretórios necessários
RUN mkdir -p /app/uploads /app/results \
    && chown -R appuser:appgroup /app

# Copiar código da aplicação
COPY --chown=appuser:appgroup . .

# Trocar para usuário não-root
USER appuser

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Comando padrão
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
