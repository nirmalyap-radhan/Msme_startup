"""
Main FastAPI Application Entry Point for Udyog Sathi.
"""

import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from apps.api.config import api_config
from apps.api.routers.admin import router as admin_router
from apps.api.routers.applications import router as applications_router
from apps.api.routers.discovery import router as discovery_router
from apps.api.routers.eligibility import router as eligibility_router
from apps.api.routers.health import router as health_router
from apps.api.routers.profiles import router as profiles_router
from apps.api.routers.rag import router as rag_router
from apps.api.routers.schemes import router as schemes_router
from apps.api.routers.updates import router as updates_router
from services.deadline_monitoring.scheduler import global_scheduler

app = FastAPI(
    title=api_config.app_name,
    version=api_config.app_version,
    description="Real-world AI-powered government scheme discovery and assistance platform for MSMEs in Odisha, India.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.on_event("startup")
def on_app_startup():
    global_scheduler.start()


@app.on_event("shutdown")
def on_app_shutdown():
    global_scheduler.stop()


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_config.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# Register Routers
app.include_router(health_router)
app.include_router(schemes_router, prefix=api_config.api_prefix)
app.include_router(eligibility_router, prefix=api_config.api_prefix)
app.include_router(profiles_router, prefix=api_config.api_prefix)
app.include_router(applications_router, prefix=api_config.api_prefix)
app.include_router(rag_router, prefix=api_config.api_prefix)
app.include_router(admin_router, prefix=api_config.api_prefix)
app.include_router(discovery_router, prefix=api_config.api_prefix)
app.include_router(updates_router, prefix=api_config.api_prefix)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
STATIC_DIR = os.path.join(WEB_DIR, "static")
INDEX_HTML = os.path.join(WEB_DIR, "index.html")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        if os.path.isfile(INDEX_HTML):
            return FileResponse(INDEX_HTML)
    return {
        "platform": "Udyog Sathi",
        "jurisdiction": "Government of Odisha",
        "description": "Unified MSME Services & Government Scheme Discovery Platform",
        "version": api_config.app_version,
        "api_docs": "/docs",
        "disclaimer": "Udyog Sathi is an advisory discovery platform backed by verified government records. Final scheme sanction is subject to departmental scrutiny.",
    }


@app.get("/app", response_class=FileResponse)
def serve_app():
    if os.path.isfile(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    return JSONResponse(status_code=404, content={"detail": "Web application not found."})

