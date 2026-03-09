"""
Model: BlastJob
================

Representa um job de BLAST/DIAMOND assíncrono.

DECISÕES TÉCNICAS:
------------------
1. Jobs assíncronos:
   - BLAST pode demorar segundos a minutos
   - Não bloquear o request HTTP
   - Permitir polling do status

2. Estados do job:
   - PENDING: Na fila, aguardando processamento
   - RUNNING: Em execução
   - COMPLETED: Finalizado com sucesso
   - FAILED: Erro durante execução

3. Armazenamento de resultados:
   - Resultados salvos em JSON no banco
   - Permite consulta rápida sem I/O de arquivo
   - Para resultados muito grandes, considerar S3/MinIO

4. Relação com Sequence:
   - Job pode ter uma query_sequence_id (do banco)
   - Ou query_content (sequência ad-hoc)
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Text,
    Enum,
    DateTime,
    Integer,
    Float,
    ForeignKey,
    JSON,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class JobStatus(str, enum.Enum):
    """
    Estados possíveis de um job BLAST.
    """
    PENDING = "pending"      # Na fila
    RUNNING = "running"      # Em execução
    COMPLETED = "completed"  # Sucesso
    FAILED = "failed"        # Erro


class BlastProgram(str, enum.Enum):
    """
    Programas BLAST disponíveis.

    - BLASTP: proteína vs proteína
    - BLASTN: nucleotídeo vs nucleotídeo
    - BLASTX: nucleotídeo traduzido vs proteína
    - TBLASTN: proteína vs nucleotídeo traduzido
    - DIAMOND: alternativa rápida ao BLASTP
    """
    BLASTP = "blastp"
    BLASTN = "blastn"
    BLASTX = "blastx"
    TBLASTN = "tblastn"
    DIAMOND = "diamond"


class BlastJob(Base):
    """
    Model para jobs de BLAST/DIAMOND.

    Armazena parâmetros de execução, status e resultados.
    """

    __tablename__ = "blast_jobs"

    # ========================================
    # IDENTIFICAÇÃO
    # ========================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID único do job"
    )

    # UUID para referência externa (não expor IDs sequenciais)
    job_uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        comment="UUID público do job"
    )

    # ========================================
    # QUERY (sequência de busca)
    # ========================================

    # Opção 1: Referência a sequência do banco
    query_sequence_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sequences.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID da sequência query (se do banco)"
    )

    # Opção 2: Sequência ad-hoc (não salva no banco)
    query_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Sequência query (se ad-hoc)"
    )

    query_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Nome da sequência query"
    )

    # ========================================
    # PARÂMETROS DO BLAST
    # ========================================

    program: Mapped[BlastProgram] = mapped_column(
        Enum(BlastProgram),
        nullable=False,
        comment="Programa: blastp, blastn, diamond, etc."
    )

    database: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nome do banco de dados alvo"
    )

    # Parâmetros principais
    evalue: Mapped[float] = mapped_column(
        Float,
        default=1e-5,
        nullable=False,
        comment="E-value threshold"
    )

    max_hits: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
        comment="Máximo de hits a retornar"
    )

    # Parâmetros adicionais em JSON (flexível)
    parameters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Parâmetros adicionais (JSON)"
    )

    # ========================================
    # STATUS E EXECUÇÃO
    # ========================================

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
        comment="Status atual do job"
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Progresso (0-100)"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mensagem de erro (se falhou)"
    )

    # ========================================
    # RESULTADOS
    # ========================================

    # Número de hits encontrados
    hits_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Número de hits encontrados"
    )

    # Resultados em JSON (para queries rápidas)
    results: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Resultados do BLAST (JSON)"
    )

    # Caminho para arquivo de resultados (opcional, para grandes resultados)
    results_file: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Caminho para arquivo de resultados"
    )

    # ========================================
    # TIMESTAMPS
    # ========================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Data de criação/submissão"
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Data de início da execução"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Data de conclusão"
    )

    # Duração em segundos (calculada)
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Duração da execução em segundos"
    )

    # ========================================
    # RELACIONAMENTOS
    # ========================================

    # Relação com Sequence (opcional)
    # query_sequence = relationship("Sequence", back_populates="blast_jobs")

    # ========================================
    # ÍNDICES
    # ========================================

    __table_args__ = (
        # Buscar jobs por status
        Index("ix_blast_jobs_status_created", "status", "created_at"),
        # Buscar jobs de uma sequência
        Index("ix_blast_jobs_query_sequence", "query_sequence_id"),
    )

    # ========================================
    # MÉTODOS
    # ========================================

    def __repr__(self) -> str:
        return f"<BlastJob(id={self.id}, uuid={self.job_uuid[:8]}..., status={self.status.value})>"

    @property
    def is_finished(self) -> bool:
        """Verifica se o job terminou (sucesso ou erro)."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED)

    @property
    def is_running(self) -> bool:
        """Verifica se o job está em execução."""
        return self.status == JobStatus.RUNNING

    def mark_running(self) -> None:
        """Marca o job como em execução."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, hits_count: int, results: dict) -> None:
        """Marca o job como concluído com sucesso."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.hits_count = hits_count
        self.results = results
        self.progress = 100

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = delta.total_seconds()

    def mark_failed(self, error_message: str) -> None:
        """Marca o job como falho."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = delta.total_seconds()
