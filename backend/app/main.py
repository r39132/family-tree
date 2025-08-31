from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes_auth import router as auth_router
from .routes_events import router as events_router
from .routes_tree import router as tree_router

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily for debugging
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(tree_router)
app.include_router(events_router)


@app.get("/healthz")
def health():
    return {"status": "ok", "version": settings.app_version}


@app.options("/{path:path}")
def options_handler():
    """Explicit OPTIONS handler for all paths to ensure CORS preflight works"""
    return {}


@app.get("/config")
def get_config():
    """Get public configuration settings"""
    return {
        "enable_map": settings.enable_map,
        "google_maps_api_key": settings.google_maps_api_key,
        "require_invite": settings.require_invite,
    }
