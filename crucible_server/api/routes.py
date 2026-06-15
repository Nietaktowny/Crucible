# src/crucible_server/api/routes.py

from fastapi import APIRouter

from crucible_server.api.runs import router as runs_router
from crucible_server.api.workflows import router as workflows_router
from crucible_server.api.data import router as data_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(workflows_router)
api_router.include_router(runs_router)
api_router.include_router(data_router)