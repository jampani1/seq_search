"""
Model: Effector
================

Representa uma predição de proteína efetora.

DECISÕES TÉCNICAS:
------------------
1. Relação com Sequence:
   - Cada Effector pertence a uma Sequence (FK)
   - Uma Sequence pode ter apenas um Effector (1:1)
   - Se a sequência for deletada, o Effector também é

2. Pipeline de predição:
   - SignalP: detecta peptídeo sinal (probabilidade 0-1)
   - TMHMM: número de domínios transmembrana
   - EffectorP: score de probabilidade de efetor
   - DeepRedeff: validação adicional
   - PHI-base: match com efetores conhecidos

3. Status do pipeline:
   - Cada etapa pode estar pending/running/completed/failed
   - Permite retomar de onde parou em caso de erro

4. Classificação final:
   - candidate: passou nos critérios básicos
   - high_confidence: EffectorP > 0.8 + DeepRedeff confirma
   - validated: match no PHI-base
   - rejected: falhou nos filtros
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
    Boolean,
    ForeignKey,
    JSON,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EffectorClassification(str, enum.Enum):
    """
    Classificação final do candidato a efetor.
    """
    PENDING = "pending"              # Ainda não classificado
    CANDIDATE = "candidate"          # Passou filtros básicos
    HIGH_CONFIDENCE = "high_confidence"  # Alta probabilidade
    VALIDATED = "validated"          # Confirmado (PHI-base match)
    REJECTED = "rejected"            # Rejeitado pelos filtros


class PipelineStatus(str, enum.Enum):
    """
    Status de cada etapa do pipeline.
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"  # Etapa pulada (ex: já tem TMHMM domains)


class Effector(Base):
    """
    Model para predição de efetores.

    Armazena resultados do pipeline Predector e classificação final.
    """

    __tablename__ = "effectors"

    # ========================================
    # IDENTIFICAÇÃO
    # ========================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID único do effector"
    )

    # Relação com Sequence (obrigatório)
    sequence_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sequences.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 1:1 com Sequence
        index=True,
        comment="ID da sequência associada"
    )

    # ========================================
    # STATUS DO PIPELINE
    # ========================================

    pipeline_status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus),
        default=PipelineStatus.PENDING,
        nullable=False,
        comment="Status geral do pipeline"
    )

    # Status individual de cada ferramenta
    signalp_status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus),
        default=PipelineStatus.PENDING,
        nullable=False,
    )

    tmhmm_status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus),
        default=PipelineStatus.PENDING,
        nullable=False,
    )

    effectorp_status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus),
        default=PipelineStatus.PENDING,
        nullable=False,
    )

    deepredeff_status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus),
        default=PipelineStatus.PENDING,
        nullable=False,
    )

    phibase_status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus),
        default=PipelineStatus.PENDING,
        nullable=False,
    )

    # ========================================
    # RESULTADOS - SignalP
    # ========================================
    # SignalP detecta peptídeo sinal (necessário para secreção)

    has_signal_peptide: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="Tem peptídeo sinal? (True/False)"
    )

    signalp_probability: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Probabilidade SignalP (0-1)"
    )

    signal_peptide_start: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Início do peptídeo sinal"
    )

    signal_peptide_end: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Fim do peptídeo sinal (cleavage site)"
    )

    # ========================================
    # RESULTADOS - TMHMM
    # ========================================
    # TMHMM detecta domínios transmembrana (devem ser filtrados)

    tmhmm_domains: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Número de domínios transmembrana"
    )

    tmhmm_topology: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Topologia predita (i/o/M)"
    )

    # ========================================
    # RESULTADOS - EffectorP
    # ========================================
    # EffectorP é o principal preditor de efetores

    effectorp_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Score EffectorP (0-1)"
    )

    effectorp_prediction: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Predição: effector/non-effector"
    )

    effectorp_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Versão do EffectorP usada"
    )

    # ========================================
    # RESULTADOS - DeepRedeff
    # ========================================
    # DeepRedeff usa deep learning para validar

    deepredeff_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Score DeepRedeff (0-1)"
    )

    deepredeff_prediction: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Predição DeepRedeff"
    )

    # ========================================
    # RESULTADOS - PHI-base
    # ========================================
    # PHI-base contém efetores experimentalmente validados

    phibase_hit: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="Tem match no PHI-base?"
    )

    phibase_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="ID do match no PHI-base"
    )

    phibase_evalue: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="E-value do BLAST contra PHI-base"
    )

    phibase_identity: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="% identidade com PHI-base"
    )

    phibase_phenotype: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Fenótipo associado no PHI-base"
    )

    # ========================================
    # CLASSIFICAÇÃO FINAL
    # ========================================

    classification: Mapped[EffectorClassification] = mapped_column(
        Enum(EffectorClassification),
        default=EffectorClassification.PENDING,
        nullable=False,
        index=True,
        comment="Classificação final"
    )

    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Score de confiança combinado (0-1)"
    )

    # Razões para a classificação
    classification_reasons: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Razões para a classificação"
    )

    # ========================================
    # ANOTAÇÃO MANUAL
    # ========================================

    manual_review: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="Foi revisado manualmente?"
    )

    manual_classification: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Classificação manual (se diferente)"
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notas do revisor"
    )

    # ========================================
    # TIMESTAMPS
    # ========================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    pipeline_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Início do pipeline"
    )

    pipeline_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Fim do pipeline"
    )

    # ========================================
    # RELACIONAMENTOS
    # ========================================

    # Relação com Sequence
    sequence: Mapped["Sequence"] = relationship(
        "Sequence",
        back_populates="effector",
        lazy="joined",
    )

    # ========================================
    # ÍNDICES
    # ========================================

    __table_args__ = (
        # Buscar por classificação
        Index("ix_effectors_classification_score", "classification", "confidence_score"),
        # Buscar candidatos com alta confiança
        Index("ix_effectors_effectorp_score", "effectorp_score"),
    )

    # ========================================
    # MÉTODOS
    # ========================================

    def __repr__(self) -> str:
        return (
            f"<Effector(id={self.id}, seq={self.sequence_id}, "
            f"class={self.classification.value}, score={self.confidence_score})>"
        )

    @property
    def is_secreted(self) -> bool:
        """Verifica se a proteína é secretada (tem peptídeo sinal, sem TM domains)."""
        return (
            self.has_signal_peptide is True and
            (self.tmhmm_domains is None or self.tmhmm_domains == 0)
        )

    @property
    def is_candidate(self) -> bool:
        """Verifica se é um candidato a efetor."""
        return self.classification in (
            EffectorClassification.CANDIDATE,
            EffectorClassification.HIGH_CONFIDENCE,
            EffectorClassification.VALIDATED,
        )

    def calculate_confidence(self) -> float:
        """
        Calcula score de confiança combinado.

        Pesos:
        - EffectorP: 40%
        - DeepRedeff: 25%
        - SignalP: 20%
        - PHI-base: 15%
        """
        score = 0.0
        weights_used = 0.0

        if self.effectorp_score is not None:
            score += self.effectorp_score * 0.40
            weights_used += 0.40

        if self.deepredeff_score is not None:
            score += self.deepredeff_score * 0.25
            weights_used += 0.25

        if self.signalp_probability is not None:
            score += self.signalp_probability * 0.20
            weights_used += 0.20

        if self.phibase_hit:
            score += 1.0 * 0.15  # Match no PHI-base = score máximo
            weights_used += 0.15

        # Normalizar pelo peso total usado
        if weights_used > 0:
            return score / weights_used
        return 0.0

    def classify(self) -> EffectorClassification:
        """
        Determina classificação baseada nos resultados.

        Critérios:
        - REJECTED: sem peptídeo sinal OU muitos TM domains
        - CANDIDATE: peptídeo sinal + EffectorP > 0.5
        - HIGH_CONFIDENCE: EffectorP > 0.8 + DeepRedeff > 0.7
        - VALIDATED: match no PHI-base
        """
        # Verificar secretion (peptídeo sinal, sem TM)
        if not self.is_secreted:
            return EffectorClassification.REJECTED

        # Match no PHI-base = validado
        if self.phibase_hit:
            return EffectorClassification.VALIDATED

        # Alta confiança
        if (
            self.effectorp_score is not None and
            self.effectorp_score > 0.8 and
            self.deepredeff_score is not None and
            self.deepredeff_score > 0.7
        ):
            return EffectorClassification.HIGH_CONFIDENCE

        # Candidato básico
        if (
            self.effectorp_score is not None and
            self.effectorp_score > 0.5
        ):
            return EffectorClassification.CANDIDATE

        return EffectorClassification.REJECTED


# Adicionar back_populates no Sequence model
# (feito via string para evitar circular import)
