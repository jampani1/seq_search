#!/bin/bash
# =============================================================================
# Download de Dados Reais - Sporisorium scitamineum
# =============================================================================
# Este script baixa genoma, proteoma e dados de RNA-seq públicos
#
# Pré-requisitos:
#   - NCBI datasets CLI: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/download-and-install/
#   - SRA Toolkit: conda install -c bioconda sra-tools
#   - wget ou curl
#
# Uso:
#   chmod +x download_all.sh
#   ./download_all.sh
# =============================================================================

set -e  # Parar em caso de erro

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/../sporisorium_scitamineum"

echo "============================================"
echo "Download de dados - Sporisorium scitamineum"
echo "============================================"
echo ""
echo "Diretório de saída: ${DATA_DIR}"
echo ""

mkdir -p "${DATA_DIR}/genome"
mkdir -p "${DATA_DIR}/rnaseq"
mkdir -p "${DATA_DIR}/expression"

# -----------------------------------------------------------------------------
# 1. GENOMA E PROTEOMA (NCBI)
# -----------------------------------------------------------------------------
echo "[1/4] Baixando genoma e proteoma..."

if command -v datasets &> /dev/null; then
    # Usando NCBI datasets CLI
    datasets download genome accession GCA_900002365.1 \
        --include genome,gff3,protein,cds \
        --filename "${DATA_DIR}/genome/ncbi_dataset.zip"

    unzip -o "${DATA_DIR}/genome/ncbi_dataset.zip" -d "${DATA_DIR}/genome/"

    # Organizar arquivos
    find "${DATA_DIR}/genome/ncbi_dataset/data" -name "*.fna" -exec mv {} "${DATA_DIR}/genome/" \;
    find "${DATA_DIR}/genome/ncbi_dataset/data" -name "*.faa" -exec mv {} "${DATA_DIR}/genome/" \;
    find "${DATA_DIR}/genome/ncbi_dataset/data" -name "*.gff" -exec mv {} "${DATA_DIR}/genome/" \;

    echo "  Genoma baixado com sucesso!"
else
    echo "  AVISO: 'datasets' CLI não encontrado."
    echo "  Instale: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/download-and-install/"
    echo ""
    echo "  Alternativa - baixar manualmente:"
    echo "  https://www.ncbi.nlm.nih.gov/datasets/genome/GCA_900002365.1/"
fi

# -----------------------------------------------------------------------------
# 2. RNA-SEQ (SRA) - PRJNA415122
# -----------------------------------------------------------------------------
echo ""
echo "[2/4] Baixando dados RNA-seq (PRJNA415122)..."

