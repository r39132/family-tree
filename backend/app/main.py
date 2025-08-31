from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes_auth import router as auth_router
from .routes_events import router as events_router
from .routes_tree import router as tree_router

app = FastAPI(title=settings.app_name, version=settings.app_version)

# CORS: allow specific front-end origins and enable credentials
ALLOWED_ORIGINS = [
    # Cloud Run web service URLs (include both styles if used)
    "https://family-tree-web-153553106247.us-central1.run.app",
    "https://family-tree-web-klif7ymw3q-uc.a.run.app",
    # Local dev (Next.js)
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
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
