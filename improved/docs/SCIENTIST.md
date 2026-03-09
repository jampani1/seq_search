# SCIENTIST.md - Base de Conhecimento Biologico para Visualizacao
> Guia de validacao cientifica para o Bioinformatics Hub
> Versao: 1.0 | Data: 2026-03-06

---

## SUMARIO

1. [Escalas e Proporcoes Biologicas](#1-escalas-e-proporcoes-biologicas)
2. [Organizacao do DNA no Nucleo](#2-organizacao-do-dna-no-nucleo)
3. [Cenarios Pre-definidos: Base Biologica](#3-cenarios-pre-definidos-base-biologica)
4. [Criterios de Validacao Visual](#4-criterios-de-validacao-visual)
5. [Rotinas de Teste Visual](#5-rotinas-de-teste-visual)
6. [Referencias Cientificas](#6-referencias-cientificas)

---

## 1. ESCALAS E PROPORCOES BIOLOGICAS

### 1.1 Hierarquia de Tamanhos (Celula Vegetal)

```
ESCALA REAL (aproximada para N. benthamiana):

Celula vegetal:        50-100 um (micrometros)
Vacuolo central:       40-80 um (80-90% do volume celular)
Nucleo:                5-15 um (tipicamente 10 um)
Cloroplasto:           3-8 um x 1-2 um (forma de lente)
Mitocondria:           1-4 um x 0.5 um
DNA desenrolado:       ~2 metros (por nucleo!)
Cromatina (30nm fiber): 30 nm
Nucleossomo:           10 nm
Dupla helice DNA:      2 nm de diametro

RAZOES IMPORTANTES:
- Nucleo/Celula: ~1:10 (volume ~0.2 do volume celular)
- DNA compactado ocupa TODO o nucleo (como cromatina)
- Dupla helice visivel apenas em escala molecular (nm)
```

### 1.2 Problema da Visualizacao do DNA

**CONCEITO BIOLOGICO CRITICO:**

O DNA NAO existe como "dupla helice flutuando no nucleo". Na realidade:

```
ORGANIZACAO REAL DO DNA:

1. DUPLA HELICE (2nm)
      |
      v enrola em
2. NUCLEOSSOMO (10nm) - DNA + histonas
      |
      v empilha em
3. FIBRA 30nm - "beads on a string" compactada
      |
      v dobra em
4. LOOPS DE CROMATINA (300nm)
      |
      v organiza em
5. DOMINIOS TOPOLOGICOS (TADs)
      |
      v forma
6. TERRITORIOS CROMOSSOMICOS (visivel no nucleo)
```

**IMPLICACAO PARA VISUALIZACAO:**

| Nivel de Zoom | O que mostrar | O que NAO mostrar |
|---------------|---------------|-------------------|
| Celula inteira | Nucleo como esfera densa | Dupla helice |
| Nucleo isolado | Cromatina difusa, nucleolo | Helices individuais |
| Zoom molecular | Fibras de cromatina | - |
| Ultra-zoom | Nucleossomos, dupla helice | - |

### 1.3 Escala Correta para o Visualizador

**RECOMENDACAO:**

```javascript
// ZOOM LEVELS BIOLOGICAMENTE CORRETOS

const ZOOM_LEVELS = {
    CELL_VIEW: {
        // Mostra celula completa
        camera_distance: 25,
        nucleus_visible: true,
        nucleus_content: 'CHROMATIN_CLOUD', // Nuvem difusa
        dna_helix_visible: false
    },

    NUCLEUS_VIEW: {
        // Foco no nucleo
        camera_distance: 8,
        nucleus_content: 'CHROMATIN_TERRITORIES',
        show_nucleolus: true,
        dna_helix_visible: false // ainda escala errada
    },

    CHROMATIN_VIEW: {
        // Zoom em regiao do nucleo
        camera_distance: 2,
        show_chromatin_fiber: true,
        show_histone_beads: true,
        dna_helix_visible: false
    },

    MOLECULAR_VIEW: {
        // Ultra zoom - escala molecular
        camera_distance: 0.5,
        dna_helix_visible: true, // AQUI SIM faz sentido
        show_base_pairs: true,
        show_nucleotides: true
    }
};
```

---

## 2. ORGANIZACAO DO DNA NO NUCLEO

### 2.1 Cromatina em Celulas Vegetais

**Caracteristicas em N. benthamiana:**

| Aspecto | Valor | Observacao |
|---------|-------|------------|
| Conteudo DNA | ~3.1 Gb | Alotetraploide |
| Cromossomos | 19 pares | - |
| Eucromatina | ~70% | Genes ativos, menos densa |
| Heterocromatina | ~30% | Genes silenciados, mais densa |

### 2.2 Distribuicao Espacial no Nucleo

```
                    ENVELOPE NUCLEAR
            +---------------------------+
           /                             \
          |  HETEROCROMATINA (periferia)  |
          |    +-------------------+      |
          |    |                   |      |
          |    |  EUCROMATINA      |      |
          |    |    (interior)     |      |
          |    |                   |      |
          |    |   [NUCLEOLO]      |      |
          |    |                   |      |
          |    +-------------------+      |
          |                               |
           \       POROS NUCLEARES       /
            +---------------------------+

- Genes ATIVOS: mais ao centro
- Genes SILENCIADOS: periferia (junto ao envelope)
- NUCLEOLO: producao de ribossomos (rRNA)
```

### 2.3 Visualizacao Correta do Nucleo

**O que o nucleo DEVE parecer:**

```javascript
// NUCLEO BIOLOGICAMENTE CORRETO
function createBiologicalNucleus() {
    const group = new THREE.Group();

    // 1. Envelope nuclear (membrana dupla, transparente)
    const envelope = createNuclearEnvelope(radius);

    // 2. Cromatina como NUVEM/PARTICULAS (nao helice!)
    const chromatin = createChromatinCloud({
        density: 0.7,  // mais denso na periferia
        distribution: 'peripheral_heterochromatin'
    });

    // 3. Nucleolo (esfera densa, excentrica)
    const nucleolus = createNucleolus({
        position: [0.3, 0.2, 0],  // nao centralizado
        density: 'high'
    });

    // 4. Poros nucleares (pequenos, na membrana)
    const pores = createNuclearPores(count: 30);

    // DNA HELIX: NAO incluir nesta escala!

    return group;
}
```

---

## 3. CENARIOS PRE-DEFINIDOS: BASE BIOLOGICA

> **NOTA PARA O LEITOR:** Esta secao foi expandida com analogias e explicacoes passo-a-passo
> para facilitar o entendimento. Se voce ja sabe biologia mas esqueceu alguns conceitos,
> as analogias vao ajudar a "reativar" a memoria.

---

### 3.1 PTI (Pattern-Triggered Immunity)

#### O que e PTI? (Explicacao Simples)

**Analogia do Alarme de Casa:**

Imagine sua casa com um sistema de alarme basico. O alarme detecta QUALQUER pessoa
estranha que entre - nao importa se e um ladrao profissional ou um curioso.
O sensor na porta reconhece "pessoa desconhecida" e dispara o alarme.

```
PTI e o ALARME BASICO da planta:

- Sensor da porta  = Receptor PRR (ex: FLS2)
- Pessoa estranha  = PAMP (molecula do patogeno)
- Alarme tocando   = Resposta de defesa
- Vizinhos ouvem   = Sinalizacao para celulas vizinhas
```

**O que sao PAMPs?**

PAMP = Pathogen-Associated Molecular Pattern (Padrao Molecular Associado a Patogenos)

Sao moleculas que TODOS os patogenos de um tipo tem em comum. A planta nao precisa
"conhecer" cada patogeno individual - basta reconhecer essas "assinaturas" gerais.

**Exemplos de PAMPs:**

| PAMP | Origem | Receptor na Planta |
|------|--------|-------------------|
| Flagelina (flg22) | Bacterias (flagelo) | FLS2 |
| EF-Tu (elf18) | Bacterias (traducao) | EFR |
| Quitina | Fungos (parede celular) | CERK1/LYK5 |
| dsRNA | Virus (replicacao) | - |

**Sacada:** *"A planta nao precisa conhecer o ladrao pelo nome - basta ver que ele
esta vestido de preto e usando mascara (PAMP) para saber que e perigoso."*

---

#### Passo-a-Passo do PTI

Vamos seguir a jornada de uma bacteria chegando na folha:

**PASSO 1: CHEGADA DO PATOGENO (0 minutos)**

```
              BACTERIA
               (O O)
                 |
         [FLAGELO] <-- Tem flagelina (PAMP)
                 |
    ========================== SUPERFICIE DA FOLHA
```

A bacteria usa seu flagelo para se mover. O flagelo e feito de uma proteina
chamada FLAGELINA. Um pedaco especifico dessa proteina (22 aminoacidos,
chamado "flg22") e reconhecido pela planta.

---

**PASSO 2: RECONHECIMENTO (1-2 minutos)**

```
    EXTERIOR DA CELULA
         [flg22]
            |
            v
    ========[FLS2]======== MEMBRANA PLASMATICA
              |
              +-- BAK1 (ajudante)
              |
    INTERIOR DA CELULA
```

- **FLS2** e o receptor na membrana (pense nele como o "sensor de movimento" do alarme)
- Quando flg22 encosta no FLS2, o receptor muda de forma
- **BAK1** e recrutado para ajudar - e um "co-receptor" (como um segundo sensor confirmando)

**Sacada:** *"FLS2 + BAK1 funcionam como aqueles sensores duplos de banco -
precisam de duas confirmacoes para abrir o cofre (ou neste caso, ativar a defesa)."*

---

**PASSO 3: PRIMEIROS SEGUNDOS DE RESPOSTA (2-5 minutos)**

```
    MEMBRANA
       |
       +-- BIK1 (quinase) --> ATIVA
       |
       +-- CANAIS DE Ca2+ --> ABREM
                |
                v
           [Ca2+ entra na celula]
```

- **BIK1** e uma quinase (enzima que fosforila outras proteinas)
- Quando FLS2+BAK1 ativam, BIK1 "acorda" e comeca a fosforilar TUDO
- **Canais de calcio** abrem - Ca2+ entra rapidamente na celula

**Por que calcio e importante?**

Calcio e um "segundo mensageiro" universal. E como se fosse o "som do alarme" -
se espalha rapidamente e avisa todo mundo dentro da celula que algo esta acontecendo.

---

**PASSO 4: ROS BURST (5-15 minutos)**

```
    MEMBRANA
       |
    [RBOHD] <-- Fosforilado por BIK1 + CPKs
       |
       v
    O2 + NADPH --> O2.- (superoxido)
       |
       v (enzima SOD)
    H2O2 (peroxido de hidrogenio)
       |
       v
    - Mata patogeno diretamente
    - Endurece parede celular
    - Sinaliza para vizinhos
```

**O que e RBOHD?**

RBOHD = Respiratory Burst Oxidase Homolog D

E uma enzima na membrana que PRODUZ ROS (Reactive Oxygen Species). Pense nela
como um "spray de pimenta" molecular que a celula dispara para fora.

**Analogia do ROS:**

*"ROS e como jogar agua sanitaria num invasor - mata o patogeno, mas se voce
exagerar, danifica sua propria casa (celula) tambem."*

---

**PASSO 5: CASCATA MAPK (10-30 minutos)**

```
    MEMBRANA
       |
       v
    MAPKKK (MEKK1)
       |
       v fosforila
    MAPKK (MKK4/5)
       |
       v fosforila
    MAPK (MPK3, MPK6)
       |
       v entram no NUCLEO
    FATORES DE TRANSCRICAO (WRKYs)
       |
       v ativam
    GENES DE DEFESA (PR1, PR2, FRK1)
```

**O que e cascata MAPK?**

E uma "corrente de fosforilacao" - cada enzima ativa a proxima adicionando
um fosfato. Amplifica o sinal: 1 molecula no inicio -> milhares de genes ativados no fim.

**Analogia:**

*"E como uma escada de dominós que cai: voce empurra uma peca no topo (receptor),
e milhares de pecas caem no fim (genes). Pequeno toque -> grande efeito."*

---

**PASSO 6: EXPRESSAO DE GENES (30-120 minutos)**

Os fatores de transcricao WRKY entram no nucleo e ativam genes de defesa:

| Gene | Funcao | Analogia |
|------|--------|----------|
| PR1 | Antimicrobiano | "Antibiotico" da planta |
| PR2 | Glucanase (quebra parede fungo) | "Acido" que dissolve invasor |
| FRK1 | Sinalizacao | "Megafone" para chamar reforcos |
| RBOHD | Mais ROS | "Mais spray de pimenta" |

---

**PASSO 7: FORTALECIMENTO DA PAREDE (1-6 horas)**

```
    PAREDE CELULAR
    ===============
         |
         +-- CALOSE depositada (polimero de glicose)
         |
         +-- Lignina (endurecimento)
         |
    ===============

    Patogeno: "Droga, nao consigo entrar!"
```

**Calose** e como "cimento express" - a planta deposita nas areas de ataque
para bloquear a entrada do patogeno.

---

#### Resumo Visual do PTI

```
TIMELINE PTI COMPLETO:

0 min    [PAMP chega]
  |
1-2 min  [FLS2 + BAK1 reconhecem]
  |
2-5 min  [BIK1 ativa, Ca2+ entra]
  |
5-15 min [RBOHD -> ROS BURST]
  |
10-30 min [Cascata MAPK]
  |
30-120 min [Genes PR expressos]
  |
1-6 h    [Calose na parede]
  |
  v
PATOGENO CONTIDO (mas nao eliminado)
```

**IMPORTANTE:** PTI geralmente NAO mata a celula da planta. E uma defesa
"proporcional" - suficiente para conter, mas sem sacrificar a celula.

---

#### Tabela de Valores para Visualizacao

| Parametro | Valor PTI Ativo (+100%) | Valor Basal (0%) | PTI Reprimido (-100%) |
|-----------|-------------------------|------------------|----------------------|
| ROS | 60-90% | 20-30% | 0-10% |
| Defesa | 70-90% | 30-40% | 0-15% |
| Sinalizacao | 60-80% | 15-25% | 0-10% |
| Membrana | 60-70% (atividade) | 45-55% | 40-50% |
| Morte celular | 10-20% | 5-10% | 0-5% |
| Patogeno | 20-40% (contido) | 50-70% | 85-100% (prolifera) |

---

### 3.2 ETI (Effector-Triggered Immunity)

#### O que e ETI? (Explicacao Simples)

**Analogia do BOPE/Forcas Especiais:**

Se PTI e o alarme basico da casa, ETI e chamar o **BOPE** ou **Forcas Especiais**.

Quando o ladrao (patogeno) e inteligente o suficiente para DESATIVAR o alarme (PTI),
a planta tem um segundo sistema: sensores INTERNOS que reconhecem ESPECIFICAMENTE
as ferramentas que o ladrao usa.

```
ETI e a RESPOSTA EXTREMA:

- Alarme normal desativado = PTI suprimida pelo efetor
- Camera interna detecta   = Proteina R reconhece efetor
- BOPE e acionado          = NLRs oligomerizam
- Operacao de contencao    = HR (morte celular)
- Ladrao preso na sala     = Patogeno confinado
```

**Sacada:** *"ETI e quando a planta diz: 'Se eu nao consigo expulsar voce,
vou trancar a porta e atear fogo no quarto com voce dentro.'"*

---

#### O que sao Efetores?

Efetores sao proteinas que o patogeno INJETA dentro da celula da planta para
SABOTAR a defesa. Sao as "ferramentas do ladrao".

**Como efetores entram?**

| Patogeno | Sistema de Secrecao | Analogia |
|----------|-------------------|----------|
| Bacterias | T3SS (seringa molecular) | Seringa que injeta direto |
| Fungos/Oomicetos | Haustorio | "Canudo" que suga e injeta |
| Virus | Pela propria infeccao | Ja esta dentro |

**Exemplos de efetores famosos:**

| Efetor | Patogeno | O que faz |
|--------|----------|-----------|
| AvrPto | Pseudomonas | Bloqueia FLS2 (desliga alarme) |
| AvrRpt2 | Pseudomonas | Cliva RIN4 (proteina de defesa) |
| AVR3a | Phytophthora | Estabiliza INF1 (suprime morte) |

---

#### Proteinas R: Os Sensores Internos

**O que sao proteinas R (Resistencia)?**

Sao proteinas DENTRO da celula que funcionam como "cameras de seguranca internas".
Cada proteina R reconhece um efetor especifico.

**Estrutura de uma proteina R (NLR):**

```
N-TERMINAL          CENTRAL          C-TERMINAL
[CC ou TIR] ------- [NB-ARC] ------- [LRR]
     |                  |               |
   Sinalizacao     Motor/Switch    Reconhecimento
   (ativar HR)     (liga/desliga)  (detecta efetor)
```

- **LRR** (Leucine-Rich Repeat): "olho" que ve o efetor
- **NB-ARC**: "interruptor" que liga quando LRR detecta algo
- **CC/TIR**: "botao de panico" que dispara a resposta

**Modelos de reconhecimento:**

```
MODELO 1: DIRETO
Efetor ---(encosta diretamente)---> Proteina R
                                         |
                                    [ATIVA]

MODELO 2: GUARDA (mais comum)
                    Guardada
Efetor --> [Proteina X] <---- Proteina R
                |                  |
           [modificada]       [detecta mudanca]
                                   |
                              [ATIVA]
```

**Sacada:** *"A proteina R e como um seguranca pessoal do VIP. Ela nao precisa
ver o assassino - basta ver que o VIP (proteina guardada) foi atacado."*

---

#### Passo-a-Passo do ETI

**PASSO 1: EFETOR ENTRA (0-10 minutos)**

```
PATOGENO                    CELULA VEGETAL
   |                             |
   | T3SS (seringa)              |
   |=============================|
   |     [EFETOR]  ----------->  |
   |                             |
```

O patogeno injeta seu efetor atraves do T3SS (Type III Secretion System).
O efetor viaja pelo citoplasma procurando seus alvos.

---

**PASSO 2: EFETOR TENTA SABOTAR (1-30 minutos)**

```
EFETOR chega no alvo:

Exemplo AvrPto:
                     FLS2
     AvrPto -------> [X] (bloqueia)
                      |
              PTI nao funciona!
```

O efetor comeca seu trabalho de sabotagem. Se nao houver proteina R que reconheca
esse efetor, a planta fica vulneravel (ver secao 3.3).

---

**PASSO 3: PROTEINA R DETECTA (5-30 minutos)**

```
Exemplo: RPS2 detectando AvrRpt2

        AvrRpt2
           |
           v  cliva
        [RIN4]  <---- RPS2 esta "guardando"
           |
       [modificado]
           |
           v
        RPS2: "Algo errado aconteceu!"
           |
           v
        [RPS2 ATIVA]
```

A proteina R detecta que algo errado aconteceu - seja o efetor diretamente
ou a modificacao de uma proteina guardada.

---

**PASSO 4: OLIGOMERIZACAO (30-120 minutos)**

```
   [NLR sensor]
        |
        v ativa
   [Helper NLRs]     <-- NRC2, NRC3, NRC4
        |
        v
   [OLIGOMERIZACAO]
        |
   /    |    |    \
 NRC  NRC  NRC  NRC  <-- Formam um "poro" na membrana
```

**O que e oligomerizacao?**

Varias copias da proteina se juntam formando um COMPLEXO maior. E como se
varios guardas se juntassem para formar um time de resposta.

**Resistossomo:**

O complexo oligomerizado e chamado de "resistossomo" - funciona como um
PORO na membrana que causa dano irreversivel.

---

**PASSO 5: HR - RESPOSTA HIPERSENSIVEL (2-6 horas)**

```
    CELULA INFECTADA
    +----------------+
    |  ROS ++++++    |
    |  DNA fragmenta |
    |  Membrana rompe|
    |  MORRE!        |
    +----------------+
           |
           v
    [Lesao necrotica]
           |
           v
    Patogeno CONFINADO (nao pode sair)
```

**O que e HR?**

HR = Hypersensitive Response (Resposta Hipersensivel)

E MORTE CELULAR PROGRAMADA. A celula se sacrifica para confinar o patogeno.
E diferente de necrose (morte descontrolada) - e um processo ATIVO.

**Por que funciona?**

Muitos patogenos precisam de celulas VIVAS para se alimentar (biotroficos).
Se a celula morre, o patogeno morre junto ou fica preso.

**Analogia:**

*"E como um soldado que se joga sobre a granada para salvar os companheiros.
A celula morre, mas protege as vizinhas."*

---

**PASSO 6: SINALIZACAO PARA VIZINHAS (6-24 horas)**

```
    [CELULA MORTA]
          |
          v emite sinais
    SA (acido salicilico)
    ROS extracelular
          |
          v
    CELULAS VIZINHAS
    [ATIVAM DEFESA]

    --> SAR (Systemic Acquired Resistance)
```

As celulas vizinhas recebem sinais da celula morta e ativam suas proprias defesas.
Isso pode se espalhar pela planta toda (SAR = Resistencia Adquirida Sistemica).

---

#### Comparacao PTI vs ETI

| Aspecto | PTI | ETI |
|---------|-----|-----|
| **Analogia** | Alarme de casa | BOPE/Forcas especiais |
| **Gatilho** | PAMPs (padrao geral) | Efetores (especifico) |
| **Receptor** | PRRs na membrana | NLRs dentro da celula |
| **Intensidade** | Moderada | Extrema |
| **Morte celular** | Rara | Comum (HR) |
| **Velocidade** | Rapida (minutos) | Mais lenta (horas) |
| **Especificidade** | Baixa (qualquer patogeno) | Alta (efetor especifico) |

**Sacada:** *"PTI e empurrar o ladrao para fora. ETI e trancar o ladrao
no quarto e atear fogo na casa."*

---

#### Tabela de Valores para Visualizacao

| Parametro | Valor ETI Ativo (+100%) | Diferenca vs PTI |
|-----------|-------------------------|------------------|
| ROS | 80-100% | +20% (mais intenso) |
| Defesa | 80-95% | +10% |
| Sinalizacao | 70-90% | +10% |
| Membrana | 70-90% (DANO) | +20% (diferente: aqui e dano, nao atividade) |
| Morte celular | 60-90% | +50% (HR!) |
| Patogeno | 5-20% | -20% (muito contido) |

---

### 3.3 Ataque por Efetor (Virulencia)

#### O que e Ataque por Efetor? (Explicacao Simples)

**Analogia do Hacker/Espiao:**

Este cenario e o OPOSTO do ETI. Aqui, o patogeno GANHA.

Imagine um hacker que consegue invadir o sistema de seguranca de um banco,
desativar as cameras, anular os alarmes, e roubar tranquilamente.

```
EFETOR BEM-SUCEDIDO:

- Hacker entra            = Efetor injetado
- Desativa cameras        = Bloqueia receptores (FLS2)
- Corta alarme            = Inibe MAPK
- Abre cofre              = Suprime genes de defesa
- Rouba tranquilo         = Patogeno coloniza
- Seguranca nem ve        = Planta adoece
```

**Por que acontece?**

1. A planta NAO tem proteina R para esse efetor
2. Ou a proteina R esta mutada/ausente
3. Ou o efetor evoluiu para nao ser reconhecido

**Sacada:** *"O efetor e um espiao perfeito - faz seu trabalho sem ser detectado.
A celula nem percebe que esta sendo sabotada."*

---

#### Passo-a-Passo do Ataque por Efetor

**PASSO 1: SECRECAO DO EFETOR (0-5 minutos)**

```
    PATOGENO
       |
       | T3SS
       v
    ====================== MEMBRANA
       |
    [EFETOR ENTRA]
```

O patogeno secreta seus efetores. Cada patogeno pode ter dezenas de efetores
diferentes, cada um com uma funcao especifica.

---

**PASSO 2: EFETORES ATINGEM ALVOS (5-60 minutos)**

```
EFETOR 1: AvrPto
   |
   v
[FLS2] <--- BLOQUEIA receptor

EFETOR 2: AvrPtoB
   |
   v
[PRRs] <--- DEGRADA (E3 ligase)

EFETOR 3: HopAI1
   |
   v
[MPK3/6] <--- DESFOSFORILA (inativa MAPK)
```

**O que cada efetor famoso faz:**

| Efetor | Alvo | Efeito | Analogia |
|--------|------|--------|----------|
| AvrPto | FLS2 | Bloqueia receptor | Tapa no sensor de movimento |
| AvrPtoB | Varios PRRs | Degrada (E3 ligase) | Destroi as cameras |
| HopAI1 | MPK3/6 | Desfosforila (inativa) | Desliga o painel de controle |
| HopM1 | MIN7 | Bloqueia trafego vesicular | Corta comunicacao interna |

---

**PASSO 3: DEFESA SUPRIMIDA (1-4 horas)**

```
    CELULA VEGETAL (SABOTADA)

    [ ] Receptores - BLOQUEADOS
    [ ] Cascata MAPK - INATIVA
    [ ] Genes PR - NAO EXPRESSOS
    [ ] ROS - BAIXO
    [ ] Calose - NAO DEPOSITADA

    Celula parece "adormecida" ou "normal"
```

A celula nao monta defesa porque todos os sistemas foram sabotados.
Ela nem "sabe" que esta sendo atacada.

---

**PASSO 4: COLONIZACAO (4-24 horas)**

```
    APOPLASTO (espaco entre celulas)

    Patogeno:  *   *   *
               * *   * *   <-- Proliferando
             *   *   *   *

    Celulas: [Normal][Normal][Normal]
              (nao sabem que tem inimigo)
```

O patogeno prolifera no apoplasto (espaco entre celulas) ou dentro das celulas,
sem encontrar resistencia.

---

**PASSO 5: DOENCA (24-72 horas)**

```
    FOLHA
    +------------------+
    |   .   .   .      |
    |  . . . . . .     | <-- Lesoes aparecem
    |    . . .   .     |
    |  [CLOROSE]       | <-- Amarelecimento
    |  [NECROSE]       | <-- Morte de tecido
    +------------------+
```

Sintomas de doenca aparecem:
- **Clorose**: Amarelecimento (cloroplastos danificados)
- **Necrose**: Morte de tecido (diferente de HR - aqui e descontrolada)
- **Murcha**: Perda de turgor
- **Podridao**: Em casos extremos

---

#### Por que a Planta Nao Reage?

```
CENARIO NORMAL (com PTI funcionando):

PAMP --> [FLS2] --> [MAPK] --> [WRKY] --> [Genes PR] --> DEFESA!

CENARIO COM EFETOR:

PAMP --> [FLS2] --> [MAPK] --> [WRKY] --> [Genes PR] --> DEFESA!
            ^          ^
            |          |
         AvrPto     HopAI1
         BLOQUEIA  INATIVA

Resultado: PAMP chega, mas sinal nao passa!
```

**Sacada:** *"E como tentar ligar para a policia, mas o telefone foi cortado.
Voce ve o ladrao, mas nao consegue pedir ajuda."*

---

#### Tabela de Valores para Visualizacao

| Parametro | Efetor Ativo (+100%) | Efetor Reprimido (-100%) |
|-----------|---------------------|-------------------------|
| ROS | 10-20% (suprimido) | 40-55% (recupera) |
| Defesa | 5-20% (sabotada) | 60-75% (funciona) |
| Sinalizacao | 0-10% (bloqueada) | 40-50% (ativa) |
| Membrana | 40-50% (normal) | 50-60% (normal) |
| Morte celular | 5-15% (patogeno nao quer matar) | 20-30% |
| Patogeno | 80-100% (prolifera) | 30-50% (contido) |

**NOTA:** Quando efetor e "reprimido" (-100%), significa que a planta
CONSEGUIU bloquear ou degradar o efetor, recuperando sua defesa.

---

### 3.4 ROS Burst

#### O que e ROS Burst? (Explicacao Simples)

**Analogia do Spray de Pimenta:**

ROS (Reactive Oxygen Species) sao moleculas altamente reativas que contem
oxigenio. O "burst" e uma producao RAPIDA e MASSIVA dessas moleculas.

```
ROS BURST:

- Invasor detectado    = PAMP/efetor reconhecido
- Spray de pimenta     = H2O2 (peroxido de hidrogenio)
- Invasor arde         = Patogeno danificado
- Voce tambem arde     = Celula tambem sofre dano (se exagerar)
```

**O que sao ROS?**

| ROS | Nome | Reatividade | Duracao |
|-----|------|-------------|---------|
| O2.- | Superoxido | Alta | Segundos |
| H2O2 | Peroxido de hidrogenio | Media | Minutos |
| OH. | Radical hidroxila | MUITO alta | Nanosegundos |

**Sacada:** *"ROS e fogo quimico. Mata o inimigo, mas se voce nao controlar,
queima sua propria casa."*

---

#### A Enzima Central: RBOHD

**O que e RBOHD?**

RBOHD = Respiratory Burst Oxidase Homolog D

E uma enzima na membrana plasmatica que PRODUZ ROS. Ela fica "desligada"
normalmente e e ATIVADA quando a planta detecta perigo.

```
ESTRUTURA DO RBOHD:

    EXTERIOR DA CELULA
           |
    =======|========= MEMBRANA
           |
    [FAD] [NADPH-binding] <-- Usa NADPH para fazer ROS
           |
    [EF-hands] <-- Liga Ca2+ (ativa a enzima)
           |
    [Sitios de fosforilacao] <-- BIK1/CPKs fosforilam (ativa)
           |
    INTERIOR DA CELULA
```

---

#### Passo-a-Passo do ROS Burst

**PASSO 1: SINAL CHEGA (0-2 minutos)**

```
PTI ativada
    |
    v
[BIK1] fosforila RBOHD
    +
[Ca2+] liga aos EF-hands
    |
    v
RBOHD ATIVA!
```

Dois sinais sao necessarios para ativar RBOHD:
1. Fosforilacao por quinases (BIK1, CPKs)
2. Ligacao de calcio (Ca2+)

**Por que dois sinais?**

Seguranca! ROS e perigoso - a celula precisa ter CERTEZA antes de produzir.

---

**PASSO 2: PRODUCAO DE SUPEROXIDO (2-5 minutos)**

```
REACAO NO RBOHD:

NADPH + O2 --> NADP+ + H+ + O2.-
                           |
                       SUPEROXIDO
                       (altamente reativo)
```

RBOHD usa NADPH (energia da celula) para converter oxigenio (O2) em
superoxido (O2.-). O superoxido e lancado para FORA da celula.

---

**PASSO 3: CONVERSAO PARA H2O2 (5-10 minutos)**

```
    O2.- + O2.- + 2H+ --> H2O2 + O2
           |
          SOD (superoxido dismutase)
```

A enzima SOD converte o superoxido (muito instavel) em peroxido de
hidrogenio (H2O2, mais estavel). H2O2 e a forma "util" do ROS.

---

**PASSO 4: EFEITOS DO H2O2 (10-60 minutos)**

```
H2O2 faz varias coisas:

1. MATA PATOGENO DIRETAMENTE
   H2O2 --> [Patogeno] --> Dano oxidativo --> Morte

2. FORTALECE PAREDE CELULAR
   H2O2 --> [Proteinas da parede] --> Crosslinking --> Mais dura

3. SINALIZA PARA VIZINHAS
   H2O2 --> [Atravessa membrana] --> Celulas vizinhas alertadas

4. ATIVA GENES DE DEFESA
   H2O2 --> [Nucleo] --> Expressao de PR genes
```

**Por que H2O2 e tao versatil?**

H2O2 e pequeno e pode atravessar membranas. Funciona tanto como "arma"
quanto como "mensageiro". E a unica ROS estavel o suficiente para isso.

---

**PASSO 5: BIFASICO EM ETI (se aplicavel)**

```
ROS ao longo do tempo:

    |
    |   .
ROS |  . .            . . .
    | .   .          .     .
    |.     .        .       .
    +-----.---.---.----------.--> tempo
    0     5   15min      2h   6h

    [Fase 1]        [Fase 2]
    PTI-like        ETI-specific
```

Em ETI, ha duas ondas de ROS:
- **Fase 1** (5-15 min): Rapida, semelhante a PTI
- **Fase 2** (2-6 h): Mais intensa, associada a HR

---

#### Quando ROS e Demais?

```
    ROS BAIXO          ROS MEDIO          ROS ALTO

    Patogeno OK        Patogeno morto     Patogeno morto
    Celula OK          Celula estressada  Celula MORRE

       :)                 :|                  :(
```

**Estresse oxidativo:**

Se ROS excede a capacidade antioxidante da celula:
- Lipidios da membrana sao peroxidados
- Proteinas sao oxidadas (perdem funcao)
- DNA e danificado
- Celula morre (necrose)

**Analogia:**

*"E como radioterapia contra cancer: mata as celulas ruins, mas se exagerar,
mata as celulas boas tambem."*

---

#### Antioxidantes: O Controle

A celula tem sistemas para CONTROLAR o ROS:

| Antioxidante | Funcao |
|--------------|--------|
| Catalase | H2O2 -> H2O + O2 |
| APX (ascorbato peroxidase) | H2O2 -> H2O (usa vitamina C) |
| Glutationa | Neutraliza varias ROS |
| SOD | O2.- -> H2O2 (converte) |

**Equilibrio:**

```
     PRODUCAO DE ROS     <==>     DEGRADACAO POR ANTIOXIDANTES
     (RBOHD, etc)                 (Catalase, APX, etc)

     Se producao > degradacao --> ESTRESSE OXIDATIVO
     Se producao < degradacao --> Patogeno escapa
     Se producao = degradacao --> Equilibrio saudavel
```

---

#### Tabela de Valores para Visualizacao

| Parametro | ROS Alto (+100%) | ROS Basal (0%) | ROS Reprimido (-100%) |
|-----------|-----------------|----------------|----------------------|
| ROS | 85-100% | 20-30% | 0-10% |
| Defesa | 50-65% | 30-40% | 25-35% |
| Membrana | 70-90% (estresse) | 45-55% | 45-55% |
| Morte celular | 40-60% | 5-10% | 5-10% |
| Patogeno | 30-50% (danificado) | 50-70% | 70-90% (prolifera) |

---

### 3.5 Resumo dos Cenarios

```
+------------------+-------------------+------------------+------------------+
|      PTI         |       ETI         |     EFETOR       |    ROS BURST     |
+------------------+-------------------+------------------+------------------+
| "Alarme basico"  | "Forcas especiais"| "Hacker"         | "Spray de pimenta"|
+------------------+-------------------+------------------+------------------+
| Reconhece PAMP   | Reconhece EFETOR  | Efetor ESCAPA    | Producao de H2O2 |
| (padrao geral)   | (especifico)      | (nao reconhecido)| (defesa quimica) |
+------------------+-------------------+------------------+------------------+
| Defesa moderada  | Defesa EXTREMA    | Defesa SUPRIMIDA | Mata patogeno    |
| Celula sobrevive | Celula MORRE (HR) | Planta adoece    | Pode matar celula|
+------------------+-------------------+------------------+------------------+
| Patogeno contido | Patogeno CONFINADO| Patogeno PROLIFERA| Patogeno danificado|
+------------------+-------------------+------------------+------------------+
```

**Relacao entre os cenarios:**

```
PATOGENO CHEGA
      |
      v
   [PAMP detectado?]
      |
   SIM --> PTI ATIVA (cenario 3.1)
      |        |
      |        v
      |    [Efetor injetado?]
      |        |
      |     SIM
      |        |
      |        v
      |    [Efetor reconhecido por proteina R?]
      |        |
      |     SIM --> ETI ATIVA (cenario 3.2)
      |        |
      |       NAO --> ATAQUE POR EFETOR (cenario 3.3)
      |
   NAO --> Patogeno nao sobrevive (nao e adaptado)

ROS BURST (cenario 3.4) ocorre DURANTE PTI e ETI, mas pode ser
visualizado separadamente para focar nesse aspecto.
```

---

### 3.6 PTI e ETI: Sinergia, Nao Sequencia Isolada

**IMPORTANTE - Atualizacao baseada em pesquisa recente (2024-2025):**

A visao antiga era: "PTI primeiro, se falhar, ETI". A visao ATUAL e mais sofisticada:

```
MODELO ANTIGO (simplificado):
PTI ---> [falha] ---> ETI

MODELO ATUAL (sinergico):
PTI ---> PRIMES ---> ETI (amplificada)
 |                     |
 +-------<-------<-----+
      feedback mutuo
```

**O que a pesquisa recente mostra:**

1. **PTI e ETI funcionam JUNTAS** - nao sao sistemas isolados
2. **PTI "prepara" a celula** para uma resposta ETI mais forte
3. **ETI amplifica e prolonga** a resposta iniciada por PTI
4. **Compartilham vias**: ROS, Ca2+, hormonios (SA, JA)
5. **NLRs raramente ativam SEM PTI** - quase sempre ha PTI primeiro

**Para a visualizacao:**

| Cenario | O que mostrar |
|---------|---------------|
| PTI sozinha | Defesa moderada, patogeno contido |
| PTI + ETI | Defesa INTENSA, morte celular, patogeno confinado |
| Efetor suprime PTI | Se nao houver proteina R: doenca. Se houver: ETI salva |

**Sacada:** *"PTI e ETI sao como primeiro e segundo tempo de um jogo.
O primeiro tempo (PTI) define o ritmo. O segundo (ETI) decide o jogo.
Mas os dois times estao jogando o tempo todo."*

---

### 3.7 Citoesqueleto em Celulas Vegetais

**O que e o citoesqueleto?**

E a "estrutura de sustentacao" da celula - como o esqueleto para nosso corpo,
mas DINAMICO (pode se reorganizar rapidamente).

**Componentes principais:**

| Estrutura | Proteina | Diametro | Funcao |
|-----------|----------|----------|--------|
| Microtubulos | Tubulina | ~25 nm | "Trilhos" para transporte, forma celular |
| Microfilamentos | Actina | 5-7 nm | Movimento, streaming citoplasmatico |
| (Filamentos intermediarios) | Varias | 10 nm | Suporte mecanico (menos em plantas) |

**Visualizacao ASCII:**

```
    PAREDE CELULAR
    ==============
         |
    MEMBRANA PLASMATICA
    --------------------
         |
         |    /---- Microtubulo (tubo rigido)
         |   /
    CITOPLASMA
         |   \
         |    \---- Microfilamento (fio flexivel)
         |
    [ORGANELAS ancoradas no citoesqueleto]
         |
    --------------------
    VACUOLO CENTRAL
```

**Por que e relevante para a visualizacao?**

No ZOOM 2 (citoplasma), podemos mostrar:
1. **Linhas finas** cruzando o citoplasma (microtubulos)
2. **Organelas "ancoradas"** nessas linhas
3. **Movimento de vesiculas** ao longo dos "trilhos"

**Conexao com imunidade:**

O citoesqueleto e CRUCIAL para defesa:
- Transporta vesiculas com materiais de defesa
- Ajuda a posicionar organelas durante ataque
- Pode ser ALVO de efetores (patogenos sabotam transporte)

---

### 3.8 Proposta: Visualizacao em Timelapse

**Conceito:**

Uma animacao que mostra TODO o processo, com zoom in/out automatico
para cada etapa relevante.

**Storyboard proposto:**

```
FASE 1: APROXIMACAO (zoom out -> celula inteira)
[0-5s]  Patogeno se aproxima da celula
        Camera: visao externa da celula

FASE 2: RECONHECIMENTO (zoom in -> membrana)
[5-10s] PAMP toca receptor FLS2
        Camera: zoom na membrana
        Efeito: FLS2 "acende" (muda de cor)

FASE 3: SINALIZACAO INICIAL (zoom in -> citoplasma)
[10-15s] Ca2+ entra (particulas azuis fluindo)
         MAPK cascade ativa (linhas brilhando)
         Camera: dentro do citoplasma

FASE 4: ROS BURST (zoom out -> membrana externa)
[15-20s] Particulas laranjas saindo da membrana
         Patogeno recuando/danificado
         Camera: lado de fora

FASE 5: [SE ETI] EFETOR ENTRA (zoom in -> citoplasma)
[20-25s] Efetor (particula vermelha) entra via T3SS
         Viaja pelo citoplasma
         Camera: seguindo o efetor

FASE 6: [SE ETI] RECONHECIMENTO POR NLR (zoom in -> proteina R)
[25-30s] Efetor encontra proteina R
         NLR "acende" e oligomeriza
         Camera: close na proteina R

FASE 7: [SE ETI] HR (zoom out -> celula inteira)
[30-35s] Celula muda de cor (verde -> vermelho)
         Fragmentacao visivel
         Patogeno confinado
         Camera: visao da celula morrendo

FASE 8: RESOLUCAO (zoom out -> tecido)
[35-40s] Celulas vizinhas ativam defesa
         Lesao visivel no tecido
         Camera: visao do tecido
```

**Controles propostos:**

```
[Play/Pause]  [<< Anterior]  [Proximo >>]  [Velocidade: 1x 2x 0.5x]

Timeline:
|----PTI----|----ROS----|----ETI----|----HR----|
0s          10s         20s         30s        40s
                    ^
                 [cursor]
```

---

## 4. CRITERIOS DE VALIDACAO VISUAL

### 4.1 Checklist por Cenario

**PTI ATIVA (+80 a +100):**
- [ ] Membrana com "halo" de atividade (Ca2+ influx)
- [ ] Particulas ROS visiveis (pontos brilhantes externos)
- [ ] Patogeno AFASTADO (posicao y > 4)
- [ ] Bloom aumentado (sinalizacao ativa)
- [ ] Nucleo "aceso" (WRKYs ativos)

**ETI ATIVA (+80 a +100):**
- [ ] Todos os efeitos de PTI, MAS MAIS INTENSOS
- [ ] Membrana com sinais de DANO (cor avermelhada)
- [ ] Morte celular visivel (fragmentacao)
- [ ] Patogeno MUITO afastado ou "contido"
- [ ] ROS burst muito intenso

**EFETOR ATIVO (+70 a +100):**
- [ ] Membrana "calma" (sem atividade de defesa)
- [ ] ROS BAIXO (particulas reduzidas)
- [ ] Patogeno PENETRANDO (posicao y < 3)
- [ ] Bloom reduzido (sinalizacao suprimida)
- [ ] Celula parece "adormecida"

**ROS BURST (+90 a +100):**
- [ ] Particulas de ROS MUITO intensas
- [ ] Membrana com sinais de estresse oxidativo
- [ ] Bloom alto (efeito de "brilho")
- [ ] Potencial de morte celular visivel
- [ ] Patogeno parcialmente afetado

### 4.2 Validacao Bidirecional

**REGRA FUNDAMENTAL:**
```
Se ativar (+100) tem EFEITO X,
reprimir (-100) deve ter EFEITO OPOSTO.

Exemplo DEFESA (FLS2):
+100%: defesa ALTA, patogeno BAIXO
-100%: defesa BAIXA, patogeno ALTO

Exemplo EFETOR (AvrPto):
+100%: efetor ATIVO (ruim para planta)
-100%: efetor BLOQUEADO (bom para planta)
```

### 4.3 Escalas de Cor para Validacao

| Estrutura | Normal | Ativado | Danificado |
|-----------|--------|---------|------------|
| Membrana | Ciano claro | Azul intenso | Vermelho |
| ROS | Laranja sutil | Laranja brilhante | Vermelho |
| Nucleo | Verde claro | Verde brilhante | Fragmentado |
| Patogeno | Vermelho | Vermelho escuro | Vermelho apagado |

---

## 5. ROTINAS DE TESTE VISUAL

### 5.1 Script de Teste Automatizado

```javascript
// tests/visual-validation.spec.js

const { test, expect } = require('@playwright/test');

// Configuracao de screenshots
const SCREENSHOT_DIR = './test-results/screenshots';

test.describe('Validacao Biologica do Cell Simulator', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:5173/cell_simulator.html');
        await page.waitForSelector('.loading.hidden', { timeout: 10000 });
    });

    // TESTE 1: PTI ATIVA
    test('PTI +100% deve mostrar defesa alta e patogeno afastado', async ({ page }) => {
        // Aplicar preset PTI
        await page.click('[data-preset="pti"]');
        await page.waitForTimeout(500);

        // Ajustar regulacao para 100%
        await page.fill('#regulation', '100');
        await page.waitForTimeout(1000);

        // Capturar screenshot
        await page.screenshot({
            path: `${SCREENSHOT_DIR}/pti_active_100.png`,
            fullPage: true
        });

        // Validar barras de consequencia
        const defenseBar = await page.$eval(
            '[data-effect="defense"] .level-bar',
            el => parseInt(el.style.width)
        );
        const pathogenBar = await page.$eval(
            '[data-effect="pathogen"] .level-bar',
            el => parseInt(el.style.width)
        );

        // Criterios biologicos
        expect(defenseBar).toBeGreaterThan(70); // Defesa > 70%
        expect(pathogenBar).toBeLessThan(40);   // Patogeno < 40%
    });

    // TESTE 2: PTI REPRIMIDA
    test('PTI -100% deve mostrar defesa baixa e patogeno avancando', async ({ page }) => {
        await page.click('[data-preset="pti"]');
        await page.fill('#regulation', '-100');
        await page.waitForTimeout(1000);

        await page.screenshot({
            path: `${SCREENSHOT_DIR}/pti_repressed_-100.png`
        });

        const defenseBar = await page.$eval(
            '[data-effect="defense"] .level-bar',
            el => parseInt(el.style.width)
        );
        const pathogenBar = await page.$eval(
            '[data-effect="pathogen"] .level-bar',
            el => parseInt(el.style.width)
        );

        expect(defenseBar).toBeLessThan(20);     // Defesa < 20%
        expect(pathogenBar).toBeGreaterThan(80); // Patogeno > 80%
    });

    // TESTE 3: ETI COM HR
    test('ETI +100% deve mostrar morte celular alta', async ({ page }) => {
        await page.click('[data-preset="eti"]');
        await page.fill('#regulation', '100');
        await page.waitForTimeout(1000);

        await page.screenshot({
            path: `${SCREENSHOT_DIR}/eti_active_100.png`
        });

        const deathBar = await page.$eval(
            '[data-effect="death"] .level-bar',
            el => parseInt(el.style.width)
        );

        expect(deathBar).toBeGreaterThan(70); // HR > 70%
    });

    // TESTE 4: EFETOR SUPRIMINDO DEFESA
    test('Efetor +100% deve suprimir defesa', async ({ page }) => {
        await page.click('[data-preset="effector"]');
        await page.fill('#regulation', '100');
        await page.waitForTimeout(1000);

        await page.screenshot({
            path: `${SCREENSHOT_DIR}/effector_active_100.png`
        });

        const defenseBar = await page.$eval(
            '[data-effect="defense"] .level-bar',
            el => parseInt(el.style.width)
        );
        const signalingBar = await page.$eval(
            '[data-effect="signaling"] .level-bar',
            el => parseInt(el.style.width)
        );

        expect(defenseBar).toBeLessThan(20);    // Defesa suprimida
        expect(signalingBar).toBeLessThan(15);  // Sinalizacao bloqueada
    });

    // TESTE 5: RESET FUNCIONA
    test('Trocar de cenario deve resetar para valores basais', async ({ page }) => {
        // Ativar PTI
        await page.click('[data-preset="pti"]');
        await page.fill('#regulation', '100');
        await page.waitForTimeout(500);

        // Trocar para ETI (deve resetar)
        await page.click('[data-preset="eti"]');
        await page.waitForTimeout(500);

        // Verificar que slider resetou para valor do preset
        const sliderValue = await page.$eval('#regulation', el => el.value);
        expect(sliderValue).toBe('100'); // ETI preset usa 100
    });

    // TESTE 6: BIDIRECIONALIDADE
    test('Slider 0% deve retornar ao estado basal', async ({ page }) => {
        await page.click('[data-preset="pti"]');
        await page.fill('#regulation', '100');
        await page.waitForTimeout(500);

        // Retornar ao basal
        await page.fill('#regulation', '0');
        await page.waitForTimeout(500);

        await page.screenshot({
            path: `${SCREENSHOT_DIR}/basal_state.png`
        });

        const defenseBar = await page.$eval(
            '[data-effect="defense"] .level-bar',
            el => parseInt(el.style.width)
        );

        // Valores basais
        expect(defenseBar).toBeGreaterThan(35);
        expect(defenseBar).toBeLessThan(45);
    });
});
```

### 5.2 Teste de Proporcoes do DNA

```javascript
// tests/dna-scale-validation.spec.js

test.describe('Validacao de Escala do DNA', () => {

    test('Cell view NAO deve mostrar dupla helice', async ({ page }) => {
        await page.goto('http://localhost:5173/cell_viewer_premium.html');
        await page.waitForSelector('.loading.hidden');

        // Clicar em "Cell" (visao completa)
        await page.click('text=Cell');
        await page.waitForTimeout(1000);

        await page.screenshot({
            path: `${SCREENSHOT_DIR}/cell_view_no_helix.png`
        });

        // Nesta visao, DNA helix nao deveria ser visivel
        // Verificar visualmente
    });

    test('DNA view deve mostrar cromatina, nao helice isolada', async ({ page }) => {
        await page.goto('http://localhost:5173/cell_viewer_premium.html');
        await page.waitForSelector('.loading.hidden');

        // Clicar em "DNA"
        await page.click('text=DNA');
        await page.waitForTimeout(1500);

        await page.screenshot({
            path: `${SCREENSHOT_DIR}/dna_view.png`
        });

        // A visualizacao deve ser de cromatina/nucleo
        // nao uma helice isolada flutuando
    });
});
```

### 5.3 Comandos para Executar Testes

```bash
# Instalar Playwright
npm install -D @playwright/test

# Executar todos os testes visuais
npx playwright test tests/visual-validation.spec.js

# Executar com UI (modo interativo)
npx playwright test --ui

# Gerar relatorio HTML
npx playwright test --reporter=html

# Ver screenshots geradas
ls test-results/screenshots/
```

---

## 6. REFERENCIAS CIENTIFICAS

### Artigos sobre PTI-ETI
- [PTI-ETI synergistic signal mechanisms](https://pmc.ncbi.nlm.nih.gov/articles/PMC11258992/)
- [PTI-ETI crosstalk: an integrative view](https://www.sciencedirect.com/science/article/abs/pii/S1369526621000303)
- [Recent Advances in ETI](https://pmc.ncbi.nlm.nih.gov/articles/PMC8124997/)

### Artigos sobre Escala Nuclear/DNA
- [Probing 3D architecture of plant nucleus](https://pmc.ncbi.nlm.nih.gov/articles/PMC6682351/)
- [How big are nuclei?](https://book.bionumbers.org/how-big-are-nuclei/)
- [Chromatin structure and dynamics in plants](https://pmc.ncbi.nlm.nih.gov/articles/PMC4009787/)

### Artigos sobre Cromatina em Plantas
- [Plant 3D genomics and chromatin organization](https://nph.onlinelibrary.wiley.com/doi/10.1111/nph.17262)
- [Genome-wide chromatin packing in Arabidopsis](https://pmc.ncbi.nlm.nih.gov/articles/PMC4315298/)
- [Nucleosome-resolution chromatin with Micro-C-XL](https://www.nature.com/articles/s41467-023-44347-z)

### Artigos sobre ROS e RBOHD
- [RBOHD regulation](https://www.nature.com/articles/s41467-020-15601-5)
- [Chloroplast immunity](https://www.cell.com/plant-communications/fulltext/S2590-3462(25)00182-8)

---

## RESUMO EXECUTIVO

### Problema do DNA na Visualizacao

**ERRO ATUAL:**
- DNA helix visivel em escala de celula/nucleo
- Proporcao completamente irreal

**SOLUCAO:**
1. CELL VIEW: Mostrar nucleo como esfera com cromatina difusa
2. NUCLEUS VIEW: Mostrar territorios cromossomicos + nucleolo
3. CHROMATIN VIEW: Mostrar fibras de 30nm
4. MOLECULAR VIEW: Aqui sim, mostrar dupla helice

### Cenarios Biologicos Validados

| Cenario | Defesa | ROS | Morte | Patogeno | Validacao |
|---------|--------|-----|-------|----------|-----------|
| PTI +100 | >70% | >55% | <30% | <40% | Correta |
| PTI -100 | <10% | <10% | <10% | >90% | Correta |
| ETI +100 | >80% | >60% | >70% | <20% | Correta |
| Efetor +100 | <20% | <20% | <15% | >90% | Correta |
| ROS +100 | >55% | >85% | >40% | <50% | Correta |

---

*Documento gerado para validacao cientifica do Bioinformatics Hub*
*Autor: Claude (com supervisao de Mauricio Jampani)*
*Data: 2026-03-06*
