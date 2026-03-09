"""
Schemas: Gene Regulatory Network (GRN)
======================================

Pydantic schemas para Gene Regulatory Networks.

DECISÕES TÉCNICAS:
------------------
1. NetworkCreateRequest: criar nova rede
2. NetworkResponse: metadados completos
3. NetworkSummary: listagem
4. GraphData: formato Cytoscape.js
5. GeneNode/RegulationEdge: elementos do grafo
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.gene_network import NetworkStatus, InferenceMethod


# ========================================
# REQUEST SCHEMAS
# ========================================

class NetworkCreateRequest(BaseModel):
    """
    Schema para criar uma nova GRN.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nome da rede"
    )

    description: Optional[str] = Field(
        None,
        description="Descrição da rede"
    )

    organism: Optional[str] = Field(
        None,
        max_length=255,
        description="Organismo de origem"
    )

    method: InferenceMethod = Field(
        InferenceMethod.CORRELATION,
        description="Método de inferência"
    )

    threshold: float = Field(
        0.5,
        ge=0,
        le=1,
        description="Threshold para incluir aresta"
    )

    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Parâmetros adicionais do método"
    )

    expression_source: Optional[str] = Field(
        None,
        description="Fonte dos dados de expressão (GEO ID, arquivo)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Sporisorium scitamineum GRN",
                    "organism": "Sporisorium scitamineum",
                    "method": "correlation",
                    "threshold": 0.7,
                    "expression_source": "GSE12345"
                }
            ]
        }
    }


class ExpressionDataUpload(BaseModel):
    """
    Schema para upload de matriz de expressão.
    """
    network_id: int = Field(
        ...,
        description="ID da rede"
    )

    # Formato: lista de genes com valores de expressão
    genes: List[str] = Field(
        ...,
        min_length=2,
        description="Lista de IDs/nomes de genes"
    )

    samples: List[str] = Field(
        ...,
        min_length=3,
        description="Lista de IDs/nomes de amostras"
    )

    expression_matrix: List[List[float]] = Field(
        ...,
        description="Matriz de expressão [genes x samples]"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "network_id": 1,
                    "genes": ["GENE1", "GENE2", "GENE3"],
                    "samples": ["sample1", "sample2", "sample3", "sample4"],
                    "expression_matrix": [
                        [1.0, 2.0, 1.5, 2.5],
                        [3.0, 4.0, 3.5, 4.5],
                        [0.5, 1.0, 0.8, 1.2]
                    ]
                }
            ]
        }
    }


class InferNetworkRequest(BaseModel):
    """
    Schema para iniciar inferência de rede.
    """
    method: Optional[InferenceMethod] = Field(
        None,
        description="Método (se diferente do padrão)"
    )

    threshold: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Threshold para arestas"
    )

    # Parâmetros específicos por método
    correlation_method: Optional[str] = Field(
        "pearson",
        description="Tipo de correlação (pearson/spearman)"
    )

    top_regulators: Optional[int] = Field(
        None,
        ge=1,
        description="Número de top reguladores a considerar"
    )


# ========================================
# GRAPH ELEMENTS
# ========================================

class GeneNode(BaseModel):
    """
    Representa um nó (gene) no grafo.
    """
    id: str = Field(..., description="ID único do gene")
    label: str = Field(..., description="Nome/símbolo do gene")

    # Atributos opcionais
    gene_id: Optional[str] = Field(None, description="ID externo (NCBI, Ensembl)")
    symbol: Optional[str] = Field(None, description="Símbolo do gene")
    description: Optional[str] = Field(None, description="Descrição/função")

    # Métricas de centralidade
    degree: Optional[int] = Field(None, ge=0, description="Grau (total de conexões)")
    in_degree: Optional[int] = Field(None, ge=0, description="In-degree (regulado por)")
    out_degree: Optional[int] = Field(None, ge=0, description="Out-degree (regula)")
    betweenness: Optional[float] = Field(None, ge=0, description="Betweenness centrality")
    pagerank: Optional[float] = Field(None, ge=0, description="PageRank score")

    # Tipo de nó
    is_transcription_factor: bool = Field(
        False,
        description="É fator de transcrição (TF)?"
    )

    # Expressão média (se disponível)
    mean_expression: Optional[float] = None

    # Posição para visualização (Cytoscape.js)
    position: Optional[Dict[str, float]] = Field(
        None,
        description="Posição {x, y} para visualização"
    )


class RegulationEdge(BaseModel):
    """
    Representa uma aresta (regulação) no grafo.
    """
    id: str = Field(..., description="ID único da aresta")
    source: str = Field(..., description="ID do gene regulador (TF)")
    target: str = Field(..., description="ID do gene alvo")

    # Propriedades da regulação
    weight: float = Field(
        ...,
        ge=-1,
        le=1,
        description="Peso/força da regulação (-1 a 1)"
    )

    regulation_type: str = Field(
        "unknown",
        description="Tipo: activation, repression, unknown"
    )

    # Métricas
    score: Optional[float] = Field(
        None,
        description="Score de confiança"
    )

    correlation: Optional[float] = Field(
        None,
        ge=-1,
        le=1,
        description="Correlação de expressão"
    )

    pvalue: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="P-value da correlação"
    )

    # Evidências
    evidence: Optional[List[str]] = Field(
        None,
        description="Fontes de evidência"
    )


# ========================================
# RESPONSE SCHEMAS
# ========================================

