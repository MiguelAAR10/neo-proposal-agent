from src.api.routers.admin import router as admin_router
from src.api.routers.agent import router as agent_router
from src.api.routers.ops import router as ops_router

__all__ = ["admin_router", "agent_router", "ops_router"]
