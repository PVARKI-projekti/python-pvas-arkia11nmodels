"""The one-time tokens"""
from typing import Optional, Dict, Any, Union
import datetime

from sqlalchemy.dialects.postgresql import UUID as saUUID, JSONB
import sqlalchemy as sa
import pendulum
from pendulum.duration import Duration

from .base import BaseModel
from .user import User

DEFAULT_EXPIRES = pendulum.duration(seconds=5 * 60)
TimeOrDuration = Union[datetime.datetime, Duration]


class Token(BaseModel):
    """Authentication token"""

    __tablename__ = "tokens"

    user = sa.Column(saUUID(), sa.ForeignKey(User.pk))
    sent_to = sa.Column(sa.String(), nullable=False)
    redirect = sa.Column(sa.String(), nullable=True)
    expires = sa.Column(sa.DateTime(timezone=True), nullable=False)
    used = sa.Column(sa.DateTime(timezone=True), nullable=True)
    audit_meta = sa.Column(JSONB, nullable=False, server_default="{}")

    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return pendulum.now("UTC") < self.expires and not self.used

    async def mark_used(self, audit_meta: Optional[Dict[str, Any]] = None) -> None:
        """Mark this token used"""
        audit_copy = dict(self.audit_meta)
        if audit_meta:
            raise NotImplementedError("We have not decided how to handle this")
        await self.update(used=pendulum.now("UTC"), audit_meta=audit_copy).apply()

    @classmethod
    def for_user(cls, user: User, expires: Optional[TimeOrDuration] = None) -> "Token":
        """Return one from user instance, just a shorthand"""
        if expires is None:
            expires = pendulum.now("UTC") + DEFAULT_EXPIRES
        elif isinstance(expires, Duration):
            expires = pendulum.now("UTC") + expires
        return Token(user=user.pk, expires=expires)
