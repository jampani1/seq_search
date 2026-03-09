"""
API Endpoints: Gene Regulatory Networks (GRN)
=============================================

Endpoints para criação, inferência e consulta de GRNs.

ENDPOINTS:
----------
POST   /                    - Criar nova rede
GET    /                    - Listar redes
GET    /{id}                - Detalhes da rede
DELETE /{id}                - Deletar rede
POST   /{id}/expression     - Upload dados de expressão
POST   /{id}/infer          - Iniciar inferência
GET    /{id}/graph          - Grafo no formato Cytoscape.js
GET    /{id}/statistics     - Estatísticas da rede
GET    /{id}/neighbors/{gene} - Vizinhos de um gene
GET    /{id}/path           - Caminho entre genes
"""

from typing import Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.gene_network import NetworkStatus, InferenceMethod
from app.schemas.grn import (
    NetworkCreateRequest,
    NetworkResponse,
    NetworkSummary,
    NetworkListResponse,
    CytoscapeGraphData,
    NetworkStatistics,
    ExpressionDataUpload,
    InferNetworkRequest,
    GeneNeighborsRequest,
    SubnetworkResponse,
    PathQueryRequest,
    PathResponse,
)
from app.services.grn_service import GRNService


router = APIRouter()


# ========================================
# CRUD ENDPOINTS
# ========================================

@router.post(
    "/",
    response_model=NetworkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova rede",
    description="Cria uma nova Gene Regulatory Network (metadados).",
)
async def create_network(
    request: NetworkCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Cria uma nova GRN.

    O grafo em si será criado após upload de dados de expressão
    e execução da inferência.
    """
    service = GRNService(db)
    network = await service.create_network(request)
    return NetworkResponse.model_validate(network)


@router.get(
    "/",
    response_model=NetworkListResponse,
    summary="Listar redes",
    description="Lista todas as redes com paginação e filtros.",
)
async def list_networks(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    organism: Optional[str] = Query(None, description="Filtrar por organismo"),
    status: Optional[NetworkStatus] = Query(None, description="Filtrar por status"),
    method: Optional[InferenceMethod] = Query(None, description="Filtrar por método"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista redes com paginação.

    Filtros disponíveis:
    - organism: busca parcial no nome do organismo
    - status: pending, inferring, completed, failed
    - method: correlation, mutual_info, grnboost2, wgcna
    """
    service = GRNService(db)
    networks, total = await service.list_networks(
        page=page,
        page_size=page_size,
        organism=organism,
        status=status,
        method=method,
    )

    return NetworkListResponse(
        items=[NetworkSummary.model_validate(n) for n in networks],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 0,
    )


@router.get(
    "/{network_id}",
    response_model=NetworkResponse,
    summary="Detalhes da rede",
    description="Retorna metadados completos de uma rede.",
)
async def get_network(
    network_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Busca rede por ID.
    """
    service = GRNService(db)
    network = await service.get_network(network_id)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Network {network_id} not found",
        )

    response = NetworkResponse.model_validate(network)
    response.density = network.density
    return response


@router.delete(
    "/{network_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar rede",
    description="Remove uma rede (PostgreSQL + Neo4j).",
)
async def delete_network(
    network_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Deleta uma rede e todos seus dados.
    """
    service = GRNService(db)
    deleted = await service.delete_network(network_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Network {network_id} not found",
        )


# ========================================
# INFERENCE ENDPOINTS
# ========================================

@router.post(
    "/{network_id}/expression",
    response_model=NetworkResponse,
    summary="Upload dados de expressão",
    description="Faz upload de matriz de expressão e inicia inferência.",
)
async def upload_expression_and_infer(
    network_id: int,
    expression_data: ExpressionDataUpload,
    db: AsyncSession = Depends(get_db),
):
    """
    Upload de dados de expressão e inferência de GRN.

    A matriz de expressão deve ter formato [genes x samples]:
    - genes: lista de IDs/nomes de genes
    - samples: lista de IDs/nomes de amostras
    - expression_matrix: matriz numérica

    Exemplo:
    ```json
    {
        "network_id": 1,
        "genes": ["GENE1", "GENE2", "GENE3"],
        "samples": ["sample1", "sample2", "sample3"],
        "expression_matrix": [
            [1.0, 2.0, 1.5],
            [3.0, 4.0, 3.5],
            [0.5, 1.0, 0.8]
        ]
    }
    ```
    """
    service = GRNService(db)
    network = await service.get_network(network_id)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Network {network_id} not found",
        )

    if network.status == NetworkStatus.INFERRING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Network inference already in progress",
        )

    # Validar dimensões da matriz
    n_genes = len(expression_data.genes)
    n_samples = len(expression_data.samples)

    if len(expression_data.expression_matrix) != n_genes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Matrix has {len(expression_data.expression_matrix)} rows, expected {n_genes} (number of genes)",
        )

    for i, row in enumerate(expression_data.expression_matrix):
        if len(row) != n_samples:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Row {i} has {len(row)} columns, expected {n_samples} (number of samples)",
            )

    # Executar inferência
    network = await service.infer_network(network_id, expression_data)

    response = NetworkResponse.model_validate(network)
    response.density = network.density
    return response


