# Datasets Reais - Sporisorium scitamineum

> Compilação de datasets públicos para testar o Bioinformatics Hub com dados reais.

## 1. Genoma de Referência

### NCBI Assembly: GCA_900002365.1

| Campo | Valor |
|-------|-------|
| Organismo | *Sporisorium scitamineum* |
| Tamanho | 19.98 Mb |
| Genes | 6,677 proteínas codificantes |
| tRNAs | 111 |
| GC Content | ~54% |
| Download | [NCBI Datasets](https://www.ncbi.nlm.nih.gov/datasets/genome/GCA_900002365.1/) |

**Arquivos disponíveis:**
- Genoma (FASTA)
- Anotação (GFF3)
- Proteoma (FAA)
- CDS (FNA)

### Assemblies Alternativos

| Assembly | Accession | Notas |
|----------|-----------|-------|
| v1 | GCA_000772675.1 | Primeira versão |
| Complete | GCA_001243155.1 | PacBio + Illumina |

---

## 2. Datasets de Expressão Gênica (RNA-seq)

### Dataset 1: Resistência a Smut (PRJNA415122)

**Fonte:** [PLOS ONE - Resistance mechanisms](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0197840)

| Campo | Valor |
|-------|-------|
| BioProject | PRJNA415122 |
| SRA | SRP121526 |
| Amostras | 6 (3 inoculado + 3 mock) |
| Timepoint | 48 hpi |
| Cultivar | CP74-2005 |
| Plataforma | Illumina HiSeq 2000 |
| Reads | 100bp paired-end |

**Dados disponíveis:**
- 861 genes diferencialmente expressos
- GO enrichment
- Lista de genes de defesa

**Download SRA:**
```bash
# Instalar sra-tools
conda install -c bioconda sra-tools

# Download das 6 amostras
prefetch SRP121526
fastq-dump --split-files SRP121526
```

---

### Dataset 2: WGCNA Network Analysis (CRA006643)

**Fonte:** [PMC9409688 - Hub Genes WGCNA](https://pmc.ncbi.nlm.nih.gov/articles/PMC9409688/)

| Campo | Valor |
|-------|-------|
| Repositório | GSA (China) |
| Accession | CRA006643 |
| Total dados | 230.24 GB |
| Reads | 1.53 bilhão |
| Q30 | >98.4% |

**Módulos identificados:**
- **MEdarkturquoise**: 66 genes
- **MEpurple**: 208 genes (inclui efetores candidatos)

**Hub Genes (MEpurple):**
```
SPSC_04270 (Mig1 protein)
SPSC_03768
SPSC_06609
SPSC_00576
SPSC_06362
SPSC_05923 (glycosyl hydrolase)
SPSC_01958 (beta-N-acetylglucosaminidase)
SPSC_04676
SPSC_02155 (secreted chorismate mutase)
SPSC_04321 (collagen)
```

**Hub Genes (MEdarkturquoise):**
```
SPSC_00606
SPSC_02450
SPSC_05681
SPSC_01622
SPSC_00571 (mRNA export factor)
SPSC_01364
SPSC_00940 (pleckstrin homology protein)
SPSC_05327
SPSC_03542
SPSC_03041
```

**Download GSA:**
```bash
# Via NGDC (National Genomics Data Center)
# https://ngdc.cncb.ac.cn/gsa/browse/CRA006643
```

---

### Dataset 3: Transcriptome Dynamics (2014)

**Fonte:** [PLOS ONE - Global View](https://pmc.ncbi.nlm.nih.gov/articles/PMC4149577/)

| Campo | Valor |
|-------|-------|
| Amostras | 8 |
| Cultivares | Yacheng05-179 (resistente), ROC22 (suscetível) |
| Timepoints | 24, 48, 120 hpi |
| Unigenes | 65,852 |
| Dados | 36.68 Gb |

**Pathways identificados:**
- Plant hormone signal transduction
- Flavonoid biosynthesis
- Plant-pathogen interaction
- Cell wall fortification

---

## 3. Efetores Candidatos

### Do genoma (PLOS ONE 2015)

- **68 CSEPs** (Candidate Secreted Effector Proteins)
- **32 expressos** durante infecção
- **21 SCRPs** (Small Cysteine-Rich Proteins) do estudo WGCNA

**Lista parcial de efetores validados:**
```
SPSC_05923 - glycosyl hydrolase (induzido durante infecção)
SPSC_02155 - secreted chorismate mutase
SPSC_04321 - collagen-like protein
```

---

## 4. Scripts de Download

### download_genome.sh
```bash
#!/bin/bash
# Download genoma e anotação de S. scitamineum

OUTDIR="sporisorium_scitamineum"
mkdir -p $OUTDIR

# Genoma
datasets download genome accession GCA_900002365.1 \
    --include genome,gff3,protein \
    --filename ${OUTDIR}/genome.zip

unzip ${OUTDIR}/genome.zip -d ${OUTDIR}/
```

### download_rnaseq.sh
```bash
#!/bin/bash
# Download dados RNA-seq do SRA

OUTDIR="rnaseq_data"
mkdir -p $OUTDIR

# BioProject PRJNA415122
prefetch --output-directory $OUTDIR SRP121526

# Converter para FASTQ
for sra in $OUTDIR/SRP121526/*.sra; do
    fastq-dump --split-files --outdir $OUTDIR $sra
done
```

---

## 5. Referências

1. Que Y, et al. (2014) A Global View of Transcriptome Dynamics during *Sporisorium scitamineum* Challenge in Sugarcane by RNA-seq. PLOS ONE 9(8): e106476.

2. Peters LP, et al. (2018) Analysis of the resistance mechanisms in sugarcane during *Sporisorium scitamineum* infection using RNA-seq and microscopy. PLOS ONE 13(5): e0197840.

3. Tao H, et al. (2022) Identification of Gene Modules and Hub Genes Associated with *Sporisorium scitamineum* Infection Using WGCNA. J Fungi 8(8): 852.

4. Taniguti LM, et al. (2015) Complete Genome Sequence of *Sporisorium scitamineum* and Biotrophic Interaction Transcriptome with Sugarcane. PLOS ONE 10(6): e0129318.

5. Dutheil JY, et al. (2016) A tale of genome compartmentalization: the evolution of virulence clusters in smut fungi. Genome Biol Evol 8(3): 681-704.
