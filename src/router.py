from fastapi import APIRouter

from src.routers.campaigns import router as campaigns_router
from src.routers.crm import router as crm_router
from src.routers.health import router as health_router
from src.routers.websocket import ws_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/api")
api_router.include_router(campaigns_router, prefix="/api")
api_router.include_router(crm_router, prefix="/api")
api_router.include_router(ws_router, prefix="/ws")
