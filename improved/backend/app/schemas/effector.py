"""
Schemas: Effector
==================

Pydantic schemas para predição de efetores.

DECISÕES TÉCNICAS:
------------------
1. EffectorPredictRequest: parâmetros para iniciar predição
2. EffectorResponse: resultado completo da predição
3. EffectorSummary: versão resumida para listagem
4. PipelineProgress: status detalhado de cada etapa
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from app.models.effector import EffectorClassification, PipelineStatus


# ========================================
# REQUEST SCHEMAS
# ========================================

class EffectorPredictRequest(BaseModel):
    """
    Schema para iniciar predição de efetor.
    """
    sequence_id: int = Field(
        ...,
        description="ID da sequência a analisar"
    )

    # Opções do pipeline
    run_signalp: bool = Field(
        True,
        description="Executar SignalP (peptídeo sinal)"
    )

    run_tmhmm: bool = Field(
        True,
        description="Executar TMHMM (domínios transmembrana)"
    )

    run_effectorp: bool = Field(
        True,
        description="Executar EffectorP (predição principal)"
    )

    run_deepredeff: bool = Field(
        True,
        description="Executar DeepRedeff (validação ML)"
    )

    run_phibase: bool = Field(
        True,
        description="Buscar no PHI-base (efetores conhecidos)"
    )

    # Thresholds
    signalp_threshold: float = Field(
        0.5,
        ge=0,
        le=1,
        description="Threshold para peptídeo sinal"
    )

    effectorp_threshold: float = Field(
        0.5,
        ge=0,
        le=1,
        description="Threshold para classificar como candidato"
    )

    phibase_evalue: float = Field(
        1e-5,
        gt=0,
        description="E-value para busca no PHI-base"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "sequence_id": 1,
                    "run_signalp": True,
                    "run_tmhmm": True,
                    "run_effectorp": True,
                    "effectorp_threshold": 0.6
                }
            ]
        }
    }


class EffectorBatchRequest(BaseModel):
    """
    Schema para predição em lote.
    """
    sequence_ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Lista de IDs de sequências"
    )

    # Herda opções do single request
    run_signalp: bool = True
    run_tmhmm: bool = True
    run_effectorp: bool = True
    run_deepredeff: bool = True
    run_phibase: bool = True


# ========================================
# RESPONSE SCHEMAS
# ========================================

class PipelineStepResult(BaseModel):
    """
    Resultado de uma etapa do pipeline.
    """
    status: PipelineStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class PipelineProgress(BaseModel):
    """
    Status detalhado do pipeline.
    """
    overall_status: PipelineStatus
    progress_percent: int = Field(ge=0, le=100)

    signalp: PipelineStepResult
    tmhmm: PipelineStepResult
    effectorp: PipelineStepResult
    deepredeff: PipelineStepResult
    phibase: PipelineStepResult


class SignalPResult(BaseModel):
    """
    Resultados do SignalP.
    """
    has_signal_peptide: bool
    probability: float = Field(ge=0, le=1)
    cleavage_site_start: Optional[int] = None
    cleavage_site_end: Optional[int] = None


class TMHMMResult(BaseModel):
    """
    Resultados do TMHMM.
    """
    num_tm_domains: int
    topology: Optional[str] = None
    is_secreted: bool = Field(
        description="True se 0-1 TM domains (potencialmente secretada)"
    )


class EffectorPResult(BaseModel):
    """
    Resultados do EffectorP.
    """
    score: float = Field(ge=0, le=1)
    prediction: str  # "effector" ou "non-effector"
    version: str


class PHIBaseMatch(BaseModel):
    """
    Match no PHI-base.
    """
    phi_id: str
    gene_name: Optional[str] = None
    organism: Optional[str] = None
    phenotype: Optional[str] = None
    evalue: float
    identity_percent: float
    coverage_percent: Optional[float] = None


class EffectorResponse(BaseModel):
    """
    Resposta completa para um effector.
    """
    id: int
    sequence_id: int
    sequence_name: Optional[str] = None

    # Classificação
    classification: EffectorClassification
    confidence_score: Optional[float] = None
    classification_reasons: Optional[Dict[str, Any]] = None

    # Status do pipeline
    pipeline_status: PipelineStatus
    pipeline_started_at: Optional[datetime] = None
    pipeline_completed_at: Optional[datetime] = None

    # Resultados SignalP
    has_signal_peptide: Optional[bool] = None
    signalp_probability: Optional[float] = None
    signal_peptide_end: Optional[int] = None

    # Resultados TMHMM
    tmhmm_domains: Optional[int] = None
    tmhmm_topology: Optional[str] = None

    # Resultados EffectorP
    effectorp_score: Optional[float] = None
    effectorp_prediction: Optional[str] = None

    # Resultados DeepRedeff
    deepredeff_score: Optional[float] = None
    deepredeff_prediction: Optional[str] = None

    # PHI-base
    phibase_hit: Optional[bool] = None
    phibase_id: Optional[str] = None
    phibase_phenotype: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EffectorSummary(BaseModel):
    """
    Versão resumida para listagem.
    """
    id: int
    sequence_id: int
    sequence_name: Optional[str] = None

    classification: EffectorClassification
    confidence_score: Optional[float] = None
    pipeline_status: PipelineStatus

    # Principais métricas
    effectorp_score: Optional[float] = None
    has_signal_peptide: Optional[bool] = None
    phibase_hit: Optional[bool] = None

    model_config = {"from_attributes": True}


class EffectorListResponse(BaseModel):
    """
    Lista de effectors com paginação.
    """
    items: List[EffectorSummary]
    total: int
    page: int
    page_size: int
    pages: int

    # Estatísticas
    by_classification: Dict[str, int] = Field(
        default_factory=dict,
        description="Contagem por classificação"
    )


# ========================================
# STATISTICS SCHEMAS
# ========================================

class EffectorStatistics(BaseModel):
    """
    Estatísticas gerais de efetores.
    """
    total_analyzed: int = Field(..., description="Total de sequências analisadas")
    total_candidates: int = Field(..., description="Total de candidatos")
    total_high_confidence: int = Field(..., description="Alta confiança")
    total_validated: int = Field(..., description="Validados (PHI-base)")
    total_rejected: int = Field(..., description="Rejeitados")

    # Métricas do pipeline
    average_effectorp_score: Optional[float] = None
    secreted_proteins: int = 0
    with_phibase_match: int = 0

    # Por organismo (se disponível)
    by_organism: Optional[Dict[str, int]] = None


# ========================================
# FILTER SCHEMAS
# ========================================

class EffectorFilter(BaseModel):
    """
    Filtros para busca de efetores.
    """
    classification: Optional[EffectorClassification] = None
    min_effectorp_score: Optional[float] = Field(None, ge=0, le=1)
    max_effectorp_score: Optional[float] = Field(None, ge=0, le=1)
    has_signal_peptide: Optional[bool] = None
    has_phibase_match: Optional[bool] = None
    organism: Optional[str] = None
