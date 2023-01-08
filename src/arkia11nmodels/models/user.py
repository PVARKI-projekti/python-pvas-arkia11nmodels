"""User model"""
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy as sa

from .base import BaseModel


class User(BaseModel):  # pylint: disable=R0903
    """Users"""

    __tablename__ = "users"

    email = sa.Column(sa.String(), nullable=False, index=True, unique=True)
    sms = sa.Column(sa.String(), nullable=True, index=True, unique=True)
    displayname = sa.Column(sa.Unicode(), nullable=False, default=lambda ctx: ctx.current_parameters.get("email"))
    profile = sa.Column(JSONB, nullable=False, server_default="{}")
