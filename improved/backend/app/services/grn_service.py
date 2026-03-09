"""
Service: Gene Regulatory Network (GRN)
======================================

Lógica de negócio para Gene Regulatory Networks.

ARQUITETURA:
------------
1. PostgreSQL: metadados da rede (via SQLAlchemy)
2. Neo4j: grafo de regulação (via neo4j-driver)

MÉTODOS DE INFERÊNCIA:
----------------------
1. Correlação (Pearson/Spearman):
   - Simples e rápido
   - Captura co-expressão linear
   - Não diferencia regulador de alvo

2. Informação Mútua (ARACNE):
   - Captura relações não-lineares
   - Data Processing Inequality (DPI)
   - Remove arestas indiretas

3. GRNBoost2 (Gradient Boosting):
   - Estado da arte para GRN
   - Usa Random Forest para cada gene
   - Identifica reguladores (TFs) -> alvos

4. WGCNA:
   - Redes de co-expressão ponderadas
   - Identifica módulos de genes
   - Bom para análise exploratória

NOTA: Nesta fase, usamos implementações simplificadas/simuladas.
      Para produção, integrar com ferramentas reais (pySCENIC, WGCNA, etc.)
"""

import math
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.models.gene_network import GeneNetwork, NetworkStatus, InferenceMethod
from app.schemas.grn import (
    NetworkCreateRequest,
    NetworkResponse,
    NetworkSummary,
    GeneNode,
    RegulationEdge,
    CytoscapeGraphData,
    NetworkStatistics,
    ExpressionDataUpload,
    SubnetworkResponse,
    PathResponse,
)
from app.core.neo4j import get_neo4j_driver


