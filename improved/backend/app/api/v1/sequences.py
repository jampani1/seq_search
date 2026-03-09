"""
API Endpoints: Sequences
========================

CRUD completo para sequências biológicas.

Endpoints:
- POST   /sequences          - Criar sequência
- GET    /sequences          - Listar com paginação
- GET    /sequences/{id}     - Buscar por ID
- PUT    /sequences/{id}     - Atualizar
- DELETE /sequences/{id}     - Deletar
- POST   /sequences/upload   - Upload de arquivo FASTA

DECISÕES TÉCNICAS:
------------------
1. Dependency Injection: db session via Depends()
2. Response Models: Pydantic schemas para documentação
3. HTTP Status Codes corretos (201 para criação, 204 para delete)
4. Paginação com offset/limit (simples e eficiente)
5. Filtros via Query parameters
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.sequence import Sequence, SequenceType
from app.schemas.sequence import (
    SequenceCreate,
    SequenceUpdate,
    SequenceResponse,
    SequenceListResponse,
)
from app.services.sequence_service import SequenceService
from app.utils.parsers import parse_fasta

# Criar router para sequences
router = APIRouter()


# ========================================
# CREATE - Criar nova sequência
# ========================================

@router.post(
    "/",
    response_model=SequenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova sequência",
    description="Cria uma nova sequência biológica (DNA, RNA ou proteína)."
)
async def create_sequence(
    sequence_data: SequenceCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova sequência no banco de dados.

    - **name**: Nome/identificador da sequência
    - **sequence_type**: Tipo (dna, rna, protein)
    - **content**: A sequência em si
    - **organism**: Organismo de origem (opcional)
    - **description**: Descrição/anotação (opcional)
    """
    service = SequenceService(db)
    sequence = await service.create(sequence_data)
    return sequence


# ========================================
# READ - Listar sequências (paginação)
# ========================================

@router.get(
    "/",
    response_model=SequenceListResponse,
    summary="Listar sequências",
    description="Lista sequências com paginação e filtros opcionais."
)
async def list_sequences(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    sequence_type: Optional[SequenceType] = Query(None, description="Filtrar por tipo"),
    organism: Optional[str] = Query(None, description="Filtrar por organismo"),
    search: Optional[str] = Query(None, description="Buscar por nome"),
):
    """
    Lista sequências com paginação.

    Filtros disponíveis:
    - **sequence_type**: dna, rna ou protein
    - **organism**: Nome do organismo (busca parcial)
    - **search**: Busca por nome da sequência

    Retorna lista paginada com metadados de navegação.
    """
    service = SequenceService(db)
    result = await service.list_sequences(
        page=page,
        page_size=page_size,
        sequence_type=sequence_type,
        organism=organism,
        search=search,
    )
    return result


# ========================================
# READ - Buscar por ID
# ========================================

@router.get(
    "/{sequence_id}",
    response_model=SequenceResponse,
    summary="Buscar sequência por ID",
    description="Retorna uma sequência específica pelo ID."
)
async def get_sequence(
    sequence_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca uma sequência pelo ID.

    Retorna 404 se não encontrada.
    """
    service = SequenceService(db)
    sequence = await service.get_by_id(sequence_id)

    if not sequence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sequência com ID {sequence_id} não encontrada"
        )

    return sequence


# ========================================
# UPDATE - Atualizar sequência
# ========================================

@router.put(
    "/{sequence_id}",
    response_model=SequenceResponse,
    summary="Atualizar sequência",
    description="Atualiza metadados de uma sequência existente."
)
async def update_sequence(
    sequence_id: int,
    sequence_data: SequenceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza uma sequência existente.

    **Nota**: Não é possível alterar o conteúdo ou tipo da sequência
    para preservar integridade de dados relacionados (efetores, BLAST, etc.).

    Campos atualizáveis:
    - name
    - description
    - organism
    - source
    """
    service = SequenceService(db)
    sequence = await service.update(sequence_id, sequence_data)

    if not sequence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sequência com ID {sequence_id} não encontrada"
        )

    return sequence


# ========================================
# DELETE - Remover sequência
# ========================================

@router.delete(
    "/{sequence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar sequência",
    description="Remove uma sequência do banco de dados."
)
async def delete_sequence(
    sequence_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Deleta uma sequência pelo ID.

    **ATENÇÃO**: Esta ação é irreversível e pode afetar
    dados relacionados (efetores, resultados de BLAST, etc.).

    Retorna 204 No Content em caso de sucesso.
    Retorna 404 se a sequência não existir.
    """
    service = SequenceService(db)
    deleted = await service.delete(sequence_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sequência com ID {sequence_id} não encontrada"
        )

    return None


# ========================================
# UPLOAD - Upload de arquivo FASTA
# ========================================

@router.post(
    "/upload",
    response_model=List[SequenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload de arquivo FASTA",
    description="Faz upload de um arquivo FASTA com múltiplas sequências."
)
async def upload_fasta(
    file: UploadFile = File(..., description="Arquivo FASTA (.fasta, .fa, .fna, .faa)"),
    organism: Optional[str] = Query(None, description="Organismo (aplicado a todas)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Faz upload de arquivo FASTA e salva todas as sequências.

    O tipo de sequência (DNA/Proteína) é detectado automaticamente.

    Formatos aceitos:
    - .fasta, .fa (genérico)
    - .fna (nucleotídeos)
    - .faa (aminoácidos)

    Retorna lista de sequências criadas.
    """
    # Validar extensão do arquivo
    allowed_extensions = {".fasta", ".fa", ".fna", ".faa"}
    file_ext = "." + file.filename.split(".")[-1].lower() if file.filename else ""

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensão não permitida. Use: {', '.join(allowed_extensions)}"
        )

    # Ler conteúdo do arquivo
    content = await file.read()
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo deve estar em formato UTF-8"
        )

    # Parse do FASTA
    try:
        parsed_sequences = parse_fasta(text_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao processar FASTA: {str(e)}"
        )

    if not parsed_sequences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma sequência encontrada no arquivo"
        )

    # Criar sequências no banco
    service = SequenceService(db)
    created_sequences = []

    for parsed in parsed_sequences:
        sequence_data = SequenceCreate(
            name=parsed["name"],
            description=parsed.get("description"),
            sequence_type=parsed["sequence_type"],
            content=parsed["content"],
            organism=organism,
            source="upload"
        )

        sequence = await service.create(sequence_data)
        created_sequences.append(sequence)

    return created_sequences


# ========================================
# STATISTICS - Estatísticas das sequências
# ========================================

@router.get(
    "/stats/summary",
    summary="Estatísticas das sequências",
    description="Retorna estatísticas gerais das sequências no banco."
)
async def get_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna estatísticas sobre as sequências:
    - Total de sequências
    - Contagem por tipo
    - Contagem por organismo
    - Comprimento médio
    """
    service = SequenceService(db)
    stats = await service.get_statistics()
    return stats
