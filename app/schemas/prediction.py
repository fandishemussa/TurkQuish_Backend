from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    decodedUrl: str = Field(..., min_length=1, max_length=4096)
    clientTimestamp: Optional[str] = None
    locale: str = "en"
    appVersion: Optional[str] = None


class TopFeature(BaseModel):
    name: str
    displayName: str
    displayNameLocalized: Dict[str, str] = {}
    group: str
    value: float | int | str
    impact: float = 0.0
    direction: str = "unknown"


class ModelDecision(BaseModel):
    name: str
    used: bool = True
    confidence: Optional[float] = None
    margin: Optional[float] = None
    probabilities: Dict[str, float] = {}


class BrandSignals(BaseModel):
    impersonationDetected: bool = False
    officialDomainMatched: bool = False
    risk: str = "low"
    score: float = 0.0
    registeredDomainLabel: Optional[str] = None
    registeredDomain: Optional[str] = None
    suffix: Optional[str] = None
    detectedBrands: List[str] = []
    domainBrands: List[str] = []
    subdomainBrands: List[str] = []
    pathBrands: List[str] = []
    similarBrands: List[Dict[str, Any]] = []
    protectedEntityMatches: List[Dict[str, Any]] = []
    signals: List[str] = []
    explanation: Dict[str, str] = {}
    urlOnly: bool = True
    method: str = "turkish_protected_registry_plus_brand_rules_plus_levenshtein_edit_distance"
    protectedRegistrySize: int = 0
    brandCatalogSize: int = 0


class PredictionResponse(BaseModel):
    predictionId: str
    normalizedUrl: str
    maskedUrl: str
    domain: str
    predictedClass: str
    riskScore: float
    riskLevel: str
    recommendedAction: str
    threshold: float
    probabilities: Dict[str, float]
    explanation: Dict[str, str]
    topFeatures: List[TopFeature]
    modelVersion: str
    featureSchemaVersion: str
    latencyMs: int
    timingMs: Dict[str, float] = {}
    urlOnly: bool = True
    decisionSource: str
    primaryModel: ModelDecision
    fallbackModel: Optional[ModelDecision] = None
    uncertainty: Dict[str, float | bool | str] = {}
    brandSignals: Optional[BrandSignals] = None


class HealthResponse(BaseModel):
    status: str
    modelLoaded: bool
    modelVersion: str
    featureSchemaVersion: str
    urlOnly: bool = True
    urlTransformerAvailable: bool = False


class ModelInfoResponse(BaseModel):
    modelVersion: str
    featureSchemaVersion: str
    classes: List[str]
    urlOnly: bool = True
    nFeatures: int
    urlTransformerAvailable: bool = False


