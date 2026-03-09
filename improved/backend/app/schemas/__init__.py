"""
Schemas - Pydantic models para validação de dados
=================================================

Schemas são usados para:
- Validar dados de entrada (requests)
- Definir formato de saída (responses)
- Documentação automática da API

Separação de Models e Schemas:
- Models (SQLAlchemy): estrutura do banco de dados
- Schemas (Pydantic): validação e serialização de API
"""

from app.schemas.sequence import (
    SequenceCreate,
    SequenceUpdate,
    SequenceResponse,
    SequenceListResponse,
)

from app.schemas.blast import (
    BlastRequest,
    BlastJobResponse,
    BlastResultResponse,
    BlastHit,
    BlastHSP,
    BlastDatabase,
    BlastDatabaseList,
    JobQueueStatus,
)

from app.schemas.effector import (
    EffectorPredictRequest,
    EffectorBatchRequest,
    EffectorResponse,
    EffectorSummary,
    EffectorListResponse,
    EffectorStatistics,
    EffectorFilter,
    PipelineProgress,
)

from app.schemas.grn import (
    NetworkCreateRequest,
    NetworkResponse,
    NetworkSummary,
    NetworkListResponse,
    GeneNode,
    RegulationEdge,
    CytoscapeGraphData,
    NetworkStatistics,
    ExpressionDataUpload,
    InferNetworkRequest,
    GeneNeighborsRequest,
    SubnetworkResponse,
    PathQueryRequest,
    PathResponse,
)

__all__ = [
    # Sequence
    "SequenceCreate",
    "SequenceUpdate",
    "SequenceResponse",
    "SequenceListResponse",
    # BLAST
    "BlastRequest",
    "BlastJobResponse",
    "BlastResultResponse",
    "BlastHit",
    "BlastHSP",
    "BlastDatabase",
    "BlastDatabaseList",
    "JobQueueStatus",
    # Effector
    "EffectorPredictRequest",
    "EffectorBatchRequest",
    "EffectorResponse",
    "EffectorSummary",
    "EffectorListResponse",
    "EffectorStatistics",
    "EffectorFilter",
    "PipelineProgress",
    # GRN
    "NetworkCreateRequest",
    "NetworkResponse",
    "NetworkSummary",
    "NetworkListResponse",
    "GeneNode",
    "RegulationEdge",
    "CytoscapeGraphData",
    "NetworkStatistics",
    "ExpressionDataUpload",
    "InferNetworkRequest",
    "GeneNeighborsRequest",
    "SubnetworkResponse",
    "PathQueryRequest",
    "PathResponse",
]
