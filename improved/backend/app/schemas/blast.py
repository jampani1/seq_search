"""
Schemas: BLAST
===============

Pydantic schemas para requisições e respostas de BLAST/DIAMOND.

DECISÕES TÉCNICAS:
------------------
1. Separação clara:
   - BlastRequest: para submeter job
   - BlastJobResponse: status do job
   - BlastResultResponse: resultados detalhados

2. Validações:
   - E-value deve ser positivo
   - max_hits limitado para evitar sobrecarga
   - Programa deve ser compatível com tipo de sequência

3. Resultados estruturados:
   - Hits com todas as métricas importantes
   - HSPs (High-Scoring Pairs) para alinhamentos
"""

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field, field_validator

from app.models.blast_job import JobStatus, BlastProgram


# ========================================
# REQUEST SCHEMAS
# ========================================

class BlastRequest(BaseModel):
    """
    Schema para submeter um job BLAST.

    Pode usar:
    - sequence_id: ID de uma sequência já no banco
    - sequence: Conteúdo da sequência diretamente
    """

    # Sequência (uma das duas opções)
    sequence_id: Optional[int] = Field(
        None,
        description="ID de uma sequência existente no banco"
    )

    sequence: Optional[str] = Field(
        None,
        min_length=10,
        description="Sequência para busca (se não usar sequence_id)"
    )

    sequence_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Nome da sequência (opcional)"
    )

    # Parâmetros do BLAST
    program: BlastProgram = Field(
        BlastProgram.BLASTP,
        description="Programa BLAST a usar"
    )

    database: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nome do banco de dados alvo",
        examples=["sporisorium_proteome", "nr", "swissprot"]
    )

    evalue: float = Field(
        1e-5,
        gt=0,
        le=10,
        description="E-value threshold (menor = mais restritivo)"
    )

    max_hits: int = Field(
        50,
        ge=1,
        le=500,
        description="Máximo de hits a retornar"
    )

    # Parâmetros avançados (opcionais)
    word_size: Optional[int] = Field(
        None,
        ge=2,
        le=7,
        description="Tamanho da palavra para seed"
    )

    gap_open: Optional[int] = Field(
        None,
        description="Penalidade para abrir gap"
    )

    gap_extend: Optional[int] = Field(
        None,
        description="Penalidade para estender gap"
    )

    matrix: Optional[str] = Field(
        None,
        description="Matriz de substituição (BLOSUM62, PAM250, etc.)"
    )

    @field_validator("sequence")
    @classmethod
    def clean_sequence(cls, v: Optional[str]) -> Optional[str]:
        """Remove espaços e converte para maiúsculo."""
        if v is None:
            return v
        import re
        return re.sub(r"\s+", "", v).upper()

    def model_post_init(self, *args, **kwargs) -> None:
        """Valida que sequence_id OU sequence foi fornecido."""
        if self.sequence_id is None and self.sequence is None:
            raise ValueError(
                "Forneça sequence_id (sequência existente) ou sequence (conteúdo)"
            )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "sequence": "MKFSILFAALVLSAAQAEPKVCNQCSKGCKGDCKCPGCKCNDCQC",
                    "program": "blastp",
                    "database": "sporisorium_proteome",
                    "evalue": 1e-5,
                    "max_hits": 50
                }
            ]
        }
    }


# ========================================
# RESPONSE SCHEMAS
# ========================================

class BlastJobResponse(BaseModel):
    """
    Schema de resposta para status de um job BLAST.
    """
    job_id: str = Field(..., description="UUID do job")
    status: JobStatus = Field(..., description="Status atual")
    progress: int = Field(..., ge=0, le=100, description="Progresso (0-100)")

    program: BlastProgram = Field(..., description="Programa usado")
    database: str = Field(..., description="Banco de dados alvo")

    created_at: datetime = Field(..., description="Data de submissão")
    started_at: Optional[datetime] = Field(None, description="Início da execução")
    completed_at: Optional[datetime] = Field(None, description="Data de conclusão")
    duration_seconds: Optional[float] = Field(None, description="Duração em segundos")

    hits_count: Optional[int] = Field(None, description="Número de hits encontrados")
    error_message: Optional[str] = Field(None, description="Mensagem de erro (se falhou)")

    model_config = {"from_attributes": True}


