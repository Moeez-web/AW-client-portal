from datetime import datetime
from app import db
from app.enums import AccountType, SubType, Owner


class Account(db.Model):
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    owner = db.Column(db.Enum(Owner), nullable=False, default=Owner.client1)
    account_type = db.Column(db.Enum(AccountType), nullable=False)
    sub_type = db.Column(db.Enum(SubType), nullable=False)
    account_number_last4 = db.Column(db.String(4), nullable=True)
    institution_name = db.Column(db.String(150), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