class NetworkResponse(BaseModel):
    """
    Resposta completa para uma rede.
    """
    id: int
    network_id: UUID

    name: str
    description: Optional[str] = None
    organism: Optional[str] = None

    status: NetworkStatus
    method: InferenceMethod
    parameters: Optional[Dict[str, Any]] = None

    # Estatísticas
    node_count: int
    edge_count: int
    density: Optional[float] = None

    # Fonte
    expression_source: Optional[str] = None
    threshold: float

    # Erro (se houver)
    error_message: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class NetworkSummary(BaseModel):
    """
    Versão resumida para listagem.
    """
    id: int
    network_id: UUID
    name: str
    organism: Optional[str] = None

    status: NetworkStatus
    method: InferenceMethod

    node_count: int
    edge_count: int

    created_at: datetime

    model_config = {"from_attributes": True}


class NetworkListResponse(BaseModel):
    """
    Lista de redes com paginação.
    """
    items: List[NetworkSummary]
    total: int
    page: int
    page_size: int
    pages: int


# ========================================
# CYTOSCAPE.JS FORMAT
# ========================================

class CytoscapeNode(BaseModel):
    """
    Nó no formato Cytoscape.js.
    """
    data: Dict[str, Any] = Field(
        ...,
        description="Atributos do nó (id, label, etc.)"
    )
    position: Optional[Dict[str, float]] = Field(
        None,
        description="Posição {x, y}"
    )
    classes: Optional[str] = Field(
        None,
        description="Classes CSS"
    )


class CytoscapeEdge(BaseModel):
    """
    Aresta no formato Cytoscape.js.
    """
    data: Dict[str, Any] = Field(
        ...,
        description="Atributos (id, source, target, weight)"
    )
    classes: Optional[str] = Field(
        None,
        description="Classes CSS"
    )


class CytoscapeGraphData(BaseModel):
    """
    Grafo completo no formato Cytoscape.js.

    Formato esperado pelo Cytoscape.js:
    {
        "elements": {
            "nodes": [...],
            "edges": [...]
        }
    }
    """
    elements: Dict[str, List[Dict[str, Any]]] = Field(
        ...,
        description="Elementos do grafo (nodes, edges)"
    )

    # Metadados opcionais
    network_id: Optional[UUID] = None
    name: Optional[str] = None
    node_count: Optional[int] = None
    edge_count: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "elements": {
                        "nodes": [
                            {"data": {"id": "GENE1", "label": "TF1"}, "position": {"x": 100, "y": 100}},
                            {"data": {"id": "GENE2", "label": "Target1"}, "position": {"x": 200, "y": 200}}
                        ],
                        "edges": [
                            {"data": {"id": "e1", "source": "GENE1", "target": "GENE2", "weight": 0.85}}
                        ]
                    },
                    "network_id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Example GRN",
                    "node_count": 2,
                    "edge_count": 1
                }
            ]
        }
    }


# ========================================
# STATISTICS
# ========================================

class NetworkStatistics(BaseModel):
    """
    Estatísticas detalhadas de uma rede.
    """
    # Contagens básicas
    node_count: int
    edge_count: int
    density: float

    # Distribuição de grau
    avg_degree: float
    max_in_degree: int
    max_out_degree: int

    # Top reguladores (hubs)
    top_regulators: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top genes por out-degree"
    )

    # Top alvos
    top_targets: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top genes por in-degree"
    )

    # Componentes
    num_components: Optional[int] = None
    largest_component_size: Optional[int] = None

    # Distribuição de pesos
    avg_weight: Optional[float] = None
    weight_distribution: Optional[Dict[str, int]] = None


class NetworkComparisonResult(BaseModel):
    """
    Resultado da comparação entre duas redes.
    """
    network1_id: int
    network2_id: int

    # Nós
    common_nodes: int
    unique_to_network1: int
    unique_to_network2: int
    node_jaccard: float = Field(ge=0, le=1)

    # Arestas
    common_edges: int
    unique_edges_network1: int
    unique_edges_network2: int
    edge_jaccard: float = Field(ge=0, le=1)

    # Correlação de pesos (arestas em comum)
    weight_correlation: Optional[float] = None


# ========================================
# QUERY SCHEMAS
# ========================================

class GeneNeighborsRequest(BaseModel):
    """
    Buscar vizinhos de um gene.
    """
    gene_id: str = Field(..., description="ID do gene")
    depth: int = Field(1, ge=1, le=3, description="Profundidade da busca")
    direction: str = Field(
        "both",
        description="Direção: incoming, outgoing, both"
    )
    min_weight: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Peso mínimo para incluir aresta"
    )


class SubnetworkResponse(BaseModel):
    """
    Sub-rede extraída.
    """
    center_gene: str
    depth: int
    nodes: List[GeneNode]
    edges: List[RegulationEdge]
    cytoscape_data: Optional[CytoscapeGraphData] = None


class PathQueryRequest(BaseModel):
    """
    Buscar caminho entre dois genes.
    """
    source_gene: str
    target_gene: str
    max_hops: int = Field(5, ge=1, le=10)


class PathResponse(BaseModel):
    """
    Caminho encontrado entre genes.
    """
    source: str
    target: str
    path_found: bool
    path_length: Optional[int] = None
    path: Optional[List[str]] = Field(
        None,
        description="Lista de genes no caminho"
    )
    edges: Optional[List[RegulationEdge]] = None
