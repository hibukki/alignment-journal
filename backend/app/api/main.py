from fastapi import APIRouter

from app.api.routes import items, login, papers, private, reviewer_assignments, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(papers.router)
api_router.include_router(reviewer_assignments.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
