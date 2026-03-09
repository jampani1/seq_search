"""
Service: Sequence
==================

Business logic para operações com sequências biológicas.

DECISÕES TÉCNICAS:
------------------
1. Repository Pattern simplificado:
   - Service encapsula todas as operações de banco
   - Endpoints não acessam ORM diretamente
   - Facilita testes com mocks

2. Operações async:
   - Todas as queries são async para não bloquear
   - Usa select() ao invés de session.query() (SQLAlchemy 2.0)

3. Paginação:
   - Offset-based (simples para UIs de paginação)
   - Retorna metadados úteis (total, pages)

4. Transações:
   - Commit/rollback gerenciados pela session do FastAPI
   - Service não faz commit explícito
"""

from typing import Optional, List, Dict, Any
from math import ceil

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sequence import Sequence, SequenceType
from app.schemas.sequence import SequenceCreate, SequenceUpdate, SequenceListResponse


class SequenceService:
    """
    Serviço para operações CRUD de sequências.

    Uso:
    ```python
    from app.services.sequence_service import SequenceService

    async def my_endpoint(db: AsyncSession = Depends(get_db)):
        service = SequenceService(db)
        sequence = await service.get_by_id(1)
    ```
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa o serviço com uma sessão do banco.

        Args:
            db: Sessão async do SQLAlchemy
        """
        self.db = db

    # ========================================
    # CREATE
    # ========================================

    async def create(self, data: SequenceCreate) -> Sequence:
        """
        Cria uma nova sequência no banco.

        Args:
            data: Dados validados pelo Pydantic

        Returns:
            Sequência criada com ID
        """
        sequence = Sequence(
            name=data.name,
            description=data.description,
            sequence_type=data.sequence_type,
            content=data.content,
            length=len(data.content),
            organism=data.organism,
            source=data.source,
        )

        self.db.add(sequence)
        await self.db.flush()  # Gera o ID sem commitar
        await self.db.refresh(sequence)  # Carrega timestamps

        return sequence

    # ========================================
    # READ - Get by ID
    # ========================================

    async def get_by_id(self, sequence_id: int) -> Optional[Sequence]:
        """
        Busca uma sequência pelo ID.

        Args:
            sequence_id: ID da sequência

        Returns:
            Sequência ou None se não encontrada
        """
        result = await self.db.execute(
            select(Sequence).where(Sequence.id == sequence_id)
        )
        return result.scalar_one_or_none()

    # ========================================
    # READ - List with pagination
    # ========================================

    async def list_sequences(
        self,
        page: int = 1,
        page_size: int = 20,
        sequence_type: Optional[SequenceType] = None,
        organism: Optional[str] = None,
        search: Optional[str] = None,
    ) -> SequenceListResponse:
        """
        Lista sequências com paginação e filtros.

        Args:
            page: Número da página (1-indexed)
            page_size: Itens por página
            sequence_type: Filtrar por tipo (dna, rna, protein)
            organism: Filtrar por organismo (busca parcial)
            search: Buscar por nome

        Returns:
            Resposta paginada com lista de sequências
        """
        # Base query
        query = select(Sequence)

        # Aplicar filtros
        if sequence_type:
            query = query.where(Sequence.sequence_type == sequence_type)

        if organism:
            # Busca parcial case-insensitive
            query = query.where(Sequence.organism.ilike(f"%{organism}%"))

        if search:
            # Busca por nome ou descrição
            query = query.where(
                or_(
                    Sequence.name.ilike(f"%{search}%"),
                    Sequence.description.ilike(f"%{search}%")
                )
            )

        # Contar total (mesmos filtros)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Aplicar paginação
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Ordenar por data de criação (mais recentes primeiro)
        query = query.order_by(Sequence.created_at.desc())

        # Executar query
        result = await self.db.execute(query)
        sequences = list(result.scalars().all())

        # Calcular total de páginas
        pages = ceil(total / page_size) if total > 0 else 1

        return SequenceListResponse(
            items=sequences,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    # ========================================
    # UPDATE
    # ========================================

    async def update(
        self, sequence_id: int, data: SequenceUpdate
    ) -> Optional[Sequence]:
        """
        Atualiza uma sequência existente.

        Apenas campos fornecidos serão atualizados.

        Args:
            sequence_id: ID da sequência
            data: Dados a atualizar

        Returns:
            Sequência atualizada ou None se não encontrada
        """
        sequence = await self.get_by_id(sequence_id)

        if not sequence:
            return None

        # Atualizar apenas campos fornecidos
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(sequence, field, value)

        await self.db.flush()
        await self.db.refresh(sequence)

        return sequence

    # ========================================
    # DELETE
    # ========================================

    async def delete(self, sequence_id: int) -> bool:
        """
        Deleta uma sequência pelo ID.

        Args:
            sequence_id: ID da sequência

        Returns:
            True se deletada, False se não encontrada
        """
        sequence = await self.get_by_id(sequence_id)

        if not sequence:
            return False

        await self.db.delete(sequence)
        await self.db.flush()

        return True

    # ========================================
    # STATISTICS
    # ========================================

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas sobre as sequências.

        Returns:
            Dict com estatísticas:
            - total: Total de sequências
            - by_type: Contagem por tipo
            - by_organism: Top organismos
            - avg_length: Comprimento médio
        """
        # Total de sequências
        total_result = await self.db.execute(
            select(func.count(Sequence.id))
        )
        total = total_result.scalar_one()

        # Contagem por tipo
        type_counts_result = await self.db.execute(
            select(
                Sequence.sequence_type,
                func.count(Sequence.id).label("count")
            ).group_by(Sequence.sequence_type)
        )
        by_type = {
            row.sequence_type.value: row.count
            for row in type_counts_result.all()
        }

        # Top 10 organismos
        organism_counts_result = await self.db.execute(
            select(
                Sequence.organism,
                func.count(Sequence.id).label("count")
            )
            .where(Sequence.organism.isnot(None))
            .group_by(Sequence.organism)
            .order_by(func.count(Sequence.id).desc())
            .limit(10)
        )
        by_organism = [
            {"organism": row.organism, "count": row.count}
            for row in organism_counts_result.all()
        ]

        # Comprimento médio por tipo
        avg_length_result = await self.db.execute(
            select(
                Sequence.sequence_type,
                func.avg(Sequence.length).label("avg_length")
            ).group_by(Sequence.sequence_type)
        )
        avg_lengths = {
            row.sequence_type.value: round(row.avg_length, 2) if row.avg_length else 0
            for row in avg_length_result.all()
        }

        return {
            "total": total,
            "by_type": by_type,
            "by_organism": by_organism,
            "average_length_by_type": avg_lengths,
        }

    # ========================================
    # BULK OPERATIONS
    # ========================================

    async def create_many(self, sequences_data: List[SequenceCreate]) -> List[Sequence]:
        """
        Cria múltiplas sequências de uma vez.

        Útil para upload de arquivos FASTA com muitas sequências.

        Args:
            sequences_data: Lista de dados de sequências

        Returns:
            Lista de sequências criadas
        """
        sequences = []

        for data in sequences_data:
            sequence = Sequence(
                name=data.name,
                description=data.description,
                sequence_type=data.sequence_type,
                content=data.content,
                length=len(data.content),
                organism=data.organism,
                source=data.source,
            )
            self.db.add(sequence)
            sequences.append(sequence)

        await self.db.flush()

        # Refresh all to get IDs and timestamps
        for seq in sequences:
            await self.db.refresh(seq)

        return sequences

    # ========================================
    # SEARCH
    # ========================================

    async def search_by_content(
        self,
        pattern: str,
        sequence_type: Optional[SequenceType] = None,
        limit: int = 100,
    ) -> List[Sequence]:
        """
        Busca sequências por padrão no conteúdo.

        NOTA: Busca simples com LIKE. Para buscas mais sofisticadas,
        usar BLAST/DIAMOND (será implementado em fase posterior).

        Args:
            pattern: Padrão a buscar (substring)
            sequence_type: Filtrar por tipo
            limit: Máximo de resultados

        Returns:
            Lista de sequências que contêm o padrão
        """
        query = select(Sequence).where(
            Sequence.content.ilike(f"%{pattern.upper()}%")
        )

        if sequence_type:
            query = query.where(Sequence.sequence_type == sequence_type)

        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
