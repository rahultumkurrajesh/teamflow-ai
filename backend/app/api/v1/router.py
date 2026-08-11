"""Aggregates every v1 endpoint module into one router."""
from fastapi import APIRouter

from app.api.v1.endpoints import health, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(users.router)
