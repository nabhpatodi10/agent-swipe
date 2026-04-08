from app.routers.admin import router as admin_router
from app.routers.agent_auth import router as agent_auth_router
from app.routers.agents import router as agents_router
from app.routers.collections import router as collections_router
from app.routers.follows import router as follows_router
from app.routers.google_oauth import router as google_oauth_router
from app.routers.profiles import router as profiles_router
from app.routers.reports import router as reports_router
from app.routers.social import router as social_router
from app.routers.swipe import router as swipe_router


__all__ = [
    "admin_router",
    "agent_auth_router",
    "agents_router",
    "collections_router",
    "follows_router",
    "google_oauth_router",
    "profiles_router",
    "reports_router",
    "social_router",
    "swipe_router",
]


