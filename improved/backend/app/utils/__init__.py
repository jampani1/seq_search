"""
Utils - Utilitários e Helpers
==============================

Funções auxiliares usadas em todo o projeto.

Inclui:
- Parsers de arquivos (FASTA, GFF, etc.)
- Detecção de tipo de sequência
- Formatação de dados
"""

from app.utils.parsers import parse_fasta, detect_sequence_type

__all__ = ["parse_fasta", "detect_sequence_type"]
