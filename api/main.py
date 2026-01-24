"""FastAPI entrypoint for ServiceNow Consultant."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import auth, chat, knowledge_base, settings, admin
from database import init_database


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="ServiceNow Consultant API", version="1.5.0")

    origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(knowledge_base.router, prefix="/api/kb", tags=["knowledge_base"])
    app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

    return app


app = create_app()


@app.on_event("startup")
def startup_event() -> None:
    """Initialize storage on startup."""
    init_database()
