from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.inference_service import InferenceService
from app.services.artifact_loader import artifacts
from app.services.transformer_service import url_transformer_service

router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest, db: Session = Depends(get_db)):
    service = InferenceService(artifacts, url_transformer_service)
    return service.predict(
        decoded_url=req.decodedUrl,
        locale=req.locale,
        app_version=req.appVersion,
        db=db,
    )