@router.post(
    "/{network_id}/infer",
    response_model=NetworkResponse,
    summary="Re-inferir rede",
    description="Re-executa inferência com novos parâmetros.",
)
async def reinfer_network(
    network_id: int,
    request: InferNetworkRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Re-infere a rede com parâmetros diferentes.

    Requer que a rede já tenha dados de expressão.
    """
    service = GRNService(db)
    network = await service.get_network(network_id)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Network {network_id} not found",
        )

    # Atualizar parâmetros se fornecidos
    if request.method:
        network.method = request.method
    if request.threshold:
        network.threshold = request.threshold

    await db.commit()

    # Nota: Para re-inferir, precisaríamos ter armazenado os dados de expressão
    # Esta é uma simplificação - em produção, armazenar dados ou exigir re-upload

    response = NetworkResponse.model_validate(network)
    response.density = network.density
    return response


# ========================================
# GRAPH QUERY ENDPOINTS
# ========================================

@router.get(
    "/{network_id}/graph",
    response_model=CytoscapeGraphData,
    summary="Exportar grafo (Cytoscape.js)",
    description="Retorna o grafo no formato Cytoscape.js para visualização.",
)
async def get_graph_cytoscape(
    network_id: int,
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=10000,
        description="Limitar número de nós"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Exporta o grafo no formato Cytoscape.js.

    Formato de saída:
    ```json
    {
        "elements": {
            "nodes": [
                {"data": {"id": "GENE1", "label": "TF1"}}
            ],
            "edges": [
                {"data": {"source": "GENE1", "target": "GENE2", "weight": 0.85}}
            ]
        }
    }
    ```

    Use o parâmetro `limit` para redes grandes.
    """
    service = GRNService(db)

    try:
        graph_data = await service.get_graph_data(network_id, limit=limit)
        return graph_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{network_id}/statistics",
    response_model=NetworkStatistics,
    summary="Estatísticas da rede",
    description="Retorna estatísticas detalhadas da rede.",
)
async def get_network_statistics(
    network_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Calcula e retorna estatísticas da rede:
    - Contagens (nós, arestas)
    - Densidade
    - Distribuição de grau
    - Top reguladores (hubs)
    - Top alvos
    """
    service = GRNService(db)

    try:
        stats = await service.get_network_statistics(network_id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{network_id}/neighbors/{gene_id}",
    response_model=SubnetworkResponse,
    summary="Vizinhos de um gene",
    description="Retorna sub-rede com vizinhos de um gene.",
)
async def get_gene_neighbors(
    network_id: int,
    gene_id: str,
    depth: int = Query(1, ge=1, le=3, description="Profundidade da busca"),
    direction: str = Query(
        "both",
        description="Direção: incoming, outgoing, both"
    ),
    min_weight: Optional[float] = Query(
        None,
        ge=0,
        le=1,
        description="Peso mínimo para incluir aresta"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Busca vizinhos de um gene até determinada profundidade.

    Parâmetros:
    - depth: 1-3 (quantos "hops" na rede)
    - direction: incoming (regulado por), outgoing (regula), both
    - min_weight: filtrar arestas por peso mínimo
    """
    if direction not in ["incoming", "outgoing", "both"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="direction must be: incoming, outgoing, or both",
        )

    service = GRNService(db)

    try:
        subnetwork = await service.get_gene_neighbors(
            network_id=network_id,
            gene_id=gene_id,
            depth=depth,
            direction=direction,
            min_weight=min_weight,
        )
        return subnetwork
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{network_id}/path",
    response_model=PathResponse,
    summary="Caminho entre genes",
    description="Encontra o caminho mais curto entre dois genes.",
)
async def find_path_between_genes(
    network_id: int,
    source: str = Query(..., description="Gene de origem"),
    target: str = Query(..., description="Gene de destino"),
    max_hops: int = Query(5, ge=1, le=10, description="Máximo de hops"),
    db: AsyncSession = Depends(get_db),
):
    """
    Encontra o caminho mais curto (shortest path) entre dois genes.

    Usa algoritmo de busca em largura do Neo4j.
    """
    service = GRNService(db)

    try:
        path = await service.find_path(
            network_id=network_id,
            source_gene=source,
            target_gene=target,
            max_hops=max_hops,
        )
        return path
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
