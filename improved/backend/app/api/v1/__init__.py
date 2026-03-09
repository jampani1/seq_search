"""
API v1 Router
=============

Agrupa todos os endpoints da versão 1 da API.

DECISÃO TÉCNICA:
----------------
Versionamento de API permite:
- Manter compatibilidade com clientes antigos
- Evoluir a API sem quebrar integrações
- Depreciar versões antigas gradualmente

Estrutura:
- /api/v1/sequences - CRUD de sequências
- /api/v1/annotation - Pipelines de anotação
- /api/v1/effectors - Predição de efetores
- /api/v1/blast - Buscas BLAST/DIAMOND
- /api/v1/grn - Redes gênicas
- /api/v1/structures - Estruturas de proteínas
"""

from fastapi import APIRouter

from app.api.v1 import sequences, blast, effectors, grn

# Criar router principal da v1
router = APIRouter()


# Placeholder para health check da API
@router.get("/")
async def api_v1_root():
    """
    Root da API v1 - informações básicas.
    """
    return {
        "api_version": "v1",
        "status": "operational",
        "endpoints": {
            "sequences": "/api/v1/sequences - CRUD completo",
            "blast": "/api/v1/blast - BLAST/DIAMOND",
            "effectors": "/api/v1/effectors - Predição de efetores",
            "grn": "/api/v1/grn - Gene Regulatory Networks",
            "structures": "/api/v1/structures (em desenvolvimento)",
        }
    }


# Incluir routers específicos
router.include_router(
    sequences.router,
    prefix="/sequences",
    tags=["Sequences"]
)

router.include_router(
    blast.router,
    prefix="/blast",
    tags=["BLAST"]
)

router.include_router(
    effectors.router,
    prefix="/effectors",
    tags=["Effectors"]
)

router.include_router(
    grn.router,
    prefix="/grn",
    tags=["Gene Regulatory Networks"]
)
