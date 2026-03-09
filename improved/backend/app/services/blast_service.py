"""
Service: BLAST
===============

Business logic para execução de BLAST/DIAMOND.

DECISÕES TÉCNICAS:
------------------
1. Execução assíncrona:
   - Jobs são submetidos e processados em background
   - Usa subprocess para chamar BLAST/DIAMOND CLI
   - Resultados parseados de XML para JSON

2. Parsing de resultados:
   - BLAST output em formato XML (-outfmt 5)
   - Parseado para estrutura JSON padronizada
   - Permite consultas rápidas no frontend

3. Gerenciamento de bancos:
   - Lista bancos disponíveis em /databases/blast/
   - Suporta múltiplos organismos

4. Queue com Redis (futuro):
   - Jobs ficam em fila quando muitos usuários
   - Worker separado processa jobs
"""

import asyncio
import subprocess
import tempfile
import os
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blast_job import BlastJob, JobStatus, BlastProgram
from app.models.sequence import Sequence
from app.schemas.blast import (
    BlastRequest,
    BlastJobResponse,
    BlastResultResponse,
    BlastHit,
    BlastHSP,
    BlastDatabase,
)
from app.config import settings


class BlastService:
    """
    Serviço para operações BLAST/DIAMOND.
    """

    # Diretório base para bancos de dados
    BLAST_DB_DIR = Path("/app/databases/blast")
    DIAMOND_DB_DIR = Path("/app/databases/diamond")

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================
    # JOB MANAGEMENT
    # ========================================

    async def submit_job(self, request: BlastRequest) -> BlastJob:
        """
        Submete um novo job BLAST.

        Args:
            request: Parâmetros do BLAST

        Returns:
            BlastJob criado (status PENDING)
        """
        # Gerar UUID
        job_uuid = str(uuid.uuid4())

        # Obter sequência
        query_content = request.sequence
        query_name = request.sequence_name

        if request.sequence_id:
            sequence = await self._get_sequence(request.sequence_id)
            if sequence:
                query_content = sequence.content
                query_name = query_name or sequence.name

        # Criar job
        job = BlastJob(
            job_uuid=job_uuid,
            query_sequence_id=request.sequence_id,
            query_content=query_content,
            query_name=query_name,
            program=request.program,
            database=request.database,
            evalue=request.evalue,
            max_hits=request.max_hits,
            parameters={
                "word_size": request.word_size,
                "gap_open": request.gap_open,
                "gap_extend": request.gap_extend,
                "matrix": request.matrix,
            },
            status=JobStatus.PENDING,
        )

        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)

        return job

    async def get_job(self, job_uuid: str) -> Optional[BlastJob]:
        """
        Busca um job pelo UUID.
        """
        result = await self.db.execute(
            select(BlastJob).where(BlastJob.job_uuid == job_uuid)
        )
        return result.scalar_one_or_none()

    async def get_job_status(self, job_uuid: str) -> Optional[BlastJobResponse]:
        """
        Retorna o status de um job.
        """
        job = await self.get_job(job_uuid)
        if not job:
            return None

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

    async def get_job_results(self, job_uuid: str) -> Optional[BlastResultResponse]:
        """
        Retorna os resultados completos de um job.
        """
        job = await self.get_job(job_uuid)
        if not job:
            return None

        if job.status != JobStatus.COMPLETED:
            return None

        # Converter resultados JSON para schema
        results = job.results or {}

        hits = []
        for hit_data in results.get("hits", []):
            hsps = [
                BlastHSP(**hsp_data)
                for hsp_data in hit_data.get("hsps", [])
            ]
            hit = BlastHit(
                hit_num=hit_data.get("hit_num", 0),
                hit_id=hit_data.get("hit_id", ""),
                hit_def=hit_data.get("hit_def", ""),
                hit_accession=hit_data.get("hit_accession"),
                hit_len=hit_data.get("hit_len", 0),
                best_evalue=hit_data.get("best_evalue", 0),
                best_bit_score=hit_data.get("best_bit_score", 0),
                best_identity_percent=hit_data.get("best_identity_percent", 0),
                hsps=hsps,
            )
            hits.append(hit)

        return BlastResultResponse(
            job_id=job.job_uuid,
            status=job.status,
            query_id=results.get("query_id"),
            query_def=results.get("query_def"),
            query_len=results.get("query_len"),
            database=job.database,
            database_sequences=results.get("database_sequences"),
            database_letters=results.get("database_letters"),
            program=job.program,
            evalue_threshold=job.evalue,
            hits_count=job.hits_count or 0,
            hits=hits,
            created_at=job.created_at,
            completed_at=job.completed_at,
            duration_seconds=job.duration_seconds,
        )

    # ========================================
    # JOB EXECUTION
    # ========================================

    async def run_job(self, job_uuid: str) -> bool:
        """
        Executa um job BLAST.

        Chamado pelo worker ou diretamente para processamento síncrono.

        Args:
            job_uuid: UUID do job

        Returns:
            True se executou com sucesso
        """
        job = await self.get_job(job_uuid)
        if not job:
            return False

        # Marcar como running
        job.mark_running()
        await self.db.flush()

        try:
            # Executar BLAST/DIAMOND
            if job.program == BlastProgram.DIAMOND:
                results = await self._run_diamond(job)
            else:
                results = await self._run_blast(job)

            # Marcar como concluído
            hits_count = len(results.get("hits", []))
            job.mark_completed(hits_count, results)
            await self.db.flush()

            return True

        except Exception as e:
            # Marcar como falho
            job.mark_failed(str(e))
            await self.db.flush()
            return False

    async def _run_blast(self, job: BlastJob) -> Dict[str, Any]:
        """
        Executa BLAST+ via subprocess.
        """
        # Criar arquivo temporário com a query
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fasta", delete=False
        ) as query_file:
            query_file.write(f">{job.query_name or 'query'}\n")
            query_file.write(job.query_content)
            query_path = query_file.name

        # Arquivo de output
        output_path = tempfile.mktemp(suffix=".xml")

        try:
            # Construir comando BLAST
            db_path = self.BLAST_DB_DIR / job.database

            cmd = [
                job.program.value,  # blastp, blastn, etc.
                "-query", query_path,
                "-db", str(db_path),
                "-out", output_path,
                "-outfmt", "5",  # XML format
                "-evalue", str(job.evalue),
                "-max_target_seqs", str(job.max_hits),
            ]

            # Adicionar parâmetros opcionais
            params = job.parameters or {}
            if params.get("word_size"):
                cmd.extend(["-word_size", str(params["word_size"])])
            if params.get("gap_open"):
                cmd.extend(["-gapopen", str(params["gap_open"])])
            if params.get("gap_extend"):
                cmd.extend(["-gapextend", str(params["gap_extend"])])
            if params.get("matrix"):
                cmd.extend(["-matrix", params["matrix"]])

            # Executar
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"BLAST failed: {stderr.decode()}")

            # Parsear XML
            results = self._parse_blast_xml(output_path)
            return results

        finally:
            # Limpar arquivos temporários
            if os.path.exists(query_path):
                os.unlink(query_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    async def _run_diamond(self, job: BlastJob) -> Dict[str, Any]:
        """
        Executa DIAMOND via subprocess.

        DIAMOND é mais rápido que BLASTP para grandes bancos.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fasta", delete=False
        ) as query_file:
            query_file.write(f">{job.query_name or 'query'}\n")
            query_file.write(job.query_content)
            query_path = query_file.name

        output_path = tempfile.mktemp(suffix=".tsv")

        try:
            db_path = self.DIAMOND_DB_DIR / f"{job.database}.dmnd"

            cmd = [
                "diamond", "blastp",
                "-q", query_path,
                "-d", str(db_path),
                "-o", output_path,
                "-e", str(job.evalue),
                "-k", str(job.max_hits),
                "--outfmt", "6", "qseqid", "sseqid", "pident", "length",
                "mismatch", "gapopen", "qstart", "qend", "sstart", "send",
                "evalue", "bitscore", "stitle",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"DIAMOND failed: {stderr.decode()}")

            # Parsear TSV
            results = self._parse_diamond_tsv(output_path, job.query_name)
            return results

        finally:
            if os.path.exists(query_path):
                os.unlink(query_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    # ========================================
    # PARSING
    # ========================================

    def _parse_blast_xml(self, xml_path: str) -> Dict[str, Any]:
        """
        Parseia output XML do BLAST.
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Informações da query
        iteration = root.find(".//Iteration")

        results = {
            "query_id": self._get_text(iteration, "Iteration_query-ID"),
            "query_def": self._get_text(iteration, "Iteration_query-def"),
            "query_len": self._get_int(iteration, "Iteration_query-len"),
            "hits": [],
        }

        # Parsear hits
        for hit_num, hit_elem in enumerate(root.findall(".//Hit"), 1):
            hit = self._parse_blast_hit(hit_elem, hit_num)
            results["hits"].append(hit)

        return results

    def _parse_blast_hit(self, hit_elem: ET.Element, hit_num: int) -> Dict[str, Any]:
        """
        Parseia um hit do BLAST XML.
        """
        hit = {
            "hit_num": hit_num,
            "hit_id": self._get_text(hit_elem, "Hit_id"),
            "hit_def": self._get_text(hit_elem, "Hit_def"),
            "hit_accession": self._get_text(hit_elem, "Hit_accession"),
            "hit_len": self._get_int(hit_elem, "Hit_len"),
            "hsps": [],
        }

        best_evalue = float("inf")
        best_bit_score = 0
        best_identity = 0

        # Parsear HSPs
        for hsp_num, hsp_elem in enumerate(hit_elem.findall(".//Hsp"), 1):
            hsp = self._parse_blast_hsp(hsp_elem, hsp_num)
            hit["hsps"].append(hsp)

            # Track best values
            if hsp["evalue"] < best_evalue:
                best_evalue = hsp["evalue"]
            if hsp["bit_score"] > best_bit_score:
                best_bit_score = hsp["bit_score"]
            if hsp["identity_percent"] > best_identity:
                best_identity = hsp["identity_percent"]

        hit["best_evalue"] = best_evalue
        hit["best_bit_score"] = best_bit_score
        hit["best_identity_percent"] = best_identity

        return hit

    def _parse_blast_hsp(self, hsp_elem: ET.Element, hsp_num: int) -> Dict[str, Any]:
        """
        Parseia um HSP do BLAST XML.
        """
        identity = self._get_int(hsp_elem, "Hsp_identity")
        align_len = self._get_int(hsp_elem, "Hsp_align-len")

        return {
            "hsp_num": hsp_num,
            "bit_score": self._get_float(hsp_elem, "Hsp_bit-score"),
            "score": self._get_int(hsp_elem, "Hsp_score"),
            "evalue": self._get_float(hsp_elem, "Hsp_evalue"),
            "query_from": self._get_int(hsp_elem, "Hsp_query-from"),
            "query_to": self._get_int(hsp_elem, "Hsp_query-to"),
            "hit_from": self._get_int(hsp_elem, "Hsp_hit-from"),
            "hit_to": self._get_int(hsp_elem, "Hsp_hit-to"),
            "identity": identity,
            "identity_percent": (identity / align_len * 100) if align_len > 0 else 0,
            "positive": self._get_int(hsp_elem, "Hsp_positive"),
            "gaps": self._get_int(hsp_elem, "Hsp_gaps"),
            "align_len": align_len,
            "query_seq": self._get_text(hsp_elem, "Hsp_qseq"),
            "hit_seq": self._get_text(hsp_elem, "Hsp_hseq"),
            "midline": self._get_text(hsp_elem, "Hsp_midline"),
        }

    def _parse_diamond_tsv(
        self, tsv_path: str, query_name: Optional[str]
    ) -> Dict[str, Any]:
        """
        Parseia output TSV do DIAMOND.
        """
        results = {
            "query_id": query_name or "query",
            "query_def": query_name,
            "hits": [],
        }

        hits_dict = {}  # Group by subject ID

        with open(tsv_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                parts = line.strip().split("\t")
                if len(parts) < 12:
                    continue

                sseqid = parts[1]
                pident = float(parts[2])
                length = int(parts[3])
                mismatch = int(parts[4])
                gapopen = int(parts[5])
                qstart = int(parts[6])
                qend = int(parts[7])
                sstart = int(parts[8])
                send = int(parts[9])
                evalue = float(parts[10])
                bitscore = float(parts[11])
                stitle = parts[12] if len(parts) > 12 else sseqid

                # Create or update hit
                if sseqid not in hits_dict:
                    hits_dict[sseqid] = {
                        "hit_num": len(hits_dict) + 1,
                        "hit_id": sseqid,
                        "hit_def": stitle,
                        "hit_accession": sseqid.split("|")[0] if "|" in sseqid else sseqid,
                        "hit_len": 0,  # Not available in this format
                        "best_evalue": evalue,
                        "best_bit_score": bitscore,
                        "best_identity_percent": pident,
                        "hsps": [],
                    }

                hit = hits_dict[sseqid]

                # Add HSP
                hsp = {
                    "hsp_num": len(hit["hsps"]) + 1,
                    "bit_score": bitscore,
                    "score": int(bitscore),  # Approximate
                    "evalue": evalue,
                    "query_from": qstart,
                    "query_to": qend,
                    "hit_from": sstart,
                    "hit_to": send,
                    "identity": int(length * pident / 100),
                    "identity_percent": pident,
                    "positive": int(length * pident / 100),  # Approximate
                    "gaps": gapopen,
                    "align_len": length,
                    "query_seq": None,
                    "hit_seq": None,
                    "midline": None,
                }
                hit["hsps"].append(hsp)

                # Update best values
                if evalue < hit["best_evalue"]:
                    hit["best_evalue"] = evalue
                if bitscore > hit["best_bit_score"]:
                    hit["best_bit_score"] = bitscore
                if pident > hit["best_identity_percent"]:
                    hit["best_identity_percent"] = pident

        results["hits"] = list(hits_dict.values())
        return results

    # ========================================
    # DATABASE MANAGEMENT
    # ========================================

    async def list_databases(self) -> List[BlastDatabase]:
        """
        Lista bancos de dados BLAST disponíveis.
        """
        databases = []

        # BLAST databases
        if self.BLAST_DB_DIR.exists():
            for db_file in self.BLAST_DB_DIR.glob("*.pin"):
                db_name = db_file.stem
                databases.append(BlastDatabase(
                    name=db_name,
                    description=f"BLAST protein database: {db_name}",
                    db_type="prot",
                ))

            for db_file in self.BLAST_DB_DIR.glob("*.nin"):
                db_name = db_file.stem
                databases.append(BlastDatabase(
                    name=db_name,
                    description=f"BLAST nucleotide database: {db_name}",
                    db_type="nucl",
                ))

        # DIAMOND databases
        if self.DIAMOND_DB_DIR.exists():
            for db_file in self.DIAMOND_DB_DIR.glob("*.dmnd"):
                db_name = db_file.stem
                databases.append(BlastDatabase(
                    name=db_name,
                    description=f"DIAMOND database: {db_name}",
                    db_type="prot",
                ))

        return databases

    # ========================================
    # HELPERS
    # ========================================

    async def _get_sequence(self, sequence_id: int) -> Optional[Sequence]:
        """
        Busca uma sequência pelo ID.
        """
        result = await self.db.execute(
            select(Sequence).where(Sequence.id == sequence_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _get_text(elem: ET.Element, tag: str) -> Optional[str]:
        """Helper para extrair texto de XML."""
        child = elem.find(tag) if elem is not None else None
        return child.text if child is not None else None

    @staticmethod
    def _get_int(elem: ET.Element, tag: str) -> int:
        """Helper para extrair inteiro de XML."""
        text = BlastService._get_text(elem, tag)
        return int(text) if text else 0

    @staticmethod
    def _get_float(elem: ET.Element, tag: str) -> float:
        """Helper para extrair float de XML."""
        text = BlastService._get_text(elem, tag)
        return float(text) if text else 0.0
