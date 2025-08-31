from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes_auth import router as auth_router
from .routes_events import router as events_router
from .routes_tree import router as tree_router

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:3001",  # Alternative local port
        "https://family-tree-web-klif7ymw3q-uc.a.run.app",  # Deployed frontend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Referer",
        "User-Agent",
    ],
    expose_headers=["*"],
)

app.include_router(auth_router)
app.include_router(tree_router)
app.include_router(events_router)


@app.get("/healthz")
def health():
    return {"status": "ok", "version": settings.app_version}


@app.get("/config")
def get_config():
    """Get public configuration settings"""
    return {
        "enable_map": settings.enable_map,
        "google_maps_api_key": settings.google_maps_api_key,
        "require_invite": settings.require_invite,
    }
