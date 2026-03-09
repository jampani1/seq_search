"""
API Endpoints: Effectors
=========================

Endpoints para predição de efetores.

Endpoints:
- POST   /effectors/predict/{sequence_id}  - Iniciar predição
- POST   /effectors/predict/batch          - Predição em lote
- GET    /effectors                        - Listar efetores
- GET    /effectors/{id}                   - Buscar por ID
- GET    /effectors/stats                  - Estatísticas
- DELETE /effectors/{id}                   - Deletar

DECISÕES TÉCNICAS:
------------------
1. Predição assíncrona:
   - Pipeline pode demorar (SignalP, etc.)
   - Executado em background
   - Polling de status

2. Filtros avançados:
   - Por classificação
   - Por score mínimo
   - Por características (signal peptide, PHI-base)

3. Batch processing:
   - Processa múltiplas sequências
   - Limite de 100 por vez
   - Retorna job_id para polling
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.effector import EffectorClassification, PipelineStatus
from app.schemas.effector import (
    EffectorPredictRequest,
    EffectorBatchRequest,
    EffectorResponse,
    EffectorListResponse,
    EffectorStatistics,
)
from app.services.effector_service import EffectorService

router = APIRouter()


# ========================================
# PREDICT
# ========================================

@router.post(
    "/predict/{sequence_id}",
    response_model=EffectorResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Iniciar predição de efetor",
    description="Executa pipeline de predição para uma sequência."
)
async def predict_effector(
    sequence_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    run_signalp: bool = Query(True, description="Executar SignalP"),
    run_tmhmm: bool = Query(True, description="Executar TMHMM"),
    run_effectorp: bool = Query(True, description="Executar EffectorP"),
    run_deepredeff: bool = Query(True, description="Executar DeepRedeff"),
    run_phibase: bool = Query(True, description="Buscar no PHI-base"),
    sync: bool = Query(False, description="Esperar resultado"),
):
    """
    Inicia predição de efetor para uma sequência.

    **Pipeline Predector:**
    1. **SignalP**: Detecta peptídeo sinal (necessário para secreção)
    2. **TMHMM**: Detecta domínios transmembrana (devem ser filtrados)
    3. **EffectorP**: Score de probabilidade de ser efetor
    4. **DeepRedeff**: Validação com deep learning
    5. **PHI-base**: Busca contra efetores experimentalmente validados

    **Classificações possíveis:**
    - `rejected`: Não passou nos filtros (sem signal peptide ou muitos TM)
    - `candidate`: Passou filtros básicos, EffectorP > 0.5
    - `high_confidence`: EffectorP > 0.8 + DeepRedeff > 0.7
    - `validated`: Match no PHI-base

    Use `?sync=true` para esperar o resultado (pode demorar).
    """
    service = EffectorService(db)

    request = EffectorPredictRequest(
        sequence_id=sequence_id,
        run_signalp=run_signalp,
        run_tmhmm=run_tmhmm,
        run_effectorp=run_effectorp,
        run_deepredeff=run_deepredeff,
        run_phibase=run_phibase,
    )

    try:
        if sync:
            effector = await service.predict(request)
        else:
            # Criar placeholder e processar em background
            effector = await service.predict(request)
            # TODO: Em produção, usar background_tasks.add_task()

        return EffectorResponse(
            id=effector.id,
            sequence_id=effector.sequence_id,
            sequence_name=effector.sequence.name if effector.sequence else None,
            classification=effector.classification,
            confidence_score=effector.confidence_score,
            classification_reasons=effector.classification_reasons,
            pipeline_status=effector.pipeline_status,
            pipeline_started_at=effector.pipeline_started_at,
            pipeline_completed_at=effector.pipeline_completed_at,
            has_signal_peptide=effector.has_signal_peptide,
            signalp_probability=effector.signalp_probability,
            signal_peptide_end=effector.signal_peptide_end,
            tmhmm_domains=effector.tmhmm_domains,
            tmhmm_topology=effector.tmhmm_topology,
            effectorp_score=effector.effectorp_score,
            effectorp_prediction=effector.effectorp_prediction,
            deepredeff_score=effector.deepredeff_score,
            deepredeff_prediction=effector.deepredeff_prediction,
            phibase_hit=effector.phibase_hit,
            phibase_id=effector.phibase_id,
            phibase_phenotype=effector.phibase_phenotype,
            created_at=effector.created_at,
            updated_at=effector.updated_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/predict/batch",
    response_model=List[EffectorResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Predição em lote",
    description="Executa predição para múltiplas sequências."
)
async def predict_batch(
    request: EffectorBatchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Executa predição para múltiplas sequências.

    Máximo de 100 sequências por requisição.
    Retorna lista de resultados na mesma ordem.
    """
    if len(request.sequence_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo de 100 sequências por vez"
        )

    service = EffectorService(db)
    results = []

    for seq_id in request.sequence_ids:
        try:
            single_request = EffectorPredictRequest(
                sequence_id=seq_id,
                run_signalp=request.run_signalp,
                run_tmhmm=request.run_tmhmm,
                run_effectorp=request.run_effectorp,
                run_deepredeff=request.run_deepredeff,
                run_phibase=request.run_phibase,
            )
            effector = await service.predict(single_request)
            results.append(EffectorResponse(
                id=effector.id,
                sequence_id=effector.sequence_id,
                sequence_name=effector.sequence.name if effector.sequence else None,
                classification=effector.classification,
                confidence_score=effector.confidence_score,
                classification_reasons=effector.classification_reasons,
                pipeline_status=effector.pipeline_status,
                pipeline_started_at=effector.pipeline_started_at,
                pipeline_completed_at=effector.pipeline_completed_at,
                has_signal_peptide=effector.has_signal_peptide,
                signalp_probability=effector.signalp_probability,
                signal_peptide_end=effector.signal_peptide_end,
                tmhmm_domains=effector.tmhmm_domains,
                tmhmm_topology=effector.tmhmm_topology,
                effectorp_score=effector.effectorp_score,
                effectorp_prediction=effector.effectorp_prediction,
                deepredeff_score=effector.deepredeff_score,
                deepredeff_prediction=effector.deepredeff_prediction,
                phibase_hit=effector.phibase_hit,
                phibase_id=effector.phibase_id,
                phibase_phenotype=effector.phibase_phenotype,
                created_at=effector.created_at,
                updated_at=effector.updated_at,
            ))
        except ValueError as e:
            # Skip sequências inválidas, mas logar
            pass

    return results


