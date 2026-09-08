from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

app_state: dict[str, Any] = {}


from src.dependencies.graph import close_checkpointer, get_graph, init_checkpointer


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_checkpointer()
    app_state["graph"] = await get_graph()
    yield
    await close_checkpointer()
    app_state.clear()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Campaign Orchestration Platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    return app


app = create_app()
