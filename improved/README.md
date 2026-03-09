# Bioinformatics Hub

> Tools for Scientists - Plataforma de visualizacao biologica e analise de redes genicas

## Status do Projeto

**Versao 0.5.0** - Visualizacao Celular 3D + Simulador

### Funcionalidades Implementadas

- [x] CRUD de Sequences + Upload FASTA
- [x] Gene Regulatory Networks com Neo4j
- [x] Inferencia de redes (Correlacao, MI)
- [x] **Visualizacao GRN 2D** (Cytoscape.js)
- [x] **Visualizacao GRN 3D** (Three.js)
- [x] **GRN Explorer** com filtros avancados
- [x] **Cell Viewer 3D** - 3 versoes (Primitivas, Metaballs, Premium)
- [x] **Hub Central** de navegacao
- [x] **Simulador de Consequencias** celulares (em desenvolvimento)
- [x] DNA Helix animado dentro do nucleo
- [x] Celula vegetal organica (N. benthamiana)

## Organismo Modelo

**Nicotiana benthamiana** - Planta modelo para fitopatologia
- 61k+ genes anotados
- 36 genes de defesa curados
- 3k+ efetores de patogenos (PHI-base)

## Quick Start

```bash
# 1. Subir ambiente
cd improved
docker-compose up -d

# 2. Servir frontend
cd frontend
python -m http.server 3000

# 3. Abrir no navegador
# http://localhost:3000/index.html
```

## Estrutura do Projeto

```
improved/
├── frontend/
│   ├── index.html              # HUB CENTRAL - comece aqui!
│   ├── grn_viewer.html         # Rede GRN 2D
│   ├── grn_viewer_3d.html      # Rede GRN 3D
│   ├── grn_explorer.html       # Explorer com filtros
│   ├── cell_viewer_3d.html     # Celula - Primitivas
│   ├── cell_viewer_metaballs.html  # Celula - Metaballs (Spore)
│   ├── cell_viewer_premium.html    # Celula - Efeitos avancados
│   └── cell_simulator.html     # Simulador de consequencias
├── data/
│   ├── processed/
│   │   ├── defense_network.json    # 36 genes, 31 interacoes
│   │   └── nbenthamiana_genes.json # 61k genes
│   └── DATA_SOURCES.md
├── docs/
│   ├── FEATURES.md             # Mapa de funcionalidades
│   ├── APRENDIZAGEM.md         # Diario tecnico
│   ├── BIOLOGIC.md             # Fundamentos biologicos
│   └── NBENTHAMIANA_DATABASE.md
├── backend/                    # FastAPI + PostgreSQL + Neo4j
└── docker-compose.yml
```

## Visualizacoes Disponiveis

| Feature | Arquivo | Tecnologia |
|---------|---------|------------|
| Rede 2D | grn_viewer.html | Cytoscape.js |
| Rede 3D | grn_viewer_3d.html | 3d-force-graph |
| Explorer | grn_explorer.html | Cytoscape + filtros |
| Celula Primitivas | cell_viewer_3d.html | Three.js r128 |
| Celula Metaballs | cell_viewer_metaballs.html | MarchingCubes |
| Celula Premium | cell_viewer_premium.html | Bloom + Shaders |
| Simulador | cell_simulator.html | Three.js + GRN |

## Tech Stack

| Camada | Tecnologia |
|--------|------------|
| Backend | Python 3.11 / FastAPI |
| Database | PostgreSQL + Neo4j |
| Visualizacao 2D | Cytoscape.js |
| Visualizacao 3D | Three.js r160 |
| Post-processing | EffectComposer (Bloom) |
| Metaballs | MarchingCubes addon |

## Documentacao

- [FEATURES.md](docs/FEATURES.md) - Mapa completo das funcionalidades
- [APRENDIZAGEM.md](docs/APRENDIZAGEM.md) - Diario tecnico de desenvolvimento
- [BIOLOGIC.md](docs/BIOLOGIC.md) - Fundamentos biologicos
- [DATA_SOURCES.md](data/DATA_SOURCES.md) - Fontes de dados

## Proximos Passos

1. Implementar logica de propagacao na GRN
2. Consequencias visuais especificas por gene
3. Animacoes de cascata de sinalizacao
4. Melhorar visual da celula vegetal

## Autor

**Mauricio Jampani de Souza**
mjampani@usp.br

## Licenca

MIT License
