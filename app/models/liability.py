from datetime import datetime
from app import db
from app.enums import LiabilityType


class Liability(db.Model):
    __tablename__ = "liabilities"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    liability_type = db.Column(db.Enum(LiabilityType), nullable=False)
    interest_rate = db.Column(db.Float, nullable=True)
    balance = db.Column(db.Float, default=0.0)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
