from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.db.database import Base


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    url_hash = Column(String(128), nullable=False)
    masked_url = Column(Text, nullable=False)
    domain = Column(String(255), index=True, nullable=True)
    predicted_class = Column(String(64), index=True, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(32), nullable=False)
    recommended_action = Column(String(32), nullable=False)
    decision_source = Column(String(128), nullable=False)
    model_version = Column(String(128), nullable=True)
    feature_schema_version = Column(String(128), nullable=True)
    latency_ms = Column(Integer, nullable=False)
    app_version = Column(String(64), nullable=True)
    locale = Column(String(16), nullable=True)


class FeedbackLog(Base):
    __tablename__ = "feedback_logs"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(String(64), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    feedback_type = Column(String(64), nullable=False)
    comment = Column(Text, nullable=True)
    client_timestamp = Column(String(64), nullable=True)
