# FEATURES.md - Mapa de Funcionalidades

> Guia rapido para encontrar todas as features do Bioinformatics Hub

---

## Estrutura do Projeto

```
improved/
├── frontend/                    # Todas as visualizacoes
│   ├── index.html              # HUB CENTRAL - comece aqui!
│   ├── grn_viewer.html         # Rede GRN 2D (Cytoscape)
│   ├── grn_viewer_3d.html      # Rede GRN 3D (Three.js)
│   ├── grn_explorer.html       # Explorer avancado com filtros
│   ├── cell_viewer_3d.html     # Celula 3D - Primitivas
│   ├── cell_viewer_metaballs.html  # Celula 3D - Metaballs
│   ├── cell_viewer_premium.html    # Celula 3D - Efeitos avancados
│   └── cell_simulator.html     # SIMULADOR DE CONSEQUENCIAS
│
├── data/
│   ├── processed/              # Dados processados
│   │   ├── defense_network.json    # Rede de defesa (36 genes)
│   │   ├── nbenthamiana_genes.json # 61k genes
│   │   └── phibase_plant_effectors.json
│   ├── scripts/
│   │   └── process_data.py     # Scripts de processamento
│   └── DATA_SOURCES.md         # Fontes de dados
│
└── docs/
    ├── FEATURES.md             # VOCE ESTA AQUI
    ├── APRENDIZAGEM.md         # Diario tecnico
    ├── BIOLOGIC.md             # Fundamentos biologicos
    └── NBENTHAMIANA_DATABASE.md # Dados do organismo
```

---

## Features por Categoria

### 1. Visualizacao de Redes (GRN)

| Feature | Arquivo | Descricao |
|---------|---------|-----------|
| Rede 2D | `grn_viewer.html` | Cytoscape.js, layout organico |
| Rede 3D | `grn_viewer_3d.html` | Three.js, forcas 3D |
| Explorer | `grn_explorer.html` | Filtros, busca, modos de visualizacao |

**Como usar:**
1. Abra `grn_viewer.html` para visao geral
2. Use `grn_explorer.html` para analise detalhada
3. Use `grn_viewer_3d.html` para apresentacoes

### 2. Visualizacao Celular 3D

| Feature | Arquivo | Estilo |
|---------|---------|--------|
| Primitivas | `cell_viewer_3d.html` | Esferas, cilindros (leve) |
| Metaballs | `cell_viewer_metaballs.html` | Formas organicas (Spore) |
| Premium | `cell_viewer_premium.html` | Bloom, shaders, particulas |

**Componentes visiveis:**
- Membrana plasmatica (ondulada)
- Parede celular (vegetal)
- Nucleo com nucleolo
- Mitocondrias (6x)
- Cloroplastos (4x)
- Reticulo endoplasmatico
- Particulas flutuantes
- Patogeno (simulacoes)

### 3. Simulador de Consequencias (EM DESENVOLVIMENTO)

| Feature | Arquivo | Status |
|---------|---------|--------|
| Simulador | `cell_simulator.html` | Em desenvolvimento |

**Fluxo:**
```
Selecionar Gene → Ajustar Regulacao → Ver Consequencias
     ↓                  ↓                    ↓
   FLS2, BAK1      Ativacao/             Membrana muda
   MPK3, WRKY      Repressao             ROS burst
                                         Defesa ativa
```

---

## Dados Disponiveis

### Genes de Defesa (defense_network.json)

| Categoria | Genes | Funcao |
|-----------|-------|--------|
| PRR | FLS2, EFR, BAK1, CERK1 | Receptores de membrana |
| MAPK | MPK3, MPK6, MPK4, MEKK1 | Cascata de sinalizacao |
| TF | WRKY33, WRKY29, MYC2, TGA3 | Fatores de transcricao |
| NLR | NRC2, NRC3, NRC4, RPM1 | Imunidade intracelular |
| Defense | PR1, PR2, PDF1.2, PAD4 | Genes de defesa |
| Hormones | NPR1, EDS1, JAZ1, COI1 | Sinalizacao hormonal |
| ROS | RBOHD, SOD, CAT1, APX1 | Especies reativas de O2 |
| Effector | AvrPto, AvrRpm1, HopAI1 | Efetores de patogenos |

### Interacoes

| Tipo | Quantidade | Exemplo |
|------|------------|---------|
| Ativacao | ~25 | FLS2 → BAK1 |
| Repressao | ~6 | AvrPto -| FLS2 |

---

## Como Navegar

### Para Usuarios

1. **Primeira vez?** Abra `frontend/index.html`
2. **Quer ver redes?** `grn_explorer.html`
3. **Quer ver celula?** `cell_viewer_premium.html`
4. **Quer simular?** `cell_simulator.html`

### Para Desenvolvedores

1. **Entender biologia:** Leia `docs/BIOLOGIC.md`
2. **Ver dados:** `data/processed/defense_network.json`
3. **Historico:** `docs/APRENDIZAGEM.md`
4. **Fontes:** `docs/DATA_SOURCES.md`

---

## Tecnologias Usadas

| Componente | Tecnologia | Versao |
|------------|------------|--------|
| Redes 2D | Cytoscape.js | 3.23+ |
| Redes 3D | 3d-force-graph | latest |
| Celula 3D | Three.js | r160 |
| Metaballs | MarchingCubes | Three.js addon |
| Post-processing | EffectComposer | Three.js addon |
| Shaders | GLSL | custom |

---

## Roadmap

### Fase Atual: Visualizacao
- [x] GRN 2D
- [x] GRN 3D
- [x] Cell Viewer Primitivas
- [x] Cell Viewer Metaballs
- [x] Cell Viewer Premium
- [ ] Cell Simulator (consequencias)

### Proxima Fase: Simulacao
- [ ] Integracao GRN + Cell Viewer
- [ ] Propagacao de efeitos na rede
- [ ] Visualizacao de consequencias
- [ ] Animacoes de vias metabolicas

### Fase Futura: Backend
- [ ] FastAPI backend
- [ ] Banco de dados (PostgreSQL + Neo4j)
- [ ] BLAST/DIAMOND integration
- [ ] Autenticacao de usuarios

---

## Contato

**Desenvolvedor:** Mauricio Jampani de Souza
**Email:** mjampani@usp.br
**Projeto:** Bioinformatics Hub - Tools for Scientists

---

*Documento atualizado: 2026-03-02*
