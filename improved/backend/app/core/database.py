"""
Configuração do Banco de Dados - PostgreSQL Async
=================================================

DECISÕES TÉCNICAS:
------------------
1. SQLAlchemy 2.0 com modo async:
   - Performance superior para I/O bound operations
   - Não bloqueia enquanto espera resposta do DB
   - Essencial para APIs que fazem muitas queries

2. asyncpg como driver:
   - Driver PostgreSQL mais rápido para Python async
   - Mantido ativamente, bem documentado

3. Padrão de conexão:
   - Usamos 'dependency injection' do FastAPI
   - Cada request recebe uma session do pool
   - Session é fechada automaticamente após o request

4. Migrações com Alembic (será adicionado depois):
   - Versionamento de schema do banco
   - Permite rollback de mudanças
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# ========================================
# ENGINE - Conexão com o Banco
# ========================================
# O engine gerencia o pool de conexões com o PostgreSQL
#
# echo=True: mostra SQL no console (útil para debug, desligar em prod)
# pool_size: conexões mantidas abertas
# max_overflow: conexões extras permitidas em picos

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log de SQL apenas em debug
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verifica se conexão está viva antes de usar
)


# ========================================
# SESSION FACTORY
# ========================================
# Cria sessions (conexões) para cada request
#
# expire_on_commit=False: objetos continuam acessíveis após commit
# Importante para retornar dados ao cliente após salvar

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ========================================
# BASE CLASS PARA MODELS
# ========================================
# Todos os models herdam desta classe
# SQLAlchemy 2.0 usa DeclarativeBase ao invés de declarative_base()

class Base(DeclarativeBase):
    """
    Classe base para todos os modelos SQLAlchemy.

    Todos os models do projeto devem herdar desta classe:

    ```python
    from app.core.database import Base

    class Sequence(Base):
        __tablename__ = "sequences"
        ...
    ```
    """
    pass


# ========================================
# DEPENDENCY INJECTION
# ========================================
# Função que fornece uma session para cada request
# O FastAPI injeta automaticamente usando Depends()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency que fornece uma session do banco de dados.

    Uso em endpoints:
    ```python
    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.database import get_db

    @router.get("/sequences")
    async def list_sequences(db: AsyncSession = Depends(get_db)):
        # db está disponível aqui
        result = await db.execute(select(Sequence))
        return result.scalars().all()
    ```

    A session é automaticamente fechada após o request (yield).
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()  # Commit automático se não houver erro
        except Exception:
            await session.rollback()  # Rollback em caso de erro
            raise
        finally:
            await session.close()


# ========================================
# LIFECYCLE FUNCTIONS
# ========================================
# Chamadas no startup/shutdown da aplicação

async def init_db() -> None:
    """
    Inicializa o banco de dados.

    Em desenvolvimento: cria as tabelas automaticamente.
    Em produção: usar Alembic para migrações!
    """
    async with engine.begin() as conn:
        # Importar todos os models para que sejam registrados
        from app.models import sequence  # noqa: F401
        from app.models import blast_job  # noqa: F401
        from app.models import effector  # noqa: F401

        # Cria todas as tabelas (apenas se não existirem)
        # ATENÇÃO: Em produção, use Alembic para migrações!
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Fecha conexões com o banco de dados.

    Chamado no shutdown da aplicação para liberar recursos.
    """
    await engine.dispose()
