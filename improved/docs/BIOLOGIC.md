# BIOLOGIC.md - Fundamentos Biologicos
> Guia de referencia biologica para o Bioinformatics Hub

---

## Organismo Modelo: Nicotiana benthamiana

### O que e?

**Nicotiana benthamiana** e uma planta da familia Solanaceae (mesma familia do tomate, batata e tabaco). E considerada o "camundongo das plantas" - o modelo mais usado em biologia vegetal e fitopatologia.

```
Reino:    Plantae
Familia:  Solanaceae
Genero:   Nicotiana
Especie:  N. benthamiana

Origem:   Australia
Genoma:   ~3 Gb (grande, mas bem anotado)
Ploidia:  Alotetraploide (4 copias de cada cromossomo)
```

### Por que e tao usada?

1. **Facil de transformar** - Aceita DNA estrangeiro facilmente (Agrobacterium)
2. **Crescimento rapido** - 6-8 semanas da semente a planta adulta
3. **Susceptivel a muitos patogenos** - Ideal para estudar doencas
4. **Sistema imune "defeituoso"** - Mutacao natural no gene Rdr1
5. **Recursos abundantes** - Genoma, transcriptomas, proteomas disponiveis

### Mutacao Chave: Rdr1

N. benthamiana tem uma **insercao natural** no gene Rdr1 (RNA-dependent RNA polymerase 1). Isso enfraquece sua defesa contra virus, tornando-a:
- Mais susceptivel a infeccoes
- Melhor hospedeira para expressar proteinas
- Ideal para estudar efetores de patogenos

---

## Conceitos Fundamentais

### 1. Gene Regulatory Networks (GRN)

**O que e uma GRN?**

Uma rede de genes que se regulam mutuamente. Imagine como uma "rede social" onde:
- **Nodes** = Genes
- **Edges** = Regulacao (ativacao ou repressao)

```
    Gene A (TF)
       |
       | ativa
       v
    Gene B ----reprime----> Gene C
       |
       | ativa
       v
    Gene D (efetor)
```

**Tipos de regulacao:**
- **Ativacao (+)**: Gene A aumenta expressao de Gene B
- **Repressao (-)**: Gene A diminui expressao de Gene B

**Fatores de Transcricao (TFs):**
- Proteinas que controlam quando genes sao ligados/desligados
- "Chefes" da rede - regulam muitos outros genes
- Aparecem como **hubs** (muitas conexoes) na visualizacao

### 2. Efetores

**O que sao efetores?**

Proteinas secretadas por patogenos para manipular a planta hospedeira.

```
PATOGENO                    PLANTA
+--------+                 +------------------+
| Efetor | ----secreta---> | Celula vegetal   |
+--------+                 |                  |
                           | - Suprime defesa |
                           | - Altera metabol.|
                           | - Causa doenca   |
                           +------------------+
```

**Caracteristicas de efetores:**
- Peptideo sinal (para secrecao)
- Pequenos (geralmente <400 aa)
- Sem dominio transmembrana (sao secretados)
- Muitos sao "orphans" (sem funcao conhecida)

**Tipos de efetores:**
| Tipo | Local de Acao | Exemplo |
|------|---------------|---------|
| Apoplastico | Espaco entre celulas | Quitinases |
| Citoplasmatico | Dentro da celula | AvrPto |
| Nuclear | No nucleo | TAL effectors |

### 3. Vias de Sinalizacao

**PTI - Pattern-Triggered Immunity**
- Primeira linha de defesa
- Reconhece PAMPs (moleculas comuns de patogenos)
- Resposta rapida mas generica

```
PAMP (ex: flagelina) --> Receptor (FLS2) --> MAPK cascade --> Defesa
```

**ETI - Effector-Triggered Immunity**
- Segunda linha de defesa
- Reconhece efetores especificos
- Resposta forte, pode causar morte celular (HR)

```
Efetor --> Proteina R --> Resposta Hipersensivel (HR) --> Morte celular
```

### 4. Consequencias Celulares

Quando um efetor entra na celula, pode afetar:

**Membrana Plasmatica:**
- Canais ionicos (fluxo de Ca2+)
- Receptores (bloqueio de sinalizacao)
- Permeabilidade (vazamento)

**Citoplasma:**
- Proteassoma (degradacao de proteinas)
- Citoesqueleto (movimento celular)
- Vesiculas (trafego intracelular)

**Nucleo:**
- Fatores de transcricao
- Expressao genica
- Reparo de DNA

**Cloroplasto:**
- Fotossintese
- Producao de ROS
- Sinalizacao

**Mitocondria:**
- Respiracao
- Morte celular programada

---

## Recursos de Dados para N. benthamiana

### Genoma e Anotacao

