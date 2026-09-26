from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.connection import get_db
from models.user import User
from models.analysis import Analysis
from schemas.auth import UserResponse
from schemas.profile import ProfileUpdate
from schemas.analysis import DashboardStats
from services.auth_service import get_current_user

router = APIRouter(tags=["Profile & Stats"])


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if profile_in.name is not None and profile_in.name.strip():
        current_user.name = profile_in.name.strip()
    if profile_in.phone is not None:
        current_user.phone = profile_in.phone.strip() if profile_in.phone.strip() else None
    if profile_in.location is not None:
        current_user.location = profile_in.location.strip() if profile_in.location.strip() else None

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analyses = db.query(Analysis).filter(Analysis.user_id == current_user.id).all()
    total = len(analyses)
    diseases = sum(1 for a in analyses if a.status.lower() != "healthy")
    healthy = total - diseases

    latest = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).order_by(desc(Analysis.created_at)).first()

    recent_at = latest.created_at if latest else None

    return DashboardStats(
        total_analyses=total,
        diseases_detected=diseases,
        healthy_results=healthy,
        recent_analysis_at=recent_at
    )
