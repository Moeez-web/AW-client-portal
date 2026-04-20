from datetime import datetime, timezone
from app import db


def _utcnow():
    return datetime.now(timezone.utc)


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    quarter = db.Column(db.Integer, nullable=False)  # 1-4
    year = db.Column(db.Integer, nullable=False)
    generated_at = db.Column(db.DateTime, default=_utcnow)
    pdf_sacs_path = db.Column(db.String(255), nullable=True)
    pdf_tcc_path = db.Column(db.String(255), nullable=True)

    entries = db.relationship("ReportEntry", backref="report", lazy=True)

    @property
    def quarter_label(self):
        return f"Q{self.quarter} {self.year}"


class ReportEntry(db.Model):
    __tablename__ = "report_entries"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("reports.id"), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=True)
    balance = db.Column(db.Float, default=0.0)
    label = db.Column(db.String(150), nullable=True)
    entered_at = db.Column(db.DateTime, default=_utcnow)
