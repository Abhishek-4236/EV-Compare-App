from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import vehicles, compare, recommend, chat, subsidies, map, auth

from core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="EV Information & Comparison Agent — VBIT",
    version="1.0.0"
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

@app.on_event("startup")
def startup():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        # Allow API to start even if DB is temporarily unavailable.
        pass

@app.get("/health")
def health():
    return {
        "status": "OK",
        "project": "India EV Compare",
        "team": "VBIT "
    }
    
app.include_router(chat.router)
