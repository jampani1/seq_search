"""
Bioinformatics Hub - Main Application
=====================================

Este é o ponto de entrada da aplicação FastAPI.

DECISÕES TÉCNICAS:
------------------
1. FastAPI foi escolhido por:
   - Suporte nativo a async/await (importante para I/O como BLAST, APIs externas)
   - Documentação automática (Swagger UI em /docs, ReDoc em /redoc)
   - Validação automática com Pydantic
   - Performance comparável a Node.js e Go

2. CORS habilitado para desenvolvimento local (frontend em porta diferente)

3. Lifespan events para gerenciar conexões de banco de dados
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import init_db, close_db
from app.api.v1 import router as api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.

    - startup: Inicializa conexões (DB, Redis, etc.)
    - shutdown: Fecha conexões de forma limpa

    NOTA: Usamos 'lifespan' ao invés de @app.on_event (deprecated no FastAPI 0.109+)
    """
    # Startup
    print("[*] Iniciando Bioinformatics Hub...")
    await init_db()
    print("[OK] Banco de dados conectado")

    yield  # Aplicação rodando

    # Shutdown
    print("[*] Encerrando conexoes...")
    await close_db()
    print("[OK] Bioinformatics Hub encerrado")


# Criação da aplicação FastAPI
app = FastAPI(
    title="Bioinformatics Hub",
    description="""
    **Plataforma de Bioinformatica para Cientistas**

    ## Funcionalidades

    * **Sequências** - Upload e gerenciamento de sequências DNA/Proteína
    * **Anotação** - Pipelines automatizados por tipo de organismo
    * **Efetores** - Predição de proteínas efetoras (pipeline Predector)
    * **Redes Gênicas** - Inferência e visualização de GRN
    * **Estruturas** - Integração com AlphaFold/ESMFold

    ## Autenticação

    Em desenvolvimento - atualmente sem autenticação para facilitar testes.
    """,
    version="0.1.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc (documentação alternativa)
    lifespan=lifespan,
)


# Configuração de CORS
# --------------------
# CORS (Cross-Origin Resource Sharing) permite que o frontend (React)
# em localhost:3000 acesse o backend em localhost:8000
#
# Em produção, restringir origins para o domínio real!

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Lista de origens permitidas
    allow_credentials=True,                # Permite cookies/auth headers
    allow_methods=["*"],                   # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],                   # Todos os headers
)


# Rotas da API
# ------------
# Prefixo /api/v1 para versionamento da API
# Isso permite criar /api/v2 no futuro sem quebrar clientes existentes

app.include_router(api_v1_router, prefix="/api/v1")


# Health Check
# ------------
# Endpoint simples para verificar se a aplicação está rodando
# Útil para: Docker health checks, load balancers, monitoring

@app.get("/health", tags=["System"])
async def health_check():
    """
    Verifica se a aplicação está funcionando.

    Retorna:
        - status: "healthy" se tudo OK
        - version: versão atual da API
        - database: status da conexão com DB
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "database": "connected",  # TODO: verificar conexão real
        "message": "Bioinformatics Hub esta rodando!"
    }


@app.get("/", tags=["System"])
async def root():
    """
    Rota raiz - redireciona para documentação.
    """
    return {
        "message": "Bem-vindo ao Bioinformatics Hub!",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1"
    }