class GRNService:
    """
    Serviço para Gene Regulatory Networks.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa o serviço.

        Args:
            db: Sessão do PostgreSQL
        """
        self.db = db

    # ========================================
    # CRUD - PostgreSQL
    # ========================================

    async def create_network(
        self,
        request: NetworkCreateRequest
    ) -> GeneNetwork:
        """
        Cria uma nova rede (metadados).

        Args:
            request: Dados para criar a rede

        Returns:
            GeneNetwork criada
        """
        network = GeneNetwork(
            network_id=uuid.uuid4(),
            name=request.name,
            description=request.description,
            organism=request.organism,
            method=request.method,
            threshold=request.threshold,
            parameters=request.parameters,
            expression_source=request.expression_source,
            status=NetworkStatus.PENDING,
        )

        self.db.add(network)
        await self.db.commit()
        await self.db.refresh(network)

        return network

    async def get_network(self, network_id: int) -> Optional[GeneNetwork]:
        """
        Busca rede por ID.
        """
        result = await self.db.execute(
            select(GeneNetwork).where(GeneNetwork.id == network_id)
        )
        return result.scalar_one_or_none()

    async def get_network_by_uuid(self, network_uuid: uuid.UUID) -> Optional[GeneNetwork]:
        """
        Busca rede por UUID.
        """
        result = await self.db.execute(
            select(GeneNetwork).where(GeneNetwork.network_id == network_uuid)
        )
        return result.scalar_one_or_none()

    async def list_networks(
        self,
        page: int = 1,
        page_size: int = 20,
        organism: Optional[str] = None,
        status: Optional[NetworkStatus] = None,
        method: Optional[InferenceMethod] = None,
    ) -> Tuple[List[GeneNetwork], int]:
        """
        Lista redes com paginação e filtros.

        Returns:
            Tuple de (lista de redes, total)
        """
        query = select(GeneNetwork)

        # Aplicar filtros
        if organism:
            query = query.where(GeneNetwork.organism.ilike(f"%{organism}%"))
        if status:
            query = query.where(GeneNetwork.status == status)
        if method:
            query = query.where(GeneNetwork.method == method)

        # Contar total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0

        # Aplicar paginação
        offset = (page - 1) * page_size
        query = query.order_by(GeneNetwork.created_at.desc())
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        networks = list(result.scalars().all())

        return networks, total

    async def delete_network(self, network_id: int) -> bool:
        """
        Deleta uma rede (PostgreSQL + Neo4j).
        """
        network = await self.get_network(network_id)
        if not network:
            return False

        # Deletar do Neo4j primeiro
        await self._clear_neo4j_network(str(network.network_id))

        # Deletar do PostgreSQL
        await self.db.delete(network)
        await self.db.commit()

        return True

    # ========================================
    # INFERÊNCIA DE REDE
    # ========================================

    async def infer_network(
        self,
        network_id: int,
        expression_data: ExpressionDataUpload,
    ) -> GeneNetwork:
        """
        Executa inferência de GRN a partir de dados de expressão.

        Args:
            network_id: ID da rede
            expression_data: Matriz de expressão

        Returns:
            Rede atualizada
        """
        network = await self.get_network(network_id)
        if not network:
            raise ValueError(f"Network {network_id} not found")

        # Atualizar status
        network.status = NetworkStatus.INFERRING
        await self.db.commit()

        try:
            # Escolher método de inferência
            if network.method == InferenceMethod.CORRELATION:
                edges = await self._infer_correlation(
                    expression_data.genes,
                    expression_data.expression_matrix,
                    network.threshold,
                    network.parameters,
                )
            elif network.method == InferenceMethod.MUTUAL_INFO:
                edges = await self._infer_mutual_info(
                    expression_data.genes,
                    expression_data.expression_matrix,
                    network.threshold,
                )
            elif network.method == InferenceMethod.GRNBOOST2:
                edges = await self._infer_grnboost2(
                    expression_data.genes,
                    expression_data.expression_matrix,
                    network.threshold,
                )
            else:  # WGCNA
                edges = await self._infer_wgcna(
                    expression_data.genes,
                    expression_data.expression_matrix,
                    network.threshold,
                )

            # Criar grafo no Neo4j
            node_count, edge_count = await self._create_neo4j_graph(
                str(network.network_id),
                expression_data.genes,
                edges,
            )

            # Atualizar metadados
            network.node_count = node_count
            network.edge_count = edge_count
            network.status = NetworkStatus.COMPLETED
            network.completed_at = datetime.utcnow()

        except Exception as e:
            network.status = NetworkStatus.FAILED
            network.error_message = str(e)

        await self.db.commit()
        await self.db.refresh(network)

        return network

    async def _infer_correlation(
        self,
        genes: List[str],
        expression_matrix: List[List[float]],
        threshold: float,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Inferência por correlação de Pearson/Spearman.

        Implementação simplificada para demonstração.
        """
        edges = []
        n_genes = len(genes)
        matrix = np.array(expression_matrix)

        method = "pearson"
        if parameters and "correlation_method" in parameters:
            method = parameters["correlation_method"]

        for i in range(n_genes):
            for j in range(i + 1, n_genes):
                # Calcular correlação
                if method == "pearson":
                    corr = self._pearson_correlation(matrix[i], matrix[j])
                else:
                    corr = self._spearman_correlation(matrix[i], matrix[j])

                # Verificar threshold
                if abs(corr) >= threshold:
                    edges.append({
                        "source": genes[i],
                        "target": genes[j],
                        "weight": corr,
                        "regulation_type": "activation" if corr > 0 else "repression",
                        "score": abs(corr),
                    })

        return edges

    async def _infer_mutual_info(
        self,
        genes: List[str],
        expression_matrix: List[List[float]],
        threshold: float,
    ) -> List[Dict[str, Any]]:
        """
        Inferência por informação mútua (ARACNE simplificado).
        """
        edges = []
        n_genes = len(genes)
        matrix = np.array(expression_matrix)

        # Calcular MI para todos os pares
        mi_matrix = np.zeros((n_genes, n_genes))
        for i in range(n_genes):
            for j in range(i + 1, n_genes):
                mi = self._mutual_information(matrix[i], matrix[j])
                mi_matrix[i, j] = mi
                mi_matrix[j, i] = mi

        # Aplicar DPI (Data Processing Inequality) simplificado
        for i in range(n_genes):
            for j in range(i + 1, n_genes):
                mi_ij = mi_matrix[i, j]
                if mi_ij < threshold:
                    continue

                # Verificar se é aresta direta (DPI)
                is_direct = True
                for k in range(n_genes):
                    if k == i or k == j:
                        continue
                    # Se MI(i,k) > MI(i,j) e MI(k,j) > MI(i,j), aresta é indireta
                    if mi_matrix[i, k] > mi_ij and mi_matrix[k, j] > mi_ij:
                        is_direct = False
                        break

                if is_direct:
                    edges.append({
                        "source": genes[i],
                        "target": genes[j],
                        "weight": mi_ij,
                        "regulation_type": "unknown",
                        "score": mi_ij,
                    })

        return edges

    async def _infer_grnboost2(
        self,
        genes: List[str],
        expression_matrix: List[List[float]],
        threshold: float,
    ) -> List[Dict[str, Any]]:
        """
        Inferência estilo GRNBoost2 (simulada).

        Na versão real, usar pySCENIC ou arboreto.
        Aqui simulamos usando correlação + ranking.
        """
        edges = []
        n_genes = len(genes)
        matrix = np.array(expression_matrix)

        # Simular: considerar primeiros 10% como TFs
        n_tfs = max(1, n_genes // 10)
        tfs = genes[:n_tfs]

        for tf in tfs:
            tf_idx = genes.index(tf)
            tf_expr = matrix[tf_idx]

            # Calcular "importância" para cada gene alvo
            for target_idx, target in enumerate(genes):
                if target == tf:
                    continue

                # Usar correlação como proxy de importância
                importance = abs(self._pearson_correlation(tf_expr, matrix[target_idx]))

                if importance >= threshold:
                    # Determinar tipo de regulação
                    corr = self._pearson_correlation(tf_expr, matrix[target_idx])
                    reg_type = "activation" if corr > 0 else "repression"

                    edges.append({
                        "source": tf,
                        "target": target,
                        "weight": importance,
                        "regulation_type": reg_type,
                        "score": importance,
                    })

        return edges

    async def _infer_wgcna(
        self,
        genes: List[str],
        expression_matrix: List[List[float]],
        threshold: float,
    ) -> List[Dict[str, Any]]:
        """
        Inferência estilo WGCNA (simplificada).
        """
        # Para WGCNA, usamos correlação com soft thresholding
        return await self._infer_correlation(
            genes,
            expression_matrix,
            threshold,
            {"correlation_method": "pearson"},
        )

    # ========================================
    # FUNÇÕES MATEMÁTICAS
    # ========================================

    def _pearson_correlation(self, x: np.ndarray, y: np.ndarray) -> float:
        """Calcula correlação de Pearson."""
        n = len(x)
        if n < 3:
            return 0.0

        mean_x = np.mean(x)
        mean_y = np.mean(y)

        numerator = np.sum((x - mean_x) * (y - mean_y))
        denominator = np.sqrt(
            np.sum((x - mean_x) ** 2) * np.sum((y - mean_y) ** 2)
        )

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _spearman_correlation(self, x: np.ndarray, y: np.ndarray) -> float:
        """Calcula correlação de Spearman (rank-based)."""
        rank_x = np.argsort(np.argsort(x)).astype(float)
        rank_y = np.argsort(np.argsort(y)).astype(float)
        return self._pearson_correlation(rank_x, rank_y)

    def _mutual_information(self, x: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
        """
        Calcula informação mútua entre duas variáveis.

        Versão simplificada usando histograma 2D.
        """
        # Discretizar em bins
        hist_2d, _, _ = np.histogram2d(x, y, bins=bins)

        # Normalizar para obter probabilidade conjunta
        pxy = hist_2d / float(np.sum(hist_2d))

        # Probabilidades marginais
        px = np.sum(pxy, axis=1)
        py = np.sum(pxy, axis=0)

        # Calcular MI
        mi = 0.0
        for i in range(bins):
            for j in range(bins):
                if pxy[i, j] > 0 and px[i] > 0 and py[j] > 0:
                    mi += pxy[i, j] * math.log2(pxy[i, j] / (px[i] * py[j]))

        return max(0, mi)  # MI deve ser >= 0

    # ========================================
    # NEO4J - OPERAÇÕES DE GRAFO
    # ========================================

    async def _create_neo4j_graph(
        self,
        network_id: str,
        genes: List[str],
        edges: List[Dict[str, Any]],
    ) -> Tuple[int, int]:
        """
        Cria o grafo no Neo4j.

        Returns:
            Tuple de (node_count, edge_count)
        """
        driver = await get_neo4j_driver()

        async with driver.session() as session:
            # Criar nós (genes)
            for gene in genes:
                await session.run("""
                    MERGE (g:Gene {gene_id: $gene_id, network_id: $network_id})
                    SET g.name = $gene_id
                """, gene_id=gene, network_id=network_id)

            # Criar arestas (regulações)
            for edge in edges:
                await session.run("""
                    MATCH (source:Gene {gene_id: $source, network_id: $network_id})
                    MATCH (target:Gene {gene_id: $target, network_id: $network_id})
                    MERGE (source)-[r:REGULATES {network_id: $network_id}]->(target)
                    SET r.weight = $weight,
                        r.regulation_type = $regulation_type,
                        r.score = $score
                """,
                    source=edge["source"],
                    target=edge["target"],
                    network_id=network_id,
                    weight=edge["weight"],
                    regulation_type=edge.get("regulation_type", "unknown"),
                    score=edge.get("score", edge["weight"]),
                )

        return len(genes), len(edges)

    async def _clear_neo4j_network(self, network_id: str) -> int:
        """
        Remove todos os nós e arestas de uma rede no Neo4j.
        """
        driver = await get_neo4j_driver()

        async with driver.session() as session:
            # Deletar arestas
            await session.run("""
                MATCH ()-[r:REGULATES {network_id: $network_id}]->()
                DELETE r
            """, network_id=network_id)

            # Deletar nós
            result = await session.run("""
                MATCH (g:Gene {network_id: $network_id})
                WITH g, count(g) as cnt
                DELETE g
                RETURN cnt
            """, network_id=network_id)

            record = await result.single()
            return record["cnt"] if record else 0

    # ========================================
    # QUERIES - NEO4J
    # ========================================

    async def get_graph_data(
        self,
        network_id: int,
        limit: Optional[int] = None,
    ) -> CytoscapeGraphData:
        """
        Retorna o grafo no formato Cytoscape.js.
        """
        network = await self.get_network(network_id)
        if not network:
            raise ValueError(f"Network {network_id} not found")

        driver = await get_neo4j_driver()
        nodes = []
        edges = []

        async with driver.session() as session:
            # Buscar nós
            node_query = """
                MATCH (g:Gene {network_id: $network_id})
                RETURN g.gene_id as id, g.name as label
            """
            if limit:
                node_query += f" LIMIT {limit}"

            result = await session.run(node_query, network_id=str(network.network_id))
            async for record in result:
                nodes.append({
                    "data": {
                        "id": record["id"],
                        "label": record["label"] or record["id"],
                    }
                })

            # Buscar arestas
            edge_query = """
                MATCH (source:Gene {network_id: $network_id})-[r:REGULATES]->(target:Gene {network_id: $network_id})
                RETURN source.gene_id as source, target.gene_id as target,
                       r.weight as weight, r.regulation_type as regulation_type
            """
            if limit:
                edge_query += f" LIMIT {limit * 2}"

            result = await session.run(edge_query, network_id=str(network.network_id))
            edge_id = 0
            async for record in result:
                edges.append({
                    "data": {
                        "id": f"e{edge_id}",
                        "source": record["source"],
                        "target": record["target"],
                        "weight": record["weight"],
                        "regulation_type": record["regulation_type"],
                    }
                })
                edge_id += 1

        return CytoscapeGraphData(
            elements={"nodes": nodes, "edges": edges},
            network_id=network.network_id,
            name=network.name,
            node_count=len(nodes),
            edge_count=len(edges),
        )

    async def get_gene_neighbors(
        self,
        network_id: int,
        gene_id: str,
        depth: int = 1,
        direction: str = "both",
        min_weight: Optional[float] = None,
    ) -> SubnetworkResponse:
        """
        Busca vizinhos de um gene.
        """
        network = await self.get_network(network_id)
        if not network:
            raise ValueError(f"Network {network_id} not found")

        driver = await get_neo4j_driver()
        nodes = []
        edges = []

        async with driver.session() as session:
            # Construir query baseado na direção
            if direction == "outgoing":
                pattern = f"(center)-[r:REGULATES*1..{depth}]->(neighbor)"
            elif direction == "incoming":
                pattern = f"(center)<-[r:REGULATES*1..{depth}]-(neighbor)"
            else:
                pattern = f"(center)-[r:REGULATES*1..{depth}]-(neighbor)"

            query = f"""
                MATCH (center:Gene {{gene_id: $gene_id, network_id: $network_id}})
                MATCH {pattern}
                WHERE neighbor.network_id = $network_id
                RETURN DISTINCT neighbor.gene_id as id, neighbor.name as label
            """

            result = await session.run(
                query,
                gene_id=gene_id,
                network_id=str(network.network_id),
            )

            neighbor_ids = set()
            async for record in result:
                neighbor_ids.add(record["id"])
                nodes.append(GeneNode(
                    id=record["id"],
                    label=record["label"] or record["id"],
                ))

            # Adicionar nó central
            nodes.insert(0, GeneNode(id=gene_id, label=gene_id))
            neighbor_ids.add(gene_id)

            # Buscar arestas entre os nós encontrados
            edge_query = """
                MATCH (source:Gene {network_id: $network_id})-[r:REGULATES]->(target:Gene {network_id: $network_id})
                WHERE source.gene_id IN $node_ids AND target.gene_id IN $node_ids
                RETURN source.gene_id as source, target.gene_id as target,
                       r.weight as weight, r.regulation_type as regulation_type,
                       r.score as score
            """

            result = await session.run(
                edge_query,
                network_id=str(network.network_id),
                node_ids=list(neighbor_ids),
            )

            edge_id = 0
            async for record in result:
                weight = record["weight"]
                if min_weight and abs(weight) < min_weight:
                    continue

                edges.append(RegulationEdge(
                    id=f"e{edge_id}",
                    source=record["source"],
                    target=record["target"],
                    weight=weight,
                    regulation_type=record["regulation_type"] or "unknown",
                    score=record["score"],
                ))
                edge_id += 1

        return SubnetworkResponse(
            center_gene=gene_id,
            depth=depth,
            nodes=nodes,
            edges=edges,
        )

    async def find_path(
        self,
        network_id: int,
        source_gene: str,
        target_gene: str,
        max_hops: int = 5,
    ) -> PathResponse:
        """
        Encontra caminho mais curto entre dois genes.
        """
        network = await self.get_network(network_id)
        if not network:
            raise ValueError(f"Network {network_id} not found")

        driver = await get_neo4j_driver()

        async with driver.session() as session:
            query = f"""
                MATCH path = shortestPath(
                    (source:Gene {{gene_id: $source, network_id: $network_id}})-
                    [r:REGULATES*1..{max_hops}]-
                    (target:Gene {{gene_id: $target, network_id: $network_id}})
                )
                RETURN [node in nodes(path) | node.gene_id] as genes,
                       length(path) as path_length
            """

            result = await session.run(
                query,
                source=source_gene,
                target=target_gene,
                network_id=str(network.network_id),
            )

            record = await result.single()

            if record:
                return PathResponse(
                    source=source_gene,
                    target=target_gene,
                    path_found=True,
                    path_length=record["path_length"],
                    path=record["genes"],
                )
            else:
                return PathResponse(
                    source=source_gene,
                    target=target_gene,
                    path_found=False,
                )

    async def get_network_statistics(self, network_id: int) -> NetworkStatistics:
        """
        Calcula estatísticas detalhadas da rede.
        """
        network = await self.get_network(network_id)
        if not network:
            raise ValueError(f"Network {network_id} not found")

        driver = await get_neo4j_driver()

        async with driver.session() as session:
            # Estatísticas básicas
            stats_query = """
                MATCH (g:Gene {network_id: $network_id})
                WITH count(g) as node_count
                MATCH ()-[r:REGULATES {network_id: $network_id}]->()
                WITH node_count, count(r) as edge_count
                RETURN node_count, edge_count
            """
            result = await session.run(stats_query, network_id=str(network.network_id))
            record = await result.single()

            node_count = record["node_count"] if record else 0
            edge_count = record["edge_count"] if record else 0

            # Calcular densidade
            density = 0.0
            if node_count > 1:
                density = edge_count / (node_count * (node_count - 1))

            # Top reguladores (por out-degree)
            top_reg_query = """
                MATCH (g:Gene {network_id: $network_id})-[r:REGULATES]->()
                WITH g.gene_id as gene, count(r) as out_degree
                ORDER BY out_degree DESC
                LIMIT 10
                RETURN gene, out_degree
            """
            result = await session.run(top_reg_query, network_id=str(network.network_id))
            top_regulators = []
            max_out_degree = 0
            async for rec in result:
                top_regulators.append({"gene": rec["gene"], "out_degree": rec["out_degree"]})
                max_out_degree = max(max_out_degree, rec["out_degree"])

            # Top alvos (por in-degree)
            top_target_query = """
                MATCH (g:Gene {network_id: $network_id})<-[r:REGULATES]-()
                WITH g.gene_id as gene, count(r) as in_degree
                ORDER BY in_degree DESC
                LIMIT 10
                RETURN gene, in_degree
            """
            result = await session.run(top_target_query, network_id=str(network.network_id))
            top_targets = []
            max_in_degree = 0
            async for rec in result:
                top_targets.append({"gene": rec["gene"], "in_degree": rec["in_degree"]})
                max_in_degree = max(max_in_degree, rec["in_degree"])

            # Grau médio
            avg_degree = (2 * edge_count / node_count) if node_count > 0 else 0

            return NetworkStatistics(
                node_count=node_count,
                edge_count=edge_count,
                density=density,
                avg_degree=avg_degree,
                max_in_degree=max_in_degree,
                max_out_degree=max_out_degree,
                top_regulators=top_regulators,
                top_targets=top_targets,
            )
