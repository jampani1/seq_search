#!/bin/bash
# ============================================
# Download Test Data - Sporisorium scitamineum
# ============================================
# Script para baixar dados de teste do organismo modelo
#
# Uso: ./scripts/download_test_data.sh
#
# Requer: curl, gunzip

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TEST_DATA_DIR="$PROJECT_DIR/test_data/sporisorium_scitamineum"
BLAST_DB_DIR="$PROJECT_DIR/databases/blast"
DIAMOND_DB_DIR="$PROJECT_DIR/databases/diamond"

# URLs NCBI
NCBI_BASE="https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/772/675/GCA_000772675.1_Sporisorium_scitamineum_v1"
PROTEOME_URL="${NCBI_BASE}/GCA_000772675.1_Sporisorium_scitamineum_v1_protein.faa.gz"
CDS_URL="${NCBI_BASE}/GCA_000772675.1_Sporisorium_scitamineum_v1_cds_from_genomic.fna.gz"
GFF_URL="${NCBI_BASE}/GCA_000772675.1_Sporisorium_scitamineum_v1_genomic.gff.gz"

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Downloading Sporisorium scitamineum data  ${NC}"
echo -e "${GREEN}============================================${NC}"

# Criar diretórios
mkdir -p "$TEST_DATA_DIR"
mkdir -p "$TEST_DATA_DIR/effectors"
mkdir -p "$TEST_DATA_DIR/expression"
mkdir -p "$BLAST_DB_DIR"
mkdir -p "$DIAMOND_DB_DIR"

cd "$TEST_DATA_DIR"

# ============================================
# 1. Download Proteome
# ============================================
echo -e "\n${YELLOW}[1/3] Downloading proteome...${NC}"
if [ -f "proteome.faa" ]; then
    echo "  proteome.faa already exists, skipping..."
else
    curl -L -o proteome.faa.gz "$PROTEOME_URL"
    gunzip proteome.faa.gz
    echo -e "  ${GREEN}Done!${NC} $(grep -c "^>" proteome.faa) proteins"
fi

# ============================================
# 2. Download CDS
# ============================================
echo -e "\n${YELLOW}[2/3] Downloading CDS...${NC}"
if [ -f "cds.fna" ]; then
    echo "  cds.fna already exists, skipping..."
else
    curl -L -o cds.fna.gz "$CDS_URL"
    gunzip cds.fna.gz
    echo -e "  ${GREEN}Done!${NC} $(grep -c "^>" cds.fna) genes"
fi

# ============================================
# 3. Download GFF annotation
# ============================================
echo -e "\n${YELLOW}[3/3] Downloading annotation...${NC}"
if [ -f "annotation.gff" ]; then
    echo "  annotation.gff already exists, skipping..."
else
    curl -L -o annotation.gff.gz "$GFF_URL"
    gunzip annotation.gff.gz
    echo -e "  ${GREEN}Done!${NC}"
fi

# ============================================
# Create BLAST database
# ============================================
echo -e "\n${YELLOW}Creating BLAST database...${NC}"
if command -v makeblastdb &> /dev/null; then
    makeblastdb -in proteome.faa -dbtype prot -out "$BLAST_DB_DIR/sporisorium_proteome" -title "S. scitamineum Proteome"
    echo -e "  ${GREEN}BLAST database created!${NC}"
else
    echo -e "  ${RED}makeblastdb not found. Install BLAST+ to create database.${NC}"
    echo "  Run: sudo apt install ncbi-blast+ (Linux) or use Docker"
fi

# ============================================
# Create DIAMOND database
# ============================================
echo -e "\n${YELLOW}Creating DIAMOND database...${NC}"
if command -v diamond &> /dev/null; then
    diamond makedb --in proteome.faa -d "$DIAMOND_DB_DIR/sporisorium_proteome"
    echo -e "  ${GREEN}DIAMOND database created!${NC}"
else
    echo -e "  ${RED}diamond not found. Install DIAMOND to create database.${NC}"
    echo "  Run: conda install -c bioconda diamond"
fi

# ============================================
# Summary
# ============================================
echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}  Download Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "\nFiles downloaded to: ${TEST_DATA_DIR}"
echo -e "\nContents:"
ls -lh "$TEST_DATA_DIR"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Start the application: docker-compose up -d"
echo "2. Upload proteome.faa via /api/v1/sequences/upload"
echo "3. Test BLAST searches against the database"
