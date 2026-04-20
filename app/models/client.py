from datetime import datetime
from app import db
from app.enums import MaritalStatus, ProfileRole


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    case_name = db.Column(db.String(150), nullable=False)
    marital_status = db.Column(db.Enum(MaritalStatus), nullable=False, default=MaritalStatus.single)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profiles = db.relationship("ClientProfile", backref="client", lazy=True)
    accounts = db.relationship("Account", backref="client", lazy=True)
    liabilities = db.relationship("Liability", backref="client", lazy=True)
    financials = db.relationship("ClientFinancial", backref="client", uselist=False)
    reports = db.relationship("Report", backref="client", lazy=True)


class ClientProfile(db.Model):
    __tablename__ = "client_profiles"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    dob = db.Column(db.Date, nullable=True)
    ssn_last4 = db.Column(db.String(4), nullable=True)
    monthly_salary_after_tax = db.Column(db.Float, default=0.0)
    role = db.Column(db.Enum(ProfileRole), nullable=False, default=ProfileRole.primary)
    is_active = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)

    @property
    def age(self):
        if self.dob:
            today = datetime.utcnow().date()
            return today.year - self.dob.year - (
                (today.month, today.day) < (self.dob.month, self.dob.day)
            )
        return None
