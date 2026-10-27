"""FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    bookings,
    catalog,
    check_ins,
    clients,
    health,
    memberships,
    notifications,
    reports,
    sessions,
    settings,
    trainers,
)
from app.api.errors import register_error_handlers
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.scheduler import scheduler
from app.services.club_settings import ClubSettingsCache
from app.services.notifications.daily_check import run_daily_check

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def configured_check_time() -> time:
    with SessionLocal() as session:
        return ClubSettingsCache().get(session).daily_check_time


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if get_settings().scheduler_enabled:
        scheduler.start(configured_check_time(), run_daily_check, check_time=configured_check_time)
    yield
    scheduler.shutdown()


def create_app() -> FastAPI:
    app_settings = get_settings()
    app = FastAPI(
        title=app_settings.app_name,
        description="REST API системи управління фітнес-клубом",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    for router in (
        health.router,
        auth.router,
        clients.router,
        trainers.router,
        catalog.halls,
        catalog.tariffs,
        catalog.options,
        memberships.router,
        memberships.promo_codes,
        check_ins.router,
        sessions.router,
        bookings.router,
        notifications.router,
        settings.router,
        reports.router,
    ):
        app.include_router(router, prefix="/api")
    return app


app = create_app()
