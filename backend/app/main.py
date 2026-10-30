"""
Main FastAPI Application Entry Point for Udyog Sathi.
"""

import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import api_config
from app.routers.admin import router as admin_router
from app.routers.applications import router as applications_router
from app.routers.discovery import router as discovery_router
from app.routers.eligibility import router as eligibility_router
from app.routers.health import router as health_router
from app.routers.profiles import router as profiles_router
from app.routers.rag import router as rag_router
from app.routers.schemes import router as schemes_router
from app.routers.updates import router as updates_router
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
ROOT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

INDEX_HTML = None
for candidate in [
    os.path.join(FRONTEND_DIR, "dist", "index.html"),
    os.path.join(FRONTEND_DIR, "index.html"),
    os.path.join(BASE_DIR, "web", "index.html"),
]:
    if os.path.isfile(candidate):
        INDEX_HTML = candidate
        break

STATIC_DIR = None
for candidate in [
    os.path.join(FRONTEND_DIR, "public", "static"),
    os.path.join(FRONTEND_DIR, "static"),
    os.path.join(FRONTEND_DIR, "dist", "static"),
    os.path.join(BASE_DIR, "web", "static"),
]:
    if os.path.isdir(candidate):
        STATIC_DIR = candidate
        break

if STATIC_DIR and os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

LOCALES_DIR = None
for candidate in [
    os.path.join(FRONTEND_DIR, "public", "locales"),
    os.path.join(FRONTEND_DIR, "locales"),
    os.path.join(FRONTEND_DIR, "dist", "locales"),
    os.path.join(BASE_DIR, "web", "locales"),
]:
    if os.path.isdir(candidate):
        LOCALES_DIR = candidate
        break

if LOCALES_DIR and os.path.isdir(LOCALES_DIR):
    app.mount("/locales", StaticFiles(directory=LOCALES_DIR), name="locales")


@app.get("/")
def root(request: Request):
    accept = request.headers.get("accept", "")
    if INDEX_HTML and os.path.isfile(INDEX_HTML):
        if "application/json" not in accept or "text/html" in accept:
            return FileResponse(INDEX_HTML)
    return {
        "platform": "Udyog Sathi",
        "jurisdiction": "Government of Odisha",
        "status": "online",
        "version": api_config.app_version,
        "api_docs": "/docs",
        "health_check": "/health/ready",
        "message": "Udyog Sathi Backend API is live. Visit /docs for interactive Swagger API testing.",
        "disclaimer": "Udyog Sathi is an advisory discovery platform backed by verified government records. Final scheme sanction is subject to departmental scrutiny.",
    }


@app.get("/app")
def serve_app():
    if INDEX_HTML and os.path.isfile(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    return JSONResponse(status_code=404, content={"detail": "Web application not found. Please access the frontend URL or explore APIs at /docs."})