# ========================================
# LIST
# ========================================

@router.get(
    "/",
    response_model=EffectorListResponse,
    summary="Listar efetores",
    description="Lista efetores com filtros e paginação."
)
async def list_effectors(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    classification: Optional[EffectorClassification] = Query(
        None, description="Filtrar por classificação"
    ),
    min_score: Optional[float] = Query(
        None, ge=0, le=1, description="Score EffectorP mínimo"
    ),
    has_signal_peptide: Optional[bool] = Query(
        None, description="Filtrar por peptídeo sinal"
    ),
    has_phibase_match: Optional[bool] = Query(
        None, description="Filtrar por match no PHI-base"
    ),
):
    """
    Lista efetores preditos.

    **Filtros disponíveis:**
    - `classification`: candidate, high_confidence, validated, rejected
    - `min_score`: Score EffectorP mínimo (0-1)
    - `has_signal_peptide`: Apenas com/sem peptídeo sinal
    - `has_phibase_match`: Apenas com/sem match no PHI-base

    Ordenado por confidence_score (decrescente).
    """
    service = EffectorService(db)

    return await service.list_effectors(
        page=page,
        page_size=page_size,
        classification=classification,
        min_score=min_score,
        has_signal_peptide=has_signal_peptide,
        has_phibase_match=has_phibase_match,
    )


# ========================================
# GET BY ID
# ========================================

@router.get(
    "/{effector_id}",
    response_model=EffectorResponse,
    summary="Buscar efetor por ID",
    description="Retorna detalhes completos de um efetor."
)
async def get_effector(
    effector_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna todos os detalhes de um efetor predito.

    Inclui:
    - Resultados de cada ferramenta do pipeline
    - Classificação e razões
    - Match no PHI-base (se houver)
    """
    service = EffectorService(db)
    effector = await service.get_by_id(effector_id)

    if not effector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Effector {effector_id} não encontrado"
        )

    return EffectorResponse(
        id=effector.id,
        sequence_id=effector.sequence_id,
        sequence_name=effector.sequence.name if effector.sequence else None,
        classification=effector.classification,
        confidence_score=effector.confidence_score,
        classification_reasons=effector.classification_reasons,
        pipeline_status=effector.pipeline_status,
        pipeline_started_at=effector.pipeline_started_at,
        pipeline_completed_at=effector.pipeline_completed_at,
        has_signal_peptide=effector.has_signal_peptide,
        signalp_probability=effector.signalp_probability,
        signal_peptide_end=effector.signal_peptide_end,
        tmhmm_domains=effector.tmhmm_domains,
        tmhmm_topology=effector.tmhmm_topology,
        effectorp_score=effector.effectorp_score,
        effectorp_prediction=effector.effectorp_prediction,
        deepredeff_score=effector.deepredeff_score,
        deepredeff_prediction=effector.deepredeff_prediction,
        phibase_hit=effector.phibase_hit,
        phibase_id=effector.phibase_id,
        phibase_phenotype=effector.phibase_phenotype,
        created_at=effector.created_at,
        updated_at=effector.updated_at,
    )


# ========================================
# STATISTICS
# ========================================

@router.get(
    "/stats/summary",
    response_model=EffectorStatistics,
    summary="Estatísticas de efetores",
    description="Retorna estatísticas gerais das predições."
)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Estatísticas das predições de efetores:
    - Total por classificação
    - Média de scores
    - Proteínas secretadas
    - Matches no PHI-base
    """
    service = EffectorService(db)
    return await service.get_statistics()


# ========================================
# DELETE
# ========================================

@router.delete(
    "/{effector_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar efetor",
    description="Remove uma predição de efetor."
)
async def delete_effector(
    effector_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Deleta uma predição de efetor.

    A sequência original NÃO é deletada, apenas a predição.
    """
    service = EffectorService(db)
    effector = await service.get_by_id(effector_id)

    if not effector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Effector {effector_id} não encontrado"
        )

    await db.delete(effector)
    await db.flush()

    return None
