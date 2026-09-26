from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from database.connection import get_db
from models.user import User
from models.analysis import Analysis
from schemas.analysis import AnalysisResponse, AdvisoryDetails
from services.auth_service import get_current_user

router = APIRouter(prefix="/history", tags=["History"])


def _to_response(record: Analysis) -> AnalysisResponse:
    adv = record.get_advisory()
    return AnalysisResponse(
        id=record.id,
        user_id=record.user_id,
        image_filename=record.image_filename,
        image_url=record.image_url,
        crop=record.crop,
        disease=record.disease,
        confidence=record.confidence,
        status=record.status,
        temperature=record.temperature,
        humidity=record.humidity,
        soil_moisture=record.soil_moisture,
        advisory=AdvisoryDetails(**adv),
        created_at=record.created_at
    )


@router.get("", response_model=List[AnalysisResponse])
def get_history(
    search: Optional[str] = Query(None, description="Search by crop or disease name"),
    crop: Optional[str] = Query(None, description="Filter by crop name"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (Healthy / Disease Detected)"),
    sort: Optional[str] = Query("desc", pattern="^(asc|desc)$", description="Sort by date asc/desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Analysis).filter(Analysis.user_id == current_user.id)

    if crop and crop.lower() != "all":
        query = query.filter(Analysis.crop.ilike(f"%{crop}%"))

    if status_filter and status_filter.lower() != "all":
        query = query.filter(Analysis.status.ilike(f"%{status_filter}%"))

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Analysis.crop.ilike(s),
                Analysis.disease.ilike(s),
                Analysis.image_filename.ilike(s)
            )
        )

    if sort == "asc":
        query = query.order_by(asc(Analysis.created_at))
    else:
        query = query.order_by(desc(Analysis.created_at))

    records = query.all()
    return [_to_response(r) for r in records]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis_detail(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis record not found."
        )

    return _to_response(record)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis record not found."
        )

    db.delete(record)
    db.commit()
    return None
