from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import FeedbackLog
from app.schemas.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    db.add(FeedbackLog(
        prediction_id=req.predictionId,
        feedback_type=req.feedbackType,
        comment=req.comment,
        client_timestamp=req.clientTimestamp,
    ))
    db.commit()
    return FeedbackResponse(status="received")
