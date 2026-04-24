from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import vehicles, compare, recommend, chat, subsidies, map, auth, garage, admin
import logging

from core.config import settings
from services.ev_rag import ev_rag_service
from services.startup_sync import ensure_data_ready_on_startup, maybe_open_startup_url

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="EV Information & Comparison Agent — VBIT",
    version="1.0.0"
)

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "type": type(exc).__name__}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_URL,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicles.router)
app.include_router(compare.router)
app.include_router(recommend.router)
app.include_router(subsidies.router)
app.include_router(map.router)
app.include_router(auth.router)
app.include_router(garage.router)
app.include_router(admin.router)

@app.on_event("startup")
def startup():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        # Allow API to start even if DB is temporarily unavailable.
        pass
    try:
        sync_result = ensure_data_ready_on_startup()
        logger.info("Startup data sync: %s", sync_result)
    except Exception as exc:
        logger.warning("Startup data sync failed: %s", exc, exc_info=True)
        ev_rag_service.warmup()

    opened_url = maybe_open_startup_url()
    if opened_url:
        logger.info("Opened browser at %s", opened_url)

@app.get("/health")
def health():
    return {
        "status": "OK",
        "project": "India EV Compare",
        "team": "VBIT "
    }
    
app.include_router(chat.router)
