# DATA_SOURCES.md
## Fontes de Dados para N. benthamiana

---

## 1. NbenBase (PRINCIPAL)

**URL**: https://nbenthamiana.jp/

### Dados Disponiveis:
- Gene Annotations Browser
- Expression Profiles (RNA-seq)
- Grafting time series
- Agroinfiltration data
- JBrowse2 Genome Browser
- Downloads de genoma

### Versao Atual:
- v1.1 (Marco 2024)
- 19 cromossomos reorganizados
- Anotacoes atualizadas

### Como Acessar:
1. Acesse https://nbenthamiana.jp/
2. Va em "Downloads" > "Genome Resources"
3. Ou use "Expression Profiles" para dados de expressao

---

## 2. Nature Plants Multi-Omic Resource (2023)

**Paper**: https://www.nature.com/articles/s41477-023-01489-8

### Dados Gerados:
- Genoma LAB strain (alta qualidade)
- Genoma QLD strain (wild)
- Transcriptoma (9 tecidos)
- Epigenoma
- miRNA
- SNP maps

### Acesso:
- Supplementary Data do paper
- Sol Genomics Network

---

## 3. Sol Genomics Network

**URL**: https://solgenomics.net/organism/Nicotiana_benthamiana/genome

### Recursos:
- Genoma Niben2.6.1
- BLAST tool
- JBrowse
- FTP download

### Download FTP:
```
ftp://ftp.solgenomics.net/genomes/Nicotiana_benthamiana/
```

---

## 4. Datasets de Infeccao (RNA-seq)

### 4.1 Phytophthora palmivora Time-Series

**Paper**: [BMC Biology 2017](https://link.springer.com/article/10.1186/s12915-017-0379-1)

**Conteudo**:
- Dual transcriptomics (planta + patogeno)
- Time series de infeccao
- Identificacao de efetores RXLR

**Dados**:
- Verificar ENA (European Nucleotide Archive)
- Supplementary tables com contagens

### 4.2 Pseudomonas fluorescens

**Paper**: [Scientific Reports 2019](https://www.nature.com/articles/s41598-018-38247-2)

**Conteudo**:
- 9 tecidos diferentes
- Reference genes identificados
- Normalizacao RNA-seq

---

## 5. Boyce Thompson Institute

**URL**: https://btiscience.org/our-research/research-facilities/research-resources/nicotiana-benthamiana/

### Recursos:
- Clones VIGS
- Informacoes de cultivo
- Protocolos

---

## 6. PHI-base (Efetores)

**URL**: http://www.phi-base.org/

### Download:
- Formato: TSV tab-delimited
- Conteudo: 10,614 genes de virulencia
- Filtro por hospedeiro: Solanaceae

### Campos Uteis:
- Gene name
- Protein ID
- Host organism
- Phenotype
- Effector function

---

## 7. STRING Database (Interacoes)

**URL**: https://string-db.org/

### Uso:
1. Buscar por "Nicotiana" ou usar ortologos de Arabidopsis
2. Download de rede de interacoes
3. Formato: TSV com scores de confianca

---

## PLANO DE DOWNLOAD

### Prioridade 1 (Essencial):
1. [ ] NbenBase - Gene annotations + Expression profiles
2. [ ] PHI-base - Tabela de efetores filtrada
3. [ ] Sol Genomics - Gene functional annotations

### Prioridade 2 (Complementar):
4. [ ] Nature Plants Supplementary - Multi-omic data
5. [ ] STRING - Rede de interacoes predita

### Prioridade 3 (Futuro):
6. [ ] SRA/GEO raw counts de estudos especificos
7. [ ] Dados de WGCNA publicados

---

## TAMANHO ESTIMADO

| Fonte | Tipo | Tamanho |
|-------|------|---------|
| NbenBase annotations | TSV/GFF | ~50 MB |
| NbenBase expression | CSV | ~20 MB |
| PHI-base filtrado | TSV | ~5 MB |
| STRING network | TSV | ~10 MB |
| **TOTAL** | - | **~85 MB** |

---

## FORMATO DE SAIDA PARA O HUB

Apos download, converter para:

```json
{
  "genes": [
    {
      "id": "Niben101Scf00010g00001",
      "symbol": "FLS2",
      "description": "Flagellin sensing 2",
      "go_terms": ["GO:0004672", "GO:0006468"],
      "category": "PRR",
      "location": "membrane"
    }
  ],
  "interactions": [
    {
      "source": "FLS2",
      "target": "BAK1",
      "type": "activation",
      "weight": 0.95,
      "evidence": "experimental"
    }
  ]
}
```

---

*Documento criado: 2026-03-02*
