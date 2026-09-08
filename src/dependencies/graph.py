from __future__ import annotations

import logging

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from src.core.config import settings
from src.pipelines.campaign_graph import compile_graph

logger = logging.getLogger(__name__)

_pool: AsyncConnectionPool | None = None
_checkpointer: AsyncPostgresSaver | None = None
_graph = None

async def init_checkpointer():
    global _pool, _checkpointer, _graph
    if _graph is None:
        logger.info("Initializing Postgres Checkpointer...")
        _pool = AsyncConnectionPool(
            conninfo=settings.POSTGRES_DSN,
            max_size=20,
            kwargs={"autocommit": True, "prepare_threshold": 0},
        )
        _checkpointer = AsyncPostgresSaver(_pool)
        await _checkpointer.setup()
        _graph = compile_graph(_checkpointer)
        logger.info("Graph compiled successfully with Postgres checkpointer.")

async def get_graph():
    global _graph
    if _graph is None:
        await init_checkpointer()
    return _graph

async def close_checkpointer():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
