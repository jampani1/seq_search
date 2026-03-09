"""
Service: Effector
==================

Business logic para predição de efetores.

DECISÕES TÉCNICAS:
------------------
1. Pipeline Predector simplificado:
   - SignalP → TMHMM → EffectorP → DeepRedeff → PHI-base
   - Cada etapa é independente e pode falhar sem afetar outras
   - Resultados salvos incrementalmente

2. Ferramentas externas:
   - Chamadas via subprocess (CLI)
   - Em produção, usar containers Docker específicos
   - Fallback para versões web-based (SignalP 6.0 online)

3. PHI-base:
   - BLAST contra banco local
   - Download periódico do FASTA
   - Cache de resultados

4. Classificação:
   - Combinação de scores de múltiplas ferramentas
   - Thresholds configuráveis
   - Ranking por confiança
"""

import asyncio
import subprocess
import tempfile
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from math import ceil

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.effector import Effector, EffectorClassification, PipelineStatus
from app.models.sequence import Sequence, SequenceType
from app.schemas.effector import (
    EffectorPredictRequest,
    EffectorResponse,
    EffectorListResponse,
    EffectorSummary,
    EffectorStatistics,
)


class EffectorService:
    """
    Serviço para predição de efetores.
    """

    # Diretórios
    PHIBASE_DB = Path("/app/databases/phibase")
    TOOLS_DIR = Path("/app/tools")

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================
    # CRUD
    # ========================================

    async def get_by_id(self, effector_id: int) -> Optional[Effector]:
        """Busca effector por ID."""
        result = await self.db.execute(
            select(Effector)
            .options(joinedload(Effector.sequence))
            .where(Effector.id == effector_id)
        )
        return result.scalar_one_or_none()

    async def get_by_sequence_id(self, sequence_id: int) -> Optional[Effector]:
        """Busca effector pela sequência."""
        result = await self.db.execute(
            select(Effector)
            .options(joinedload(Effector.sequence))
            .where(Effector.sequence_id == sequence_id)
        )
        return result.scalar_one_or_none()

    async def list_effectors(
        self,
        page: int = 1,
        page_size: int = 20,
        classification: Optional[EffectorClassification] = None,
        min_score: Optional[float] = None,
        has_signal_peptide: Optional[bool] = None,
        has_phibase_match: Optional[bool] = None,
    ) -> EffectorListResponse:
        """Lista effectors com filtros e paginação."""
        query = select(Effector).options(joinedload(Effector.sequence))

        # Aplicar filtros
        if classification:
            query = query.where(Effector.classification == classification)

        if min_score is not None:
            query = query.where(Effector.effectorp_score >= min_score)

        if has_signal_peptide is not None:
            query = query.where(Effector.has_signal_peptide == has_signal_peptide)

        if has_phibase_match is not None:
            query = query.where(Effector.phibase_hit == has_phibase_match)

        # Contar total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Paginação e ordenação
        offset = (page - 1) * page_size
        query = (
            query
            .order_by(Effector.confidence_score.desc().nullslast())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        effectors = list(result.scalars().all())

        # Estatísticas por classificação
        stats_query = select(
            Effector.classification,
            func.count(Effector.id)
        ).group_by(Effector.classification)
        stats_result = await self.db.execute(stats_query)
        by_classification = {
            row.classification.value: row[1]
            for row in stats_result.all()
        }

        items = [
            EffectorSummary(
                id=e.id,
                sequence_id=e.sequence_id,
                sequence_name=e.sequence.name if e.sequence else None,
                classification=e.classification,
                confidence_score=e.confidence_score,
                pipeline_status=e.pipeline_status,
                effectorp_score=e.effectorp_score,
                has_signal_peptide=e.has_signal_peptide,
                phibase_hit=e.phibase_hit,
            )
            for e in effectors
        ]

        return EffectorListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=ceil(total / page_size) if total > 0 else 1,
            by_classification=by_classification,
        )

    async def get_statistics(self) -> EffectorStatistics:
        """Retorna estatísticas gerais."""
        # Total por classificação
        class_counts = {}
        for cls in EffectorClassification:
            result = await self.db.execute(
                select(func.count(Effector.id))
                .where(Effector.classification == cls)
            )
            class_counts[cls.value] = result.scalar_one()

        # Média de scores
        avg_result = await self.db.execute(
            select(func.avg(Effector.effectorp_score))
            .where(Effector.effectorp_score.isnot(None))
        )
        avg_score = avg_result.scalar_one()

        # Secretadas
        secreted_result = await self.db.execute(
            select(func.count(Effector.id))
            .where(
                Effector.has_signal_peptide == True,
                (Effector.tmhmm_domains == 0) | (Effector.tmhmm_domains.is_(None))
            )
        )
        secreted = secreted_result.scalar_one()

        # PHI-base matches
        phibase_result = await self.db.execute(
            select(func.count(Effector.id))
            .where(Effector.phibase_hit == True)
        )
        phibase_count = phibase_result.scalar_one()

        return EffectorStatistics(
            total_analyzed=sum(class_counts.values()),
            total_candidates=class_counts.get("candidate", 0),
            total_high_confidence=class_counts.get("high_confidence", 0),
            total_validated=class_counts.get("validated", 0),
            total_rejected=class_counts.get("rejected", 0),
            average_effectorp_score=round(avg_score, 3) if avg_score else None,
            secreted_proteins=secreted,
            with_phibase_match=phibase_count,
        )

    # ========================================
    # PIPELINE
    # ========================================

    async def predict(
        self,
        request: EffectorPredictRequest
    ) -> Effector:
        """
        Executa pipeline de predição para uma sequência.
        """
        # Verificar se sequência existe e é proteína
        sequence = await self._get_sequence(request.sequence_id)
        if not sequence:
            raise ValueError(f"Sequência {request.sequence_id} não encontrada")

        if sequence.sequence_type != SequenceType.PROTEIN:
            raise ValueError(
                f"Predição de efetores requer proteína, "
                f"mas sequência é {sequence.sequence_type.value}"
            )

        # Verificar se já existe effector
        effector = await self.get_by_sequence_id(request.sequence_id)

        if effector:
            # Já existe, atualizar
            effector.pipeline_status = PipelineStatus.RUNNING
            effector.pipeline_started_at = datetime.utcnow()
        else:
            # Criar novo
            effector = Effector(
                sequence_id=request.sequence_id,
                pipeline_status=PipelineStatus.RUNNING,
                pipeline_started_at=datetime.utcnow(),
            )
            self.db.add(effector)

        await self.db.flush()

        # Executar cada etapa do pipeline
        try:
            if request.run_signalp:
                await self._run_signalp(effector, sequence)

            if request.run_tmhmm:
                await self._run_tmhmm(effector, sequence)

            if request.run_effectorp:
                await self._run_effectorp(effector, sequence)

            if request.run_deepredeff:
                await self._run_deepredeff(effector, sequence)

            if request.run_phibase:
                await self._run_phibase(effector, sequence, request.phibase_evalue)

            # Classificar
            effector.confidence_score = effector.calculate_confidence()
            effector.classification = effector.classify()
            effector.classification_reasons = self._build_reasons(effector)

            effector.pipeline_status = PipelineStatus.COMPLETED
            effector.pipeline_completed_at = datetime.utcnow()

        except Exception as e:
            effector.pipeline_status = PipelineStatus.FAILED
            effector.classification_reasons = {"error": str(e)}

        await self.db.flush()
        await self.db.refresh(effector)

        return effector

    # ========================================
    # PIPELINE STEPS
    # ========================================

    async def _run_signalp(self, effector: Effector, sequence: Sequence) -> None:
        """
        Executa SignalP para detectar peptídeo sinal.

        SignalP 6.0 detecta diferentes tipos de peptídeos sinal:
        - Sec/SPI: via pathway Sec (maioria dos efetores)
        - Tat/SPI: via pathway Tat
        - Sec/SPII: lipoproteínas
        """
        effector.signalp_status = PipelineStatus.RUNNING
        await self.db.flush()

        try:
            # Em desenvolvimento: simulação
            # Em produção: chamar signalp CLI ou API
            result = await self._simulate_signalp(sequence.content)

            effector.has_signal_peptide = result["has_signal"]
            effector.signalp_probability = result["probability"]
            effector.signal_peptide_start = result.get("start", 1)
            effector.signal_peptide_end = result.get("end")

            effector.signalp_status = PipelineStatus.COMPLETED

        except Exception as e:
            effector.signalp_status = PipelineStatus.FAILED
            raise

    async def _run_tmhmm(self, effector: Effector, sequence: Sequence) -> None:
        """
        Executa TMHMM para detectar domínios transmembrana.

        Efetores secretados não devem ter domínios TM
        (exceto possivelmente 1 na região do peptídeo sinal).
        """
        effector.tmhmm_status = PipelineStatus.RUNNING
        await self.db.flush()

        try:
            result = await self._simulate_tmhmm(sequence.content)

            effector.tmhmm_domains = result["num_domains"]
            effector.tmhmm_topology = result.get("topology")

            effector.tmhmm_status = PipelineStatus.COMPLETED

        except Exception as e:
            effector.tmhmm_status = PipelineStatus.FAILED
            raise

    async def _run_effectorp(self, effector: Effector, sequence: Sequence) -> None:
        """
        Executa EffectorP para predição principal.

        EffectorP 3.0 usa machine learning para prever
        se uma proteína é um efetor fúngico.
        """
        effector.effectorp_status = PipelineStatus.RUNNING
        await self.db.flush()

        try:
            result = await self._simulate_effectorp(sequence.content)

            effector.effectorp_score = result["score"]
            effector.effectorp_prediction = result["prediction"]
            effector.effectorp_version = result.get("version", "3.0")

            effector.effectorp_status = PipelineStatus.COMPLETED

        except Exception as e:
            effector.effectorp_status = PipelineStatus.FAILED
            raise

    async def _run_deepredeff(self, effector: Effector, sequence: Sequence) -> None:
        """
        Executa DeepRedeff para validação.

        DeepRedeff usa deep learning e é especialmente bom
        para efetores de oomicetos.
        """
        effector.deepredeff_status = PipelineStatus.RUNNING
        await self.db.flush()

        try:
            result = await self._simulate_deepredeff(sequence.content)

            effector.deepredeff_score = result["score"]
            effector.deepredeff_prediction = result["prediction"]

            effector.deepredeff_status = PipelineStatus.COMPLETED

        except Exception as e:
            effector.deepredeff_status = PipelineStatus.FAILED
            raise

    async def _run_phibase(
        self,
        effector: Effector,
        sequence: Sequence,
        evalue: float
    ) -> None:
        """
        Busca no PHI-base (efetores conhecidos).
        """
        effector.phibase_status = PipelineStatus.RUNNING
        await self.db.flush()

        try:
            result = await self._simulate_phibase(sequence.content, evalue)

            effector.phibase_hit = result["has_match"]
            if result["has_match"]:
                effector.phibase_id = result.get("phi_id")
                effector.phibase_evalue = result.get("evalue")
                effector.phibase_identity = result.get("identity")
                effector.phibase_phenotype = result.get("phenotype")

            effector.phibase_status = PipelineStatus.COMPLETED

        except Exception as e:
            effector.phibase_status = PipelineStatus.FAILED
            raise

    # ========================================
    # SIMULAÇÕES (desenvolvimento)
    # ========================================
    # Em produção, substituir por chamadas reais

    async def _simulate_signalp(self, sequence: str) -> Dict[str, Any]:
        """
        Simula SignalP baseado em características da sequência.

        Heurísticas simples:
        - Começa com M (metionina)
        - Região hidrofóbica nos primeiros 30aa
        - Região polar antes do cleavage
        """
        await asyncio.sleep(0.1)  # Simular processamento

        # Heurísticas básicas
        has_m_start = sequence.upper().startswith("M")

        # Calcular hidrofobicidade dos primeiros 30aa
        hydrophobic = set("AILMFVW")
        first_30 = sequence[:30].upper()
        hydro_count = sum(1 for aa in first_30 if aa in hydrophobic)
        hydro_ratio = hydro_count / len(first_30) if first_30 else 0

        # Simular probabilidade
        if has_m_start and hydro_ratio > 0.3:
            prob = min(0.5 + hydro_ratio, 0.95)
            return {
                "has_signal": True,
                "probability": round(prob, 3),
                "start": 1,
                "end": min(25, len(sequence)),
            }
        else:
            return {
                "has_signal": False,
                "probability": round(hydro_ratio, 3),
            }

    async def _simulate_tmhmm(self, sequence: str) -> Dict[str, Any]:
        """
        Simula TMHMM baseado em regiões hidrofóbicas.
        """
        await asyncio.sleep(0.1)

        # Janela deslizante para encontrar regiões hidrofóbicas
        hydrophobic = set("AILMFVWP")
        window_size = 20
        threshold = 0.7
        tm_domains = 0

        for i in range(len(sequence) - window_size):
            window = sequence[i:i + window_size].upper()
            hydro_ratio = sum(1 for aa in window if aa in hydrophobic) / window_size
            if hydro_ratio > threshold:
                tm_domains += 1
                # Skip para não contar a mesma região duas vezes
                i += window_size

        return {
            "num_domains": min(tm_domains, 5),  # Cap em 5
            "topology": "o" if tm_domains == 0 else f"i{'M' * tm_domains}o",
        }

    async def _simulate_effectorp(self, sequence: str) -> Dict[str, Any]:
        """
        Simula EffectorP baseado em características de efetores.

        Características típicas de efetores:
        - Pequenos (< 300 aa)
        - Ricos em cisteína
        - Poucos resíduos carregados
        """
        await asyncio.sleep(0.2)

        length = len(sequence)
        seq_upper = sequence.upper()

        # Características
        is_small = length < 300
        cysteine_count = seq_upper.count("C")
        cysteine_rich = cysteine_count > length * 0.02

        charged = set("DEKRH")
        charged_count = sum(1 for aa in seq_upper if aa in charged)
        low_charge = charged_count < length * 0.15

        # Calcular score
        score = 0.3  # Base
        if is_small:
            score += 0.2
        if cysteine_rich:
            score += 0.2
        if low_charge:
            score += 0.15

        # Adicionar ruído
        import random
        score += random.uniform(-0.1, 0.1)
        score = max(0, min(1, score))

        return {
            "score": round(score, 3),
            "prediction": "effector" if score > 0.5 else "non-effector",
            "version": "3.0-simulated",
        }

    async def _simulate_deepredeff(self, sequence: str) -> Dict[str, Any]:
        """Simula DeepRedeff."""
        await asyncio.sleep(0.2)

        # Similar ao EffectorP mas com características diferentes
        import random
        base_score = random.uniform(0.3, 0.7)

        # Ajustar por tamanho
        if len(sequence) < 250:
            base_score += 0.1
        if len(sequence) < 150:
            base_score += 0.1

        score = max(0, min(1, base_score))

        return {
            "score": round(score, 3),
            "prediction": "effector" if score > 0.5 else "non-effector",
        }

    async def _simulate_phibase(
        self,
        sequence: str,
        evalue: float
    ) -> Dict[str, Any]:
        """Simula busca no PHI-base."""
        await asyncio.sleep(0.3)

        # Simular 20% de chance de match
        import random
        has_match = random.random() < 0.2

        if has_match:
            return {
                "has_match": True,
                "phi_id": f"PHI:{random.randint(1000, 9999)}",
                "evalue": round(random.uniform(1e-50, 1e-10), 2),
                "identity": round(random.uniform(30, 99), 1),
                "phenotype": random.choice([
                    "reduced_virulence",
                    "loss_of_pathogenicity",
                    "increased_virulence",
                    "effector",
                ]),
            }
        else:
            return {"has_match": False}

    # ========================================
    # HELPERS
    # ========================================

    async def _get_sequence(self, sequence_id: int) -> Optional[Sequence]:
        """Busca sequência por ID."""
        result = await self.db.execute(
            select(Sequence).where(Sequence.id == sequence_id)
        )
        return result.scalar_one_or_none()

    def _build_reasons(self, effector: Effector) -> Dict[str, Any]:
        """Constrói razões para a classificação."""
        reasons = {
            "has_signal_peptide": effector.has_signal_peptide,
            "tm_domains": effector.tmhmm_domains,
            "is_secreted": effector.is_secreted,
            "effectorp_score": effector.effectorp_score,
            "deepredeff_score": effector.deepredeff_score,
            "phibase_match": effector.phibase_hit,
        }

        # Adicionar explicação textual
        if effector.classification == EffectorClassification.REJECTED:
            if not effector.has_signal_peptide:
                reasons["rejection_reason"] = "Sem peptídeo sinal"
            elif effector.tmhmm_domains and effector.tmhmm_domains > 1:
                reasons["rejection_reason"] = "Múltiplos domínios transmembrana"
            else:
                reasons["rejection_reason"] = "Score EffectorP baixo"

        elif effector.classification == EffectorClassification.VALIDATED:
            reasons["validation_reason"] = f"Match no PHI-base: {effector.phibase_id}"

        elif effector.classification == EffectorClassification.HIGH_CONFIDENCE:
            reasons["confidence_reason"] = (
                f"EffectorP: {effector.effectorp_score:.2f}, "
                f"DeepRedeff: {effector.deepredeff_score:.2f}"
            )

        return reasons
