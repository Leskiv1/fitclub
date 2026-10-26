"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, bookings, catalog, check_ins, clients, health, memberships, sessions, trainers
from app.api.errors import register_error_handlers
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="REST API системи управління фітнес-клубом",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
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
    ):
        app.include_router(router, prefix="/api")
    return app


app = create_app()
