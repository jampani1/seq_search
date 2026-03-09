"""
Parsers: FASTA e formatos bioinformáticos
==========================================

Funções para parsear arquivos de sequências biológicas.

DECISÕES TÉCNICAS:
------------------
1. Parser FASTA simples e eficiente:
   - Não usa BioPython para evitar dependência pesada
   - Suporta sequências multilinhas
   - Extrai nome e descrição do header

2. Detecção automática de tipo:
   - Analisa composição de caracteres
   - DNA: predominantemente A, T, C, G
   - RNA: tem U ao invés de T
   - Proteína: tem aminoácidos que não existem em DNA/RNA

3. Validação:
   - Remove caracteres inválidos
   - Converte para maiúsculo
   - Valida formato do header
"""

import re
from typing import List, Dict, Tuple, Optional
from collections import Counter

from app.models.sequence import SequenceType


# ========================================
# CONSTANTES
# ========================================

# Caracteres válidos por tipo
DNA_CHARS = set("ATCGN")
RNA_CHARS = set("AUCGN")
# Aminoácidos + X (unknown) + * (stop codon)
PROTEIN_CHARS = set("ACDEFGHIKLMNPQRSTVWYX*")

# Aminoácidos exclusivos (não aparecem em DNA/RNA)
PROTEIN_ONLY_CHARS = set("DEFHIKLMPQRSVWY")


# ========================================
# PARSER FASTA
# ========================================

def parse_fasta(content: str) -> List[Dict]:
    """
    Faz parsing de conteúdo FASTA.

    Formato FASTA:
    ```
    >nome_sequencia descrição opcional aqui
    ATCGATCGATCGATCG
    ATCGATCGATCGATCG
    >outra_sequencia
    MFINRWLFSTNHKDIG
    ```

    Args:
        content: Conteúdo do arquivo FASTA como string

    Returns:
        Lista de dicionários com:
        - name: Nome da sequência (até primeiro espaço)
        - description: Descrição (resto do header)
        - content: Sequência (sem espaços/quebras)
        - sequence_type: Tipo detectado automaticamente

    Raises:
        ValueError: Se o formato for inválido
    """
    sequences = []
    current_name = None
    current_description = None
    current_content = []

    lines = content.strip().split("\n")

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Ignorar linhas vazias
        if not line:
            continue

        # Linha de header
        if line.startswith(">"):
            # Salvar sequência anterior (se existir)
            if current_name is not None:
                if not current_content:
                    raise ValueError(
                        f"Sequência '{current_name}' está vazia"
                    )
                sequences.append(_build_sequence_dict(
                    current_name,
                    current_description,
                    "".join(current_content)
                ))

            # Parsear novo header
            header = line[1:].strip()
            if not header:
                raise ValueError(
                    f"Linha {line_num}: Header vazio (apenas '>')"
                )

            # Separar nome e descrição
            parts = header.split(None, 1)  # Split no primeiro espaço
            current_name = parts[0]
            current_description = parts[1] if len(parts) > 1 else None
            current_content = []

        # Linha de sequência
        else:
            if current_name is None:
                raise ValueError(
                    f"Linha {line_num}: Sequência sem header. "
                    f"Arquivo FASTA deve começar com '>'"
                )

            # Limpar e validar linha
            clean_line = re.sub(r"\s+", "", line).upper()
            current_content.append(clean_line)

    # Não esquecer a última sequência
    if current_name is not None:
        if not current_content:
            raise ValueError(f"Sequência '{current_name}' está vazia")
        sequences.append(_build_sequence_dict(
            current_name,
            current_description,
            "".join(current_content)
        ))

    return sequences


def _build_sequence_dict(
    name: str,
    description: Optional[str],
    content: str
) -> Dict:
    """
    Constrói dicionário de sequência com tipo detectado.
    """
    sequence_type = detect_sequence_type(content)

    return {
        "name": name,
        "description": description,
        "content": content,
        "sequence_type": sequence_type,
    }


# ========================================
# DETECÇÃO DE TIPO
# ========================================

def detect_sequence_type(sequence: str) -> SequenceType:
    """
    Detecta automaticamente o tipo da sequência.

    Algoritmo:
    1. Se tem aminoácidos exclusivos → Proteína
    2. Se tem U e não tem T → RNA
    3. Caso contrário → DNA

    Args:
        sequence: Sequência a analisar

    Returns:
        SequenceType detectado
    """
    sequence = sequence.upper()
    chars = set(sequence)

    # Se tem caracteres exclusivos de proteína → é proteína
    if chars & PROTEIN_ONLY_CHARS:
        return SequenceType.PROTEIN

    # Se tem U e não tem T → RNA
    if "U" in chars and "T" not in chars:
        return SequenceType.RNA

    # Caso contrário, assumir DNA
    return SequenceType.DNA


