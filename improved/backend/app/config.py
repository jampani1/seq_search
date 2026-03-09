"""
Configurações da Aplicação
==========================

DECISÕES TÉCNICAS:
------------------
1. pydantic-settings para gerenciar configurações:
   - Lê automaticamente de variáveis de ambiente
   - Lê de arquivo .env
   - Validação de tipos automática
   - Valores default para desenvolvimento

2. Separação de configurações por ambiente:
   - Desenvolvimento: DEBUG=True, DBs locais
   - Produção: DEBUG=False, DBs em cloud

3. Secrets NUNCA devem estar no código:
   - Use .env (não commitado) ou variáveis de ambiente
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações globais da aplicação.

    Todas as configurações podem ser sobrescritas por variáveis de ambiente.
    Exemplo: DATABASE_URL pode ser definida no sistema ou no .env
    """

    # ========================================
    # GERAL
    # ========================================

    APP_NAME: str = "Bioinformatics Hub"
    DEBUG: bool = True  # False em produção!
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-use-openssl-rand-hex-32"

    # ========================================
    # DATABASE - PostgreSQL
    # ========================================
    # Formato: postgresql+asyncpg://user:password@host:port/database
    # asyncpg é o driver async mais rápido para PostgreSQL

    DATABASE_URL: str = "postgresql+asyncpg://biohub:biohub123@localhost:5432/biohub"

    # Pool de conexões
    # - min: conexões mínimas mantidas abertas
    # - max: conexões máximas permitidas
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # ========================================
    # REDIS - Cache e Filas
    # ========================================
    # Usado para: cache de resultados, fila de jobs (Celery)

    REDIS_URL: str = "redis://localhost:6379/0"

    # ========================================
    # NEO4J - Banco de Grafos (GRN)
    # ========================================
    # Para armazenar e consultar Gene Regulatory Networks

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "biohub123"

    # ========================================
    # CORS - Origens Permitidas
    # ========================================
    # Lista de URLs que podem acessar a API
    # Em produção: apenas o domínio do frontend

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",      # React dev server
        "http://localhost:5173",      # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "null",                        # file:// URLs (local HTML)
        "*",                           # Allow all for development
    ]

    # ========================================
    # EXTERNAL APIS
    # ========================================
    # APIs externas de bioinformática

    # NCBI - para BLAST remoto e Entrez
    NCBI_API_KEY: str = ""  # Opcional, aumenta rate limit de 3 para 10 req/s
    NCBI_EMAIL: str = ""    # Obrigatório para Entrez

    # UniProt
    UNIPROT_BASE_URL: str = "https://rest.uniprot.org"

    # ========================================
    # FILE STORAGE
    # ========================================
    # Onde armazenar arquivos enviados e resultados

    UPLOAD_DIR: str = "./uploads"
    RESULTS_DIR: str = "./results"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100 MB

    # ========================================
    # CELERY - Task Queue
    # ========================================
    # Para tarefas demoradas (BLAST, pipelines, etc.)

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ========================================
    # CONFIGURAÇÃO DO PYDANTIC-SETTINGS
    # ========================================

    model_config = SettingsConfigDict(
        env_file=".env",           # Lê do arquivo .env
        env_file_encoding="utf-8",
        case_sensitive=True,        # DATABASE_URL != database_url
        extra="ignore",             # Ignora variáveis extras no .env
    )


# Instância global de settings
# Importar como: from app.config import settings
settings = Settings()
