from fastapi import APIRouter
from app.schemas.prediction import HealthResponse, ModelInfoResponse
from app.services.artifact_loader import artifacts
from app.services.transformer_service import url_transformer_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        modelLoaded=artifacts.model is not None,
        modelVersion=artifacts.model_version,
        featureSchemaVersion=artifacts.feature_schema_version,
        urlOnly=True,
        urlTransformerAvailable=url_transformer_service.available,
    )


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info():
    return ModelInfoResponse(
        modelVersion=artifacts.model_version,
        featureSchemaVersion=artifacts.feature_schema_version,
        classes=artifacts.classes,
        nFeatures=artifacts.n_features,
        urlOnly=True,
        urlTransformerAvailable=url_transformer_service.available,
    )
