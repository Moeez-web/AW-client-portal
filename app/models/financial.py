from app import db


class ClientFinancial(db.Model):
    __tablename__ = "client_financials"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, unique=True)
    monthly_expense_budget = db.Column(db.Float, default=0.0)
    private_reserve_target = db.Column(db.Float, default=0.0)
    insurance_deductibles = db.Column(db.Float, default=0.0)
