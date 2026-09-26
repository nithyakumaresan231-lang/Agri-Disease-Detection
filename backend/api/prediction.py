import os
import uuid
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import User
from models.analysis import Analysis
from schemas.analysis import AnalysisResponse, AdvisoryDetails
from services.auth_service import get_current_user
from services.prediction_service import get_prediction_service

router = APIRouter(tags=["Prediction"])

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB limit


@router.post("/predict", response_model=AnalysisResponse)
async def predict(
    file: UploadFile = File(...),
    temperature: Optional[float] = Form(None),
    humidity: Optional[float] = Form(None),
    soil_moisture: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Validate file extension
    file_ext = Path(file.filename or "sample.jpg").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format '{file_ext}'. Supported formats: JPG, JPEG, PNG, WEBP."
        )

    # 2. Read image bytes and validate size
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded image file: {str(e)}"
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image file is empty."
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image file size exceeds maximum limit of {MAX_FILE_SIZE // (1024 * 1024)}MB."
        )

    # 3. Save image to uploads directory
    unique_filename = f"{uuid.uuid4().hex}_{file.filename or 'leaf.jpg'}"
    # Sanitize filename
    safe_filename = "".join(c for c in unique_filename if c.isalnum() or c in "._-")
    file_path = UPLOADS_DIR / safe_filename

    with open(file_path, "wb") as f:
        f.write(contents)

    image_url = f"/uploads/{safe_filename}"

    # 4. Invoke Prediction Service (Mock or ML)
    prediction_service = get_prediction_service()
    pred_result = await prediction_service.predict(
        image_bytes=contents,
        filename=file.filename or "",
        temperature=temperature,
        humidity=humidity,
        soil_moisture=soil_moisture
    )

    # 5. Persist Analysis record in database linked to authenticated user
    analysis_record = Analysis(
        user_id=current_user.id,
        image_filename=file.filename or safe_filename,
        image_url=image_url,
        crop=pred_result["crop"],
        disease=pred_result["disease"],
        confidence=pred_result["confidence"],
        status=pred_result["status"],
        temperature=temperature,
        humidity=humidity,
        soil_moisture=soil_moisture,
        advisory_data=json.dumps(pred_result["advisory"])
    )

    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)

    advisory_obj = AdvisoryDetails(**pred_result["advisory"])

    return AnalysisResponse(
        id=analysis_record.id,
        user_id=analysis_record.user_id,
        image_filename=analysis_record.image_filename,
        image_url=analysis_record.image_url,
        crop=analysis_record.crop,
        disease=analysis_record.disease,
        confidence=analysis_record.confidence,
        status=analysis_record.status,
        temperature=analysis_record.temperature,
        humidity=analysis_record.humidity,
        soil_moisture=analysis_record.soil_moisture,
        advisory=advisory_obj,
        created_at=analysis_record.created_at
    )
