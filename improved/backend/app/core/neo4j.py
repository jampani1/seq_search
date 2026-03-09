"""
Neo4j Database Connection
==========================

Conexão com banco de grafos Neo4j para Gene Regulatory Networks.

DECISÕES TÉCNICAS:
------------------
1. Driver assíncrono:
   - neo4j-driver suporta async nativo
   - Não bloqueia o event loop do FastAPI

2. Padrão de conexão:
   - Similar ao PostgreSQL (dependency injection)
   - Session por request

3. Cypher queries:
   - Linguagem de query do Neo4j
   - Otimizada para traversal de grafos
   - CREATE, MATCH, MERGE, DELETE

4. Estrutura do grafo GRN:
   - Nós: Gene, TranscriptionFactor
   - Arestas: REGULATES (com peso/score)
"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.config import settings


# ========================================
# DRIVER
# ========================================
# Driver gerencia pool de conexões

_driver: Optional[AsyncDriver] = None


async def get_neo4j_driver() -> AsyncDriver:
    """
    Retorna o driver Neo4j (cria se não existir).
    """
    global _driver

    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_lifetime=3600,  # 1 hora
            max_connection_pool_size=50,
            connection_acquisition_timeout=60,
        )

    return _driver


async def close_neo4j_driver() -> None:
    """
    Fecha o driver Neo4j.
    """
    global _driver

    if _driver is not None:
        await _driver.close()
        _driver = None


# ========================================
# SESSION - Dependency Injection
# ========================================

async def get_neo4j_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency que fornece uma session Neo4j.

    Uso em endpoints:
    ```python
    from fastapi import Depends
    from app.core.neo4j import get_neo4j_session

    @router.get("/grn/{id}")
    async def get_network(
        network_id: int,
        neo4j: AsyncSession = Depends(get_neo4j_session)
    ):
        result = await neo4j.run("MATCH (n) RETURN n LIMIT 10")
        ...
    ```
    """
    driver = await get_neo4j_driver()
    async with driver.session(database="neo4j") as session:
        yield session


# ========================================
# HEALTH CHECK
# ========================================

async def check_neo4j_health() -> dict:
    """
    Verifica se o Neo4j está acessível.
    """
    try:
        driver = await get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run("RETURN 1 as health")
            record = await result.single()

            if record and record["health"] == 1:
                return {
                    "status": "healthy",
                    "uri": settings.NEO4J_URI,
                }
    except ServiceUnavailable:
        return {
            "status": "unavailable",
            "error": "Neo4j service unavailable",
        }
    except AuthError:
        return {
            "status": "auth_error",
            "error": "Invalid credentials",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }

    return {"status": "unknown"}


# ========================================
# SCHEMA INITIALIZATION
# ========================================

async def init_neo4j_schema() -> None:
    """
    Inicializa schema/constraints no Neo4j.

    Constraints garantem unicidade e melhoram performance.
    """
    driver = await get_neo4j_driver()

    async with driver.session() as session:
        # Constraint de unicidade para genes
        await session.run("""
            CREATE CONSTRAINT gene_id_unique IF NOT EXISTS
            FOR (g:Gene) REQUIRE g.gene_id IS UNIQUE
        """)

        # Constraint para redes
        await session.run("""
            CREATE CONSTRAINT network_id_unique IF NOT EXISTS
            FOR (n:Network) REQUIRE n.network_id IS UNIQUE
        """)

        # Índices para busca
        await session.run("""
            CREATE INDEX gene_name_index IF NOT EXISTS
            FOR (g:Gene) ON (g.name)
        """)

        await session.run("""
            CREATE INDEX gene_symbol_index IF NOT EXISTS
            FOR (g:Gene) ON (g.symbol)
        """)


# ========================================
# UTILITY FUNCTIONS
# ========================================

async def clear_network(network_id: str) -> int:
    """
    Remove todos os nós e arestas de uma rede.

    Returns:
        Número de nós deletados
    """
    driver = await get_neo4j_driver()

    async with driver.session() as session:
        result = await session.run("""
            MATCH (n)-[r]->()
            WHERE n.network_id = $network_id
            DELETE r
            WITH count(r) as deleted_edges
            MATCH (n)
            WHERE n.network_id = $network_id
            DELETE n
            RETURN count(n) as deleted_nodes
        """, network_id=network_id)

        record = await result.single()
        return record["deleted_nodes"] if record else 0


async def get_network_stats(network_id: str) -> dict:
    """
    Retorna estatísticas de uma rede.
    """
    driver = await get_neo4j_driver()

    async with driver.session() as session:
        result = await session.run("""
            MATCH (n {network_id: $network_id})
            WITH count(n) as nodes
            MATCH ()-[r {network_id: $network_id}]->()
            RETURN nodes, count(r) as edges
        """, network_id=network_id)

        record = await result.single()
        if record:
            return {
                "nodes": record["nodes"],
                "edges": record["edges"],
            }
        return {"nodes": 0, "edges": 0}