class BlastHSP(BaseModel):
    """
    High-Scoring Pair - um alinhamento individual.

    Cada hit pode ter múltiplos HSPs se houver
    alinhamentos em regiões diferentes.
    """
    hsp_num: int = Field(..., description="Número do HSP")

    # Scores
    bit_score: float = Field(..., description="Bit score")
    score: int = Field(..., description="Score raw")
    evalue: float = Field(..., description="E-value")

    # Posições na query
    query_from: int = Field(..., description="Início na query")
    query_to: int = Field(..., description="Fim na query")

    # Posições no hit (subject)
    hit_from: int = Field(..., description="Início no hit")
    hit_to: int = Field(..., description="Fim no hit")

    # Métricas de qualidade
    identity: int = Field(..., description="Número de matches idênticos")
    identity_percent: float = Field(..., description="Porcentagem de identidade")
    positive: int = Field(..., description="Matches positivos (similar)")
    gaps: int = Field(..., description="Número de gaps")
    align_len: int = Field(..., description="Comprimento do alinhamento")

    # Alinhamentos (strings)
    query_seq: Optional[str] = Field(None, description="Sequência query alinhada")
    hit_seq: Optional[str] = Field(None, description="Sequência hit alinhada")
    midline: Optional[str] = Field(None, description="Linha do meio (matches)")


class BlastHit(BaseModel):
    """
    Um hit do BLAST - uma sequência encontrada.
    """
    hit_num: int = Field(..., description="Ranking do hit")
    hit_id: str = Field(..., description="ID da sequência")
    hit_def: str = Field(..., description="Descrição/definição")
    hit_accession: Optional[str] = Field(None, description="Accession number")
    hit_len: int = Field(..., description="Comprimento da sequência")

    # Melhor HSP (para ordenação rápida)
    best_evalue: float = Field(..., description="Melhor E-value")
    best_bit_score: float = Field(..., description="Melhor bit score")
    best_identity_percent: float = Field(..., description="Melhor % identidade")

    # Todos os HSPs
    hsps: List[BlastHSP] = Field(default_factory=list, description="Lista de HSPs")


class BlastResultResponse(BaseModel):
    """
    Schema completo de resultados BLAST.
    """
    job_id: str = Field(..., description="UUID do job")
    status: JobStatus = Field(..., description="Status do job")

    # Informações da query
    query_id: Optional[str] = Field(None, description="ID da query")
    query_def: Optional[str] = Field(None, description="Descrição da query")
    query_len: Optional[int] = Field(None, description="Comprimento da query")

    # Informações do banco
    database: str = Field(..., description="Banco de dados usado")
    database_sequences: Optional[int] = Field(None, description="Sequências no banco")
    database_letters: Optional[int] = Field(None, description="Letras no banco")

    # Parâmetros usados
    program: BlastProgram = Field(..., description="Programa usado")
    evalue_threshold: float = Field(..., description="E-value threshold")

    # Resultados
    hits_count: int = Field(..., description="Número de hits")
    hits: List[BlastHit] = Field(default_factory=list, description="Lista de hits")

    # Execução
    created_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]


# ========================================
# DATABASE SCHEMAS
# ========================================

class BlastDatabase(BaseModel):
    """
    Informações sobre um banco de dados BLAST disponível.
    """
    name: str = Field(..., description="Nome do banco")
    description: Optional[str] = Field(None, description="Descrição")
    db_type: str = Field(..., description="Tipo: nucl ou prot")
    num_sequences: Optional[int] = Field(None, description="Número de sequências")
    total_length: Optional[int] = Field(None, description="Comprimento total")
    created_at: Optional[datetime] = Field(None, description="Data de criação")


class BlastDatabaseList(BaseModel):
    """
    Lista de bancos de dados disponíveis.
    """
    databases: List[BlastDatabase] = Field(..., description="Bancos disponíveis")
    total: int = Field(..., description="Total de bancos")


# ========================================
# QUEUE SCHEMAS
# ========================================

class JobQueueStatus(BaseModel):
    """
    Status da fila de jobs.
    """
    pending_jobs: int = Field(..., description="Jobs aguardando")
    running_jobs: int = Field(..., description="Jobs em execução")
    completed_today: int = Field(..., description="Jobs completados hoje")
    failed_today: int = Field(..., description="Jobs falhos hoje")
    average_duration: Optional[float] = Field(None, description="Duração média (s)")
