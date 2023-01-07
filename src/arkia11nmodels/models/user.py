"""User model"""
import uuid

from sqlalchemy.dialects.postgresql import UUID as saUUID, JSONB
import sqlalchemy as sa

from .base import db

# pylint: disable=R0903
class User(db.Model):
    """Users"""

    __tablename__ = "users"
    __table_args__ = {"schema": "a11n"}

    pk = sa.Column(saUUID(), primary_key=True, default=uuid.uuid4)
    email = sa.Column(sa.String(), nullable=False, index=True, unique=True)
    sms = sa.Column(sa.String(), nullable=True, index=True, unique=True)
    displayname = sa.Column(sa.Unicode(), nullable=False, default=lambda ctx: ctx.current_parameters.get("email"))
    profile = sa.Column(JSONB, nullable=False, server_default="{}")
