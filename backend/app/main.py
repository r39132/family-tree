from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes_admin import router as admin_router
from .routes_auth import router as auth_router
from .routes_events import router as events_router
from .routes_spaces import ensure_default_spaces
from .routes_spaces import router as spaces_router
from .routes_tree import router as tree_router
from .routes_user import router as user_router

# Pre-initialize bcrypt to avoid initialization errors during request handling
# This works around a passlib/bcrypt issue where internal tests use >72 byte passwords
try:
    from .auth_utils import hash_password, verify_password

    # Trigger bcrypt initialization with both hash and verify operations
    # The verify operation triggers detect_wrap_bug() which uses >72 byte passwords
    test_hash = hash_password("initialization_test")
    _ = verify_password("initialization_test", test_hash)
except Exception:
    # If initialization fails, log but don't crash
    import logging

    logging.warning("Bcrypt initialization warning - may affect password operations")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Family Tree API with health monitoring",
)

# CORS: allow front-end origins and enable credentials.
# Keep explicit local dev origins; use a regex for Cloud Run web URLs.
ALLOWED_ORIGINS = [
    # Prod Cloud Run web URLs (explicit)
    "https://family-tree-web-153553106247.us-central1.run.app",
    "https://family-tree-web-klif7ymw3q-uc.a.run.app",
    # Local dev (Next.js)
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Local dev (Vite)
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    # Allow Cloud Run frontend URLs like: https://family-tree-web-<hash>-uc.a.run.app
    allow_origin_regex=r"^https://family-tree-web-[a-z0-9-]+-uc\.a\.run\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

app.include_router(auth_router)
app.include_router(tree_router)
app.include_router(events_router)
app.include_router(admin_router)
app.include_router(user_router)
app.include_router(spaces_router)

# Initialize default family spaces on startup
try:
    ensure_default_spaces()
except Exception as e:
    print(f"Warning: Failed to initialize default spaces: {e}")
    # Continue startup even if database initialization fails


@app.get("/status")
def status():
    """Health check endpoint - Google Cloud Run intercepts /healthz so we use /status"""
    return {"status": "ok"}


@app.get("/config")
def get_config():
    """Get public configuration settings"""
    return {
        "enable_map": settings.enable_map,
        "google_maps_api_key": settings.google_maps_api_key,
        "require_invite": settings.require_invite,
        "frontend_url": settings.frontend_url,
    }
