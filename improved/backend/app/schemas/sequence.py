"""
Schemas: Sequence
=================

Pydantic schemas para validação de sequências biológicas.

DECISÕES TÉCNICAS:
------------------
1. Separação de schemas por operação:
   - Create: campos obrigatórios para criar
   - Update: campos opcionais para atualizar
   - Response: campos retornados ao cliente

2. Validadores customizados:
   - Verifica se sequência contém apenas caracteres válidos
   - Calcula comprimento automaticamente
   - Detecta tipo de sequência se não especificado

3. Configurações de Pydantic v2:
   - model_config ao invés de class Config
   - from_attributes para converter de ORM
"""

import re
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.sequence import SequenceType


# ========================================
# CONSTANTES DE VALIDAÇÃO
# ========================================

# Caracteres válidos por tipo de sequência
VALID_DNA_CHARS = set("ATCGN")
VALID_RNA_CHARS = set("AUCGN")
VALID_PROTEIN_CHARS = set("ACDEFGHIKLMNPQRSTVWYX*")


# ========================================
# BASE SCHEMA
# ========================================

class SequenceBase(BaseModel):
    """
    Campos compartilhados entre todos os schemas de Sequence.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nome/identificador da sequência",
        examples=["COX1_Ntropicalis", "effector_NtEC05"]
    )

    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Descrição da sequência (header FASTA)",
        examples=["Cytochrome c oxidase subunit 1"]
    )

    sequence_type: SequenceType = Field(
        ...,
        description="Tipo da sequência: dna, rna ou protein"
    )

    content: str = Field(
        ...,
        min_length=1,
        description="Sequência de nucleotídeos ou aminoácidos"
    )

    organism: Optional[str] = Field(
        None,
        max_length=255,
        description="Organismo de origem",
        examples=["Neophysopella tropicalis"]
    )

    source: Optional[str] = Field(
        None,
        max_length=100,
        description="Fonte dos dados",
        examples=["upload", "NCBI", "MFannot"]
    )


# ========================================
# CREATE SCHEMA
# ========================================

class SequenceCreate(SequenceBase):
    """
    Schema para criar uma nova sequência.

    Inclui validações rigorosas para garantir dados corretos.
    """

    @field_validator("content")
    @classmethod
    def clean_content(cls, v: str) -> str:
        """
        Limpa e normaliza o conteúdo da sequência.

        - Remove espaços e quebras de linha
        - Converte para maiúsculo
        - Remove caracteres especiais (exceto os válidos)
        """
        # Remove espaços, tabs, quebras de linha
        v = re.sub(r"\s+", "", v)
        # Converte para maiúsculo
        v = v.upper()
        return v

    @model_validator(mode="after")
    def validate_sequence_content(self) -> "SequenceCreate":
        """
        Valida se o conteúdo corresponde ao tipo declarado.
        """
        content = self.content

        if self.sequence_type == SequenceType.DNA:
            valid_chars = VALID_DNA_CHARS
            type_name = "DNA"
        elif self.sequence_type == SequenceType.RNA:
            valid_chars = VALID_RNA_CHARS
            type_name = "RNA"
        elif self.sequence_type == SequenceType.PROTEIN:
            valid_chars = VALID_PROTEIN_CHARS
            type_name = "proteína"
        else:
            raise ValueError(f"Tipo de sequência inválido: {self.sequence_type}")

        # Encontra caracteres inválidos
        invalid_chars = set(content) - valid_chars
        if invalid_chars:
            raise ValueError(
                f"Sequência de {type_name} contém caracteres inválidos: {invalid_chars}. "
                f"Caracteres permitidos: {sorted(valid_chars)}"
            )

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "COX1_Ntropicalis",
                    "description": "Cytochrome c oxidase subunit 1 - mitochondrial",
                    "sequence_type": "protein",
                    "content": "MFINRWLFSTNHKDIGTLYLIFGAWAGMVGTAL",
                    "organism": "Neophysopella tropicalis",
                    "source": "MFannot"
                }
            ]
        }
    }


# ========================================
# UPDATE SCHEMA
# ========================================

class SequenceUpdate(BaseModel):
    """
    Schema para atualizar uma sequência existente.

    Todos os campos são opcionais - apenas os fornecidos serão atualizados.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    organism: Optional[str] = Field(None, max_length=255)
    source: Optional[str] = Field(None, max_length=100)

    # NOTA: Não permitimos atualizar content ou sequence_type
    # pois isso poderia corromper dados relacionados (efetores, BLAST, etc.)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "COX1_Ntropicalis_v2",
                    "organism": "Neophysopella tropicalis (isolate BR)"
                }
            ]
        }
    }


# ========================================
# RESPONSE SCHEMAS
# ========================================

class SequenceResponse(SequenceBase):
    """
    Schema de resposta para uma sequência.

    Inclui campos gerados pelo sistema (id, timestamps, length).
    """
    id: int = Field(..., description="ID único da sequência")
    length: int = Field(..., description="Comprimento da sequência")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data da última atualização")

    model_config = {
        # Permite criar a partir de objetos ORM (SQLAlchemy)
        "from_attributes": True,
    }


class SequenceListResponse(BaseModel):
    """
    Schema para listagem de sequências com paginação.
    """
    items: List[SequenceResponse] = Field(..., description="Lista de sequências")
    total: int = Field(..., description="Total de sequências no banco")
    page: int = Field(..., description="Página atual")
    page_size: int = Field(..., description="Itens por página")
    pages: int = Field(..., description="Total de páginas")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [],
                    "total": 100,
                    "page": 1,
                    "page_size": 20,
                    "pages": 5
                }
            ]
        }
    }


# ========================================
# UTILITY SCHEMAS
# ========================================

class SequenceTypeDetection(BaseModel):
    """
    Resposta da detecção automática de tipo de sequência.
    """
    detected_type: SequenceType
    confidence: float = Field(..., ge=0, le=1, description="Confiança da detecção (0-1)")
    length: int
    composition: dict = Field(..., description="Composição de caracteres")