| Recurso | URL | Descricao |
|---------|-----|-----------|
| Sol Genomics | solgenomics.net | Genoma, genes, mapas |
| NCBI | ncbi.nlm.nih.gov | Sequencias, SRA |
| Phytozome | phytozome.jgi.doe.gov | Comparativo |
| UniProt | uniprot.org | Proteinas anotadas |

### Transcriptomas Publicos

**GEO/SRA datasets relevantes:**
- GSE56922 - Infeccao por Pseudomonas
- GSE117926 - Resposta a efetores
- GSE149217 - Virus do mosaico
- GSE162599 - Phytophthora infestans

### Bancos de Efetores

| Banco | Conteudo |
|-------|----------|
| PHI-base | Efetores validados experimentalmente |
| EffectorP | Predicoes por ML |
| SignalP | Peptideos sinal |
| TMHMM | Dominios transmembrana |

---

## Fluxo de Analise Proposto

```
1. DADOS DE EXPRESSAO
   |
   v
2. NORMALIZACAO (TPM/FPKM)
   |
   v
3. INFERENCIA DE GRN
   |-- Correlacao
   |-- Informacao Mutua
   |-- GRNBoost2
   |
   v
4. INTEGRACAO COM ANOTACAO
   |-- GO terms
   |-- Efetores preditos
   |-- Alvos de TFs
   |
   v
5. VISUALIZACAO
   |-- Rede completa
   |-- Sub-redes por funcao
   |-- Vias especificas
   |
   v
6. SIMULACAO DE CONSEQUENCIAS
   |-- Knockout virtual
   |-- Cascata de efeitos
   |-- Impacto celular
```

---

## Glossario

| Termo | Definicao |
|-------|-----------|
| **Avirulencia (Avr)** | Efetor reconhecido pela planta (causa resistencia) |
| **DAMP** | Moleculas de dano (da propria planta) |
| **ETI** | Imunidade disparada por efetor |
| **GO term** | Categoria funcional padronizada |
| **HR** | Resposta hipersensivel (morte celular) |
| **Hub gene** | Gene com muitas conexoes na rede |
| **MAPK** | Quinase de sinalizacao |
| **Ortolgo** | Gene equivalente em outra especie |
| **PAMP** | Padrao molecular de patogeno |
| **PRR** | Receptor de reconhecimento de padroes |
| **PTI** | Imunidade disparada por PAMP |
| **R gene** | Gene de resistencia |
| **ROS** | Especies reativas de oxigenio |
| **SA** | Acido salicilico (hormonio de defesa) |
| **TF** | Fator de transcricao |
| **WGCNA** | Analise de co-expressao ponderada |

---

## Exemplos de Vias a Explorar

### Via 1: Defesa contra Pseudomonas

```
Flagelina (PAMP)
    |
    v
FLS2 (receptor) + BAK1
    |
    v
MAPK cascade (MPK3, MPK6)
    |
    v
WRKY TFs (WRKY33, WRKY29)
    |
    v
Genes de defesa (PR1, PR2, FRK1)
    |
    v
Producao de SA e Calose
```

### Via 2: Efetor suprimindo defesa

```
Efetor AvrPto (Pseudomonas)
    |
    v
Inibe quinases FLS2/BAK1
    |
    v
Bloqueia MAPK cascade
    |
    v
Reducao de defesa
    |
    v
Maior susceptibilidade
```

### Via 3: Reconhecimento e HR

```
Efetor AvrRpt2 (Pseudomonas)
    |
    v
Reconhecido por RPS2 (proteina R)
    |
    v
Ativacao de NDR1
    |
    v
Cascata de sinalizacao
    |
    v
Burst oxidativo (ROS)
    |
    v
Morte celular (HR)
    |
    v
Confinamento do patogeno
```

---

## Proximos Passos Biologicos

1. **Baixar transcriptoma de N. benthamiana** infectada
2. **Identificar genes diferencialmente expressos**
3. **Inferir GRN** das condicoes infectado vs controle
4. **Mapear efetores conhecidos** na rede
5. **Simular** knockouts e visualizar consequencias

---

## Referencias para Estudo

**Artigos fundamentais:**
1. Goodin et al. (2008) - "Nicotiana benthamiana: Its History and Future as a Model"
2. Jones & Dangl (2006) - "The plant immune system" (Nature Reviews)
3. Kourelis & van der Hoorn (2018) - "Defended to the Nines: Plant Immune Receptors"

**Livros:**
- "Molecular Plant Pathology" - Dickinson & Lucas
- "Plant Pathology" - Agrios

**Cursos online:**
- Coursera: "Plant Bioinformatics"
- EMBL-EBI Training: "Functional Genomics"
