from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import classify, customers, health, tasks

settings = get_settings()

app = FastAPI(
    title="ABC-Salon API",
    description="Phase 1: Jev-based message classification and a single booking-hours policy rule.",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(classify.router)
app.include_router(customers.router)
app.include_router(tasks.router)
app.include_router(health.router)
