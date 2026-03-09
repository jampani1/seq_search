"""
Model: GeneNetwork
==================

Representa uma Gene Regulatory Network (GRN).

ARQUITETURA HÍBRIDA:
--------------------
1. PostgreSQL (este model):
   - Metadados da rede (nome, organismo, status)
   - Configuração de inferência
   - Estatísticas agregadas
   - Rastreabilidade (timestamps, usuário)

2. Neo4j (via neo4j.py):
   - Grafo em si (nós = genes, arestas = regulação)
   - Queries de traversal
   - Algoritmos de grafo (PageRank, centralidade)

DECISÕES TÉCNICAS:
------------------
1. Separação de concerns:
   - PostgreSQL: excelente para queries relacionais, transações ACID
   - Neo4j: otimizado para grafos, traversal eficiente

2. network_id como UUID:
   - Usado para linkar PostgreSQL <-> Neo4j
   - UUID garante unicidade global

3. Status workflow:
   - PENDING: aguardando processamento
   - INFERRING: inferência em andamento
   - COMPLETED: rede pronta
   - FAILED: erro no processamento

4. Métodos de inferência suportados:
   - CORRELATION: correlação de Pearson/Spearman
   - MUTUAL_INFO: informação mútua (ARACNE)
   - GRNBOOST2: gradient boosting (GRNBoost2/SCENIC)
   - WGCNA: Weighted Gene Co-expression Network Analysis
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Text,
    Enum,
    DateTime,
    Integer,
    Float,
    JSON,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NetworkStatus(str, enum.Enum):
    """
    Status do processamento da rede.
    """
    PENDING = "pending"         # Aguardando processamento
    INFERRING = "inferring"     # Inferência em andamento
    COMPLETED = "completed"     # Rede pronta
    FAILED = "failed"           # Erro no processamento


class InferenceMethod(str, enum.Enum):
    """
    Métodos de inferência de GRN suportados.
    """
    CORRELATION = "correlation"     # Pearson/Spearman
    MUTUAL_INFO = "mutual_info"     # ARACNE
    GRNBOOST2 = "grnboost2"         # Gradient boosting
    WGCNA = "wgcna"                 # Co-expression


class GeneNetwork(Base):
    """
    Model para Gene Regulatory Networks.

    Armazena metadados no PostgreSQL, grafo no Neo4j.

    Attributes:
        id: ID auto-incremento (PostgreSQL)
        network_id: UUID único (link com Neo4j)
        name: Nome da rede
        description: Descrição opcional
        organism: Organismo de origem
        status: Status do processamento
        method: Método de inferência usado
        parameters: Parâmetros do método (JSON)
        node_count: Número de genes/nós
        edge_count: Número de regulações/arestas
        expression_source: Fonte dos dados de expressão
        error_message: Mensagem de erro (se falhou)
        created_at: Data de criação
        updated_at: Última atualização
        completed_at: Quando finalizou
    """

    __tablename__ = "gene_networks"

    # ========================================
    # IDENTIFICADORES
    # ========================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID único (PostgreSQL)"
    )

    network_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
        comment="UUID único (link com Neo4j)"
    )

    # ========================================
    # METADADOS DA REDE
    # ========================================

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Nome da rede"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Descrição da rede"
    )

    organism: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Organismo de origem"
    )

    # ========================================
    # STATUS E PROCESSAMENTO
    # ========================================

    status: Mapped[NetworkStatus] = mapped_column(
        Enum(NetworkStatus),
        default=NetworkStatus.PENDING,
        nullable=False,
        index=True,
        comment="Status do processamento"
    )

    method: Mapped[InferenceMethod] = mapped_column(
        Enum(InferenceMethod),
        default=InferenceMethod.CORRELATION,
        nullable=False,
        comment="Método de inferência"
    )

    parameters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Parâmetros do método (JSON)"
    )

    # ========================================
    # ESTATÍSTICAS
    # ========================================

    node_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Número de genes/nós"
    )

    edge_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Número de regulações/arestas"
    )

    # ========================================
    # FONTE DE DADOS
    # ========================================

    expression_source: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Fonte dos dados de expressão (GEO ID, arquivo, etc.)"
    )

    threshold: Mapped[float] = mapped_column(
        Float,
        default=0.5,
        nullable=False,
        comment="Threshold para incluir aresta"
    )

    # ========================================
    # ERRO (se houver)
    # ========================================

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mensagem de erro (se status=failed)"
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

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Data de conclusão"
    )

    # ========================================
    # ÍNDICES COMPOSTOS
    # ========================================

    __table_args__ = (
        Index("ix_gene_networks_status_created", "status", "created_at"),
        Index("ix_gene_networks_organism_method", "organism", "method"),
    )

    # ========================================
    # MÉTODOS
    # ========================================

    def __repr__(self) -> str:
        """Representação para debug."""
        return (
            f"<GeneNetwork(id={self.id}, name='{self.name}', "
            f"status={self.status.value}, nodes={self.node_count}, edges={self.edge_count})>"
        )

    @property
    def is_ready(self) -> bool:
        """Verifica se a rede está pronta para uso."""
        return self.status == NetworkStatus.COMPLETED

    @property
    def is_processing(self) -> bool:
        """Verifica se está processando."""
        return self.status == NetworkStatus.INFERRING

    @property
    def has_failed(self) -> bool:
        """Verifica se falhou."""
        return self.status == NetworkStatus.FAILED

    @property
    def density(self) -> float:
        """
        Calcula a densidade do grafo.

        Densidade = 2E / (N * (N-1)) para grafos não-direcionados
        Densidade = E / (N * (N-1)) para grafos direcionados (nosso caso)
        """
        if self.node_count < 2:
            return 0.0
        max_edges = self.node_count * (self.node_count - 1)
        return self.edge_count / max_edges if max_edges > 0 else 0.0

    def neo4j_node_label(self) -> str:
        """Retorna o label do nó no Neo4j."""
        return f"Gene_{self.network_id.hex[:8]}"

    def neo4j_relationship_type(self) -> str:
        """Retorna o tipo de relacionamento no Neo4j."""
        return "REGULATES"
