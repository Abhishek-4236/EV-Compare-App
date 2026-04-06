from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import vehicles, compare, recommend
from routers import vehicles, compare, recommend, chat

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="India EV Compare API",
    description="EV Information & Comparison Agent — VBIT",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicles.router)
app.include_router(compare.router)
app.include_router(recommend.router)

@app.get("/health")
def health():
    return {
        "status": "OK",
        "project": "India EV Compare",
        "team": "VBIT 24P61A66"
    }
    
app.include_router(chat.router)