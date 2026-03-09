"""
API Endpoints: BLAST
=====================

Endpoints para buscas de similaridade com BLAST/DIAMOND.

Endpoints:
- POST   /blast              - Submeter job
- GET    /blast/{job_id}     - Status do job
- GET    /blast/{job_id}/results - Resultados completos
- GET    /blast/databases    - Listar bancos disponíveis
- DELETE /blast/{job_id}     - Cancelar/deletar job

DECISÕES TÉCNICAS:
------------------
1. Jobs assíncronos:
   - POST retorna imediatamente com job_id
   - Cliente faz polling do status
   - Ou usa WebSocket para notificações (futuro)

2. Processamento em background:
   - Jobs ficam em fila Redis
   - Worker separado processa
   - Escala horizontalmente

3. Modo síncrono (opcional):
   - Para sequências pequenas
   - Espera resultado no mesmo request
   - Timeout de 30 segundos
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.blast_job import JobStatus
from app.schemas.blast import (
    BlastRequest,
    BlastJobResponse,
    BlastResultResponse,
    BlastDatabase,
    BlastDatabaseList,
)
from app.services.blast_service import BlastService

router = APIRouter()


# ========================================
# SUBMIT JOB
# ========================================

@router.post(
    "/",
    response_model=BlastJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submeter job BLAST",
    description="Submete um job de BLAST/DIAMOND para execução assíncrona."
)
async def submit_blast_job(
    request: BlastRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    sync: bool = Query(
        False,
        description="Se True, espera o resultado (máx 60s)"
    ),
):
    """
    Submete um novo job BLAST.

    O job é processado em background. Use o `job_id` retornado
    para consultar o status e resultados.

    **Parâmetros importantes:**
    - **program**: blastp (proteína), blastn (nucleotídeo), diamond (rápido)
    - **database**: Nome do banco de dados alvo
    - **evalue**: Threshold de E-value (default: 1e-5)
    - **max_hits**: Máximo de hits a retornar (default: 50)

    **Modo síncrono:**
    Use `?sync=true` para esperar o resultado (timeout 60s).
    Recomendado apenas para sequências pequenas.
    """
    service = BlastService(db)

    # Verificar se banco existe
    databases = await service.list_databases()
    db_names = [d.name for d in databases]

    if request.database not in db_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Banco '{request.database}' não encontrado. "
                   f"Disponíveis: {db_names}"
        )

    # Criar job
    job = await service.submit_job(request)

    if sync:
        # Modo síncrono: executar e esperar
        await service.run_job(job.job_uuid)
        # Refresh para pegar resultados
        job = await service.get_job(job.job_uuid)
    else:
        # Modo assíncrono: agendar para background
        background_tasks.add_task(
            _run_blast_job,
            job.job_uuid,
        )

    return BlastJobResponse(
        job_id=job.job_uuid,
        status=job.status,
        progress=job.progress,
        program=job.program,
        database=job.database,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        duration_seconds=job.duration_seconds,
        hits_count=job.hits_count,
        error_message=job.error_message,
    )


async def _run_blast_job(job_uuid: str):
    """
    Função auxiliar para executar job em background.

    NOTA: Em produção, isso seria feito por um worker separado
    consumindo de uma fila Redis.
    """
    from app.core.database import async_session_maker

    async with async_session_maker() as session:
        service = BlastService(session)
        await service.run_job(job_uuid)
        await session.commit()


# ========================================
# GET JOB STATUS
# ========================================

@router.get(
    "/{job_id}",
    response_model=BlastJobResponse,
    summary="Status do job",
    description="Retorna o status atual de um job BLAST."
)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Consulta o status de um job.

    **Status possíveis:**
    - `pending`: Na fila, aguardando
    - `running`: Em execução
    - `completed`: Finalizado com sucesso
    - `failed`: Erro durante execução

    Use este endpoint para polling até o job completar.
    """
    service = BlastService(db)
    job_response = await service.get_job_status(job_id)

    if not job_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} não encontrado"
        )

    return job_response


# ========================================
# GET JOB RESULTS
# ========================================

@router.get(
    "/{job_id}/results",
    response_model=BlastResultResponse,
    summary="Resultados do job",
    description="Retorna os resultados completos de um job BLAST concluído."
)
async def get_job_results(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna os resultados completos do BLAST.

    Só disponível para jobs com status `completed`.

    **Estrutura dos resultados:**
    - Lista de hits ordenados por E-value
    - Cada hit contém HSPs (alinhamentos)
    - Métricas: E-value, bit score, % identidade
    """
    service = BlastService(db)

    # Verificar se job existe
    job_status = await service.get_job_status(job_id)
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} não encontrado"
        )

    # Verificar se completou
    if job_status.status == JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job ainda não iniciou. Aguarde..."
        )

    if job_status.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job em execução ({job_status.progress}%). Aguarde..."
        )

    if job_status.status == JobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job falhou: {job_status.error_message}"
        )

    # Buscar resultados
    results = await service.get_job_results(job_id)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao carregar resultados"
        )

    return results


# ========================================
# LIST DATABASES
# ========================================

@router.get(
    "/databases",
    response_model=BlastDatabaseList,
    summary="Listar bancos de dados",
    description="Lista todos os bancos de dados BLAST/DIAMOND disponíveis."
)
async def list_databases(
    db: AsyncSession = Depends(get_db),
):
    """
    Lista bancos de dados disponíveis para busca.

    **Tipos de bancos:**
    - `prot`: Proteínas (para BLASTP, DIAMOND)
    - `nucl`: Nucleotídeos (para BLASTN)

    Os bancos são criados a partir de arquivos FASTA
    usando `makeblastdb` ou `diamond makedb`.
    """
    service = BlastService(db)
    databases = await service.list_databases()

    return BlastDatabaseList(
        databases=databases,
        total=len(databases),
    )


# ========================================
# DELETE JOB
# ========================================

@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar job",
    description="Remove um job e seus resultados."
)
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Deleta um job BLAST.

    Se o job estiver em execução, será cancelado.
    Resultados são removidos permanentemente.
    """
    service = BlastService(db)
    job = await service.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} não encontrado"
        )

    await db.delete(job)
    await db.flush()

    return None


# ========================================
# HEALTH CHECK
# ========================================

@router.get(
    "/health",
    summary="Health check do BLAST",
    description="Verifica se BLAST/DIAMOND estão funcionando."
)
async def blast_health():
    """
    Verifica disponibilidade dos programas BLAST.

    Retorna versões instaladas e status.
    """
    import asyncio
    import shutil

    results = {
        "blast_available": False,
        "diamond_available": False,
        "blast_version": None,
        "diamond_version": None,
    }

    # Check BLAST
    if shutil.which("blastp"):
        try:
            process = await asyncio.create_subprocess_exec(
                "blastp", "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            results["blast_available"] = True
            results["blast_version"] = stdout.decode().split("\n")[0]
        except Exception:
            pass

    # Check DIAMOND
    if shutil.which("diamond"):
        try:
            process = await asyncio.create_subprocess_exec(
                "diamond", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            results["diamond_available"] = True
            results["diamond_version"] = stdout.decode().strip()
        except Exception:
            pass

    return results