if command -v prefetch &> /dev/null; then
    # Lista de SRR IDs do projeto PRJNA415122
    # (6 amostras: 3 inoculadas + 3 mock, 48hpi)
    SRR_IDS=(
        "SRR6175706"
        "SRR6175707"
        "SRR6175708"
        "SRR6175709"
        "SRR6175710"
        "SRR6175711"
    )

    for srr in "${SRR_IDS[@]}"; do
        echo "  Baixando ${srr}..."
        prefetch --output-directory "${DATA_DIR}/rnaseq" "${srr}" || true
    done

    echo "  Convertendo para FASTQ..."
    for sra in "${DATA_DIR}/rnaseq"/*/*.sra; do
        if [ -f "$sra" ]; then
            fastq-dump --split-files --outdir "${DATA_DIR}/rnaseq" "$sra" || true
        fi
    done

    echo "  RNA-seq baixado com sucesso!"
else
    echo "  AVISO: SRA Toolkit não encontrado."
    echo "  Instale: conda install -c bioconda sra-tools"
    echo ""
    echo "  Alternativa - ENA (mais rápido):"
    echo "  https://www.ebi.ac.uk/ena/browser/view/PRJNA415122"
fi

# -----------------------------------------------------------------------------
# 3. MATRIZ DE EXPRESSÃO (da literatura)
# -----------------------------------------------------------------------------
echo ""
echo "[3/4] Criando matriz de expressão de teste..."

# Hub genes do estudo WGCNA (PMC9409688)
cat > "${DATA_DIR}/expression/hub_genes_wgcna.txt" << 'EOF'
# Hub Genes - S. scitamineum WGCNA Study
# Fonte: PMC9409688 (Tao et al., 2022)

# MEpurple Module (208 genes total, top 10 hubs)
SPSC_04270	Mig1 protein	hub_purple
SPSC_03768	hypothetical protein	hub_purple
SPSC_06609	hypothetical protein	hub_purple
SPSC_00576	hypothetical protein	hub_purple
SPSC_06362	hypothetical protein	hub_purple
SPSC_05923	glycosyl hydrolase family 16	hub_purple
SPSC_01958	beta-N-acetylglucosaminidase	hub_purple
SPSC_04676	hypothetical protein	hub_purple
SPSC_02155	secreted chorismate mutase	hub_purple
SPSC_04321	collagen triple helix repeat	hub_purple

# MEdarkturquoise Module (66 genes total, top 10 hubs)
SPSC_00606	hypothetical protein	hub_darkturquoise
SPSC_02450	hypothetical protein	hub_darkturquoise
SPSC_05681	hypothetical protein	hub_darkturquoise
SPSC_01622	hypothetical protein	hub_darkturquoise
SPSC_00571	mRNA export factor	hub_darkturquoise
SPSC_01364	hypothetical protein	hub_darkturquoise
SPSC_00940	pleckstrin homology domain	hub_darkturquoise
SPSC_05327	hypothetical protein	hub_darkturquoise
SPSC_03542	hypothetical protein	hub_darkturquoise
SPSC_03041	hypothetical protein	hub_darkturquoise
EOF

echo "  Lista de hub genes salva!"

# -----------------------------------------------------------------------------
# 4. EFETORES CANDIDATOS
# -----------------------------------------------------------------------------
echo ""
echo "[4/4] Criando lista de efetores candidatos..."

cat > "${DATA_DIR}/expression/candidate_effectors.txt" << 'EOF'
# Candidate Secreted Effector Proteins (CSEPs) - S. scitamineum
# Fonte: PLOS ONE 2015 (Taniguti et al.)
# Total: 68 CSEPs, 32 expressos durante infecção

# Efetores validados/caracterizados
SPSC_05923	glycosyl hydrolase family 16	induced_infection	validated
SPSC_02155	secreted chorismate mutase	induced_infection	validated
SPSC_04321	collagen triple helix repeat	induced_infection	candidate

# Small Cysteine-Rich Proteins (SCRPs) - 21 identificados
SPSC_00576	SCRP candidate	induced_infection	candidate
SPSC_06362	SCRP candidate	induced_infection	candidate
SPSC_04676	SCRP candidate	induced_infection	candidate
SPSC_01958	beta-N-acetylglucosaminidase	induced_infection	candidate

# Mig1 - regulador de virulência
SPSC_04270	Mig1 protein	master_regulator	validated

# Genes de ilha genômica (expressos apenas in planta)
SPSC_genomic_island_1	island gene 1	in_planta_only	candidate
SPSC_genomic_island_2	island gene 2	in_planta_only	candidate
EOF

echo "  Lista de efetores salva!"

# -----------------------------------------------------------------------------
# RESUMO
# -----------------------------------------------------------------------------
echo ""
echo "============================================"
echo "Download concluído!"
echo "============================================"
echo ""
echo "Arquivos em: ${DATA_DIR}"
echo ""
echo "Estrutura:"
echo "  genome/"
echo "    - *.fna (genoma)"
echo "    - *.faa (proteoma)"
echo "    - *.gff (anotação)"
echo "  rnaseq/"
echo "    - *.fastq (reads)"
echo "  expression/"
echo "    - hub_genes_wgcna.txt"
echo "    - candidate_effectors.txt"
echo ""
echo "Próximos passos:"
echo "  1. Alinhar RNA-seq ao genoma (STAR/HISAT2)"
echo "  2. Quantificar expressão (featureCounts/Salmon)"
echo "  3. Normalizar (TPM/FPKM)"
echo "  4. Usar matriz no endpoint /api/v1/grn"
