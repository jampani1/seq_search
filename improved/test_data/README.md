# Test Data - Bioinformatics Hub

Dados de teste para validação da plataforma.

## Organismo Modelo: Sporisorium scitamineum

Fungo causador do carvão da cana-de-açúcar. Escolhido por:
- Genoma completo e bem anotado
- ~68 efetores confirmados (CSEPs)
- Dados de expressão durante infecção disponíveis
- Relevância agrícola (cana é importante no Brasil)

### Dados Disponíveis

| Tipo | Fonte | Acesso |
|------|-------|--------|
| Genoma | NCBI Assembly | GCA_000772675.1 |
| Proteoma | NCBI Protein | ~6,677 proteínas |
| RNA-seq infecção | GEO | GSE57429, GSE114613 |
| Efetores anotados | Literatura | Taniguti et al. 2015 |

### Como Baixar

```bash
# 1. Proteoma (para BLAST/DIAMOND)
cd test_data/sporisorium_scitamineum
curl -O "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/772/675/GCA_000772675.1_Sporisorium_scitamineum_v1/GCA_000772675.1_Sporisorium_scitamineum_v1_protein.faa.gz"
gunzip GCA_000772675.1_Sporisorium_scitamineum_v1_protein.faa.gz
mv GCA_000772675.1_Sporisorium_scitamineum_v1_protein.faa proteome.faa

# 2. Genoma (CDS para genes)
curl -O "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/772/675/GCA_000772675.1_Sporisorium_scitamineum_v1/GCA_000772675.1_Sporisorium_scitamineum_v1_cds_from_genomic.fna.gz"
gunzip GCA_000772675.1_Sporisorium_scitamineum_v1_cds_from_genomic.fna.gz
mv GCA_000772675.1_Sporisorium_scitamineum_v1_cds_from_genomic.fna cds.fna

# 3. Anotação GFF
curl -O "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/772/675/GCA_000772675.1_Sporisorium_scitamineum_v1/GCA_000772675.1_Sporisorium_scitamineum_v1_genomic.gff.gz"
gunzip GCA_000772675.1_Sporisorium_scitamineum_v1_genomic.gff.gz
mv GCA_000772675.1_Sporisorium_scitamineum_v1_genomic.gff annotation.gff
```

### Scripts de Download Automático

Use o script em `scripts/download_test_data.sh` para baixar tudo automaticamente.

## Dados de Expressão (RNA-seq)

Para testar Gene Regulatory Networks:

| Dataset | Condição | Timepoints | GEO ID |
|---------|----------|------------|--------|
| Taniguti 2015 | Infecção cana-de-açúcar | 24h, 48h, 120h | GSE57429 |
| Resistance study | Cultivar resistente vs suscetível | 48h | GSE114613 |

### Download via GEO

```bash
# Instalar GEOquery ou usar wget
# Os dados processados (counts matrix) serão baixados

# Para GSE57429 (expressão durante infecção)
cd test_data/sporisorium_scitamineum/expression
wget "https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE57429&format=file" -O GSE57429_RAW.tar
```

## Estrutura de Pastas

```
test_data/
├── sporisorium_scitamineum/
│   ├── proteome.faa          # Proteínas para BLAST
│   ├── cds.fna               # Genes para análise
│   ├── annotation.gff        # Anotação do genoma
│   ├── effectors/            # Efetores conhecidos
│   │   ├── confirmed_cseps.faa
│   │   └── predicted_effectors.txt
│   └── expression/           # Dados RNA-seq
│       ├── counts_matrix.tsv
│       └── metadata.tsv
└── README.md                 # Este arquivo
```

## Referências

1. Taniguti LM, et al. (2015). Complete Genome Sequence of Sporisorium scitamineum. PLOS ONE. DOI: 10.1371/journal.pone.0129318

2. Que Y, et al. (2014). A Global View of Transcriptome Dynamics during Sporisorium scitamineum Challenge in Sugarcane by RNA-seq. PLOS ONE. DOI: 10.1371/journal.pone.0106476

3. Barnabas L, et al. (2018). Analysis of the resistance mechanisms in sugarcane during Sporisorium scitamineum infection. PLOS ONE. DOI: 10.1371/journal.pone.0197840
