from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database.connection import init_db
from api.auth import router as auth_router
from api.prediction import router as prediction_router
from api.history import router as history_router
from api.profile import router as profile_router

# Setup upload directory
UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    print("[Agriculture Advisory System] Database initialized.")
    yield


app = FastAPI(
    title="Agriculture Advisory System",
    description="Intelligent Crop Disease Detection & Preventive Agricultural Advisory API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for React frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static uploads directory so frontend can display submitted images
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Mount API routers
app.include_router(auth_router)
app.include_router(prediction_router)
app.include_router(history_router)
app.include_router(profile_router)


@app.get("/")
def root():
    return {
        "title": "Agriculture Advisory System API",
        "status": "online",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }