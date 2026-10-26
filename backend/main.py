
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database.connection import init_db
from api.auth import router as auth_router
from api.prediction import router as prediction_router
from api.history import router as history_router
from api.profile import router as profile_router
from api.sensor import router as sensor_router
from translation_service import translate_report


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
    description=(
        "Intelligent Crop Disease Detection "
        "& Preventive Agricultural Advisory API"
    ),
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


# Mount static uploads directory
app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOADS_DIR)),
    name="uploads"
)


# Mount existing API routers
app.include_router(auth_router)
app.include_router(prediction_router)
app.include_router(history_router)
app.include_router(profile_router)
app.include_router(sensor_router)


# Root endpoint
@app.get("/")
def root():
    return {
        "title": "Agriculture Advisory System API",
        "status": "online",
        "version": "2.0.0",
        "docs": "/docs"
    }


# Health endpoint
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# Translation request format
class TranslationRequest(BaseModel):
    report: dict
    language: str


# Translate report into English or Tamil
@app.post("/translate-report")
def translate_report_endpoint(request: TranslationRequest):
    if request.language not in ["en", "ta"]:
        raise HTTPException(
            status_code=400,
            detail="Language must be 'en' or 'ta'"
        )

    try:
        translated = translate_report(
            request.report,
            request.language
        )
        return {"report": translated}

    except Exception as error:
        print("Report translation failed:", error)
        raise HTTPException(
            status_code=500,
            detail="Report translation failed"
        )
