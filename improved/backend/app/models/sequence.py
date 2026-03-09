"""
Model: Sequence
===============

Representa uma sequência biológica (DNA, RNA ou Proteína).

DECISÕES TÉCNICAS:
------------------
1. Enum para tipo de sequência:
   - Garante valores válidos no banco
   - Facilita validação e queries

2. Campos de timestamp:
   - created_at: quando foi criado
   - updated_at: última modificação
   - Útil para auditoria e ordenação

3. Índices:
   - Por nome (busca frequente)
   - Por tipo (filtros)
   - Por data (ordenação)

4. Relação com outros models (futuro):
   - Sequence -> Annotations (1:N)
   - Sequence -> Effectors (1:N)
   - Sequence -> BLASTResults (1:N)
"""

import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.effector import Effector

from sqlalchemy import (
    String,
    Text,
    Enum,
    DateTime,
    Integer,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SequenceType(str, enum.Enum):
    """
    Tipos de sequências biológicas suportadas.

    - DNA: Sequência de nucleotídeos (A, T, C, G)
    - RNA: Sequência de nucleotídeos (A, U, C, G)
    - PROTEIN: Sequência de aminoácidos (20 letras padrão)

    Herda de 'str' para serialização JSON automática.
    """
    DNA = "dna"
    RNA = "rna"
    PROTEIN = "protein"


class Sequence(Base):
    """
    Model para sequências biológicas.

    Armazena sequências DNA, RNA ou proteína com metadados.

    Attributes:
        id: Identificador único (auto-incremento)
        name: Nome/identificador da sequência (ex: "COX1_Ntropicalis")
        description: Descrição opcional (linha do FASTA após >)
        sequence_type: Tipo da sequência (DNA, RNA, PROTEIN)
        content: A sequência em si (pode ser muito longa)
        length: Comprimento da sequência (calculado automaticamente)
        organism: Organismo de origem (opcional)
        source: Fonte dos dados (ex: "NCBI", "upload", "MFannot")
        created_at: Data/hora de criação
        updated_at: Data/hora da última atualização
    """

    __tablename__ = "sequences"

    # ========================================
    # COLUNAS PRINCIPAIS
    # ========================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID único da sequência"
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Nome/identificador da sequência"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Descrição da sequência (header FASTA)"
    )

    sequence_type: Mapped[SequenceType] = mapped_column(
        Enum(SequenceType),
        nullable=False,
        index=True,
        comment="Tipo: dna, rna ou protein"
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Sequência de nucleotídeos ou aminoácidos"
    )

    length: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Comprimento da sequência"
    )

    # ========================================
    # METADADOS OPCIONAIS
    # ========================================

    organism: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Organismo de origem (ex: Neophysopella tropicalis)"
    )

    source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Fonte dos dados (upload, NCBI, etc.)"
    )

    # ========================================
    # TIMESTAMPS
    # ========================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Data de criação"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Data da última atualização"
    )

    # ========================================
    # RELACIONAMENTOS
    # ========================================

    # Relação 1:1 com Effector (predição de efetor)
    effector: Mapped["Effector"] = relationship(
        "Effector",
        back_populates="sequence",
        uselist=False,
        lazy="joined",
        cascade="all, delete-orphan",
    )

    # ========================================
    # ÍNDICES COMPOSTOS
    # ========================================
    # Otimizam queries frequentes

    __table_args__ = (
        # Índice para buscar por organismo + tipo
        Index("ix_sequences_organism_type", "organism", "sequence_type"),

        # Índice para ordenação por data
        Index("ix_sequences_created_at", "created_at"),
    )

    # ========================================
    # MÉTODOS
    # ========================================

    def __repr__(self) -> str:
        """Representação para debug."""
        return f"<Sequence(id={self.id}, name='{self.name}', type={self.sequence_type.value}, length={self.length})>"

    @property
    def is_dna(self) -> bool:
        """Verifica se é sequência de DNA."""
        return self.sequence_type == SequenceType.DNA

    @property
    def is_protein(self) -> bool:
        """Verifica se é sequência de proteína."""
        return self.sequence_type == SequenceType.PROTEIN

    def validate_content(self) -> bool:
        """
        Valida se o conteúdo corresponde ao tipo declarado.

        Returns:
            True se válido, False caso contrário
        """
        content_upper = self.content.upper()

        if self.sequence_type == SequenceType.DNA:
            valid_chars = set("ATCGN")
        elif self.sequence_type == SequenceType.RNA:
            valid_chars = set("AUCGN")
        elif self.sequence_type == SequenceType.PROTEIN:
            # 20 aminoácidos padrão + X (desconhecido) + * (stop)
            valid_chars = set("ACDEFGHIKLMNPQRSTVWYX*")
        else:
            return False

        return all(char in valid_chars for char in content_upper)
