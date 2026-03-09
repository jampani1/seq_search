"""
Models - Definições das tabelas do banco de dados
=================================================

Cada model representa uma tabela no PostgreSQL.
Usamos SQLAlchemy 2.0 com tipagem moderna.
"""

from app.models.sequence import Sequence, SequenceType
from app.models.blast_job import BlastJob, JobStatus, BlastProgram
from app.models.effector import Effector, EffectorClassification, PipelineStatus
from app.models.gene_network import GeneNetwork, NetworkStatus, InferenceMethod

__all__ = [
    "Sequence",
    "SequenceType",
    "BlastJob",
    "JobStatus",
    "BlastProgram",
    "Effector",
    "EffectorClassification",
    "PipelineStatus",
    "GeneNetwork",
    "NetworkStatus",
    "InferenceMethod",
]