def detect_sequence_type_with_confidence(
    sequence: str
) -> Tuple[SequenceType, float, Dict]:
    """
    Detecta tipo de sequência com score de confiança.

    Útil para sequências ambíguas onde queremos mais informação.

    Args:
        sequence: Sequência a analisar

    Returns:
        Tupla com:
        - SequenceType detectado
        - Confiança (0.0 a 1.0)
        - Composição de caracteres (dict)
    """
    sequence = sequence.upper()
    length = len(sequence)

    if length == 0:
        return SequenceType.DNA, 0.0, {}

    # Contar caracteres
    counter = Counter(sequence)
    composition = {char: count / length for char, count in counter.items()}

    chars = set(sequence)

    # Check for protein-specific amino acids
    protein_specific = chars & PROTEIN_ONLY_CHARS
    if protein_specific:
        # Alta confiança se tem muitos aminoácidos exclusivos
        protein_ratio = sum(counter[c] for c in protein_specific) / length
        confidence = min(0.5 + protein_ratio * 2, 1.0)
        return SequenceType.PROTEIN, confidence, composition

    # Check for RNA (has U, no T)
    if "U" in chars and "T" not in chars:
        # Alta confiança se não tem caracteres estranhos
        valid_ratio = sum(counter[c] for c in chars & RNA_CHARS) / length
        return SequenceType.RNA, valid_ratio, composition

    # Check for DNA
    if "T" in chars or ("A" in chars and "C" in chars and "G" in chars):
        valid_ratio = sum(counter[c] for c in chars & DNA_CHARS) / length
        return SequenceType.DNA, valid_ratio, composition

    # Default to DNA with low confidence
    return SequenceType.DNA, 0.5, composition


# ========================================
# VALIDAÇÃO
# ========================================

def validate_sequence(
    sequence: str,
    sequence_type: SequenceType
) -> Tuple[bool, Optional[str]]:
    """
    Valida se a sequência contém apenas caracteres válidos.

    Args:
        sequence: Sequência a validar
        sequence_type: Tipo esperado

    Returns:
        Tupla (is_valid, error_message)
    """
    sequence = sequence.upper()

    if sequence_type == SequenceType.DNA:
        valid_chars = DNA_CHARS
        type_name = "DNA"
    elif sequence_type == SequenceType.RNA:
        valid_chars = RNA_CHARS
        type_name = "RNA"
    elif sequence_type == SequenceType.PROTEIN:
        valid_chars = PROTEIN_CHARS
        type_name = "proteína"
    else:
        return False, f"Tipo de sequência desconhecido: {sequence_type}"

    invalid_chars = set(sequence) - valid_chars
    if invalid_chars:
        return False, (
            f"Sequência de {type_name} contém caracteres inválidos: "
            f"{sorted(invalid_chars)}. "
            f"Caracteres permitidos: {sorted(valid_chars)}"
        )

    return True, None


# ========================================
# FORMATAÇÃO
# ========================================

def format_fasta(
    name: str,
    sequence: str,
    description: Optional[str] = None,
    line_width: int = 60
) -> str:
    """
    Formata uma sequência no formato FASTA.

    Args:
        name: Nome da sequência
        sequence: Conteúdo da sequência
        description: Descrição opcional
        line_width: Caracteres por linha (padrão: 60)

    Returns:
        String formatada em FASTA
    """
    header = f">{name}"
    if description:
        header += f" {description}"

    # Quebrar sequência em linhas
    lines = [header]
    for i in range(0, len(sequence), line_width):
        lines.append(sequence[i:i + line_width])

    return "\n".join(lines)


def format_multi_fasta(sequences: List[Dict], line_width: int = 60) -> str:
    """
    Formata múltiplas sequências em formato FASTA.

    Args:
        sequences: Lista de dicts com name, content, description
        line_width: Caracteres por linha

    Returns:
        String com todas as sequências em FASTA
    """
    fasta_entries = []

    for seq in sequences:
        fasta_entries.append(format_fasta(
            name=seq["name"],
            sequence=seq["content"],
            description=seq.get("description"),
            line_width=line_width
        ))

    return "\n".join(fasta_entries)
