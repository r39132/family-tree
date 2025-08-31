from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes_auth import router as auth_router
from .routes_events import router as events_router
from .routes_tree import router as tree_router

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://family-tree-web-klif7ymw3q-uc.a.run.app",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_origin_regex=None,
    allow_credentials=True,  # Can be True with specific origins
    allow_methods=["*"],
    allow_headers=["*"],
    # Optional but harmless: expose headers and cache preflight
    expose_headers=["*"],
    max_age=600,
)


# --- CORS debug instrumentation (safe to keep; logs only on OPTIONS) ---
@app.middleware("http")
async def _log_cors_preflight(request: Request, call_next):
    if request.method == "OPTIONS":
        origin = request.headers.get("origin")
        acr_method = request.headers.get("access-control-request-method")
        acr_headers = request.headers.get("access-control-request-headers")
        # Compact single-line for Cloud Run logs
        print(
            f"CORS preflight: origin={origin} acr_method={acr_method} acr_headers={acr_headers} path={request.url.path}"
        )
    return await call_next(request)


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


@app.options("/__cors-debug")
async def cors_debug_options(request: Request):
    # Echo back what the browser sent; CORSMiddleware will still apply headers
    return {
        "origin": request.headers.get("origin"),
        "acr_method": request.headers.get("access-control-request-method"),
        "acr_headers": request.headers.get("access-control-request-headers"),
    }
