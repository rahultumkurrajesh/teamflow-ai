"""Aggregates every v1 endpoint module into one router."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, comments, health, projects, tasks, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)
api_router.include_router(comments.router)
