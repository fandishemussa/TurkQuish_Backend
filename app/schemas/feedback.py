from typing import Optional
from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    predictionId: str = Field(..., min_length=1)
    feedbackType: str = Field(..., min_length=1)
    comment: Optional[str] = Field(default=None, max_length=2000)
    clientTimestamp: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str = "received"
