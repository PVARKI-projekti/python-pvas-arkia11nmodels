"""Schemas for models.Token"""
from typing import Optional, Any, Dict
import logging
import uuid
import datetime
from enum import Enum

from pydantic import Field

from .base import CreateBase, DBBase

# pylint: disable=R0903
LOGGER = logging.getLogger(__name__)


class ValidTokenDelivery(str, Enum):
    """Valid destinations to send token to"""

    EMAIL = "email"
    SMS = "sms"


class TokenRequest(CreateBase):
    """Request a login token"""

    target: str = Field(description="Which target to deliver token to, must match available user for the deliver_via")
    deliver_via: ValidTokenDelivery = Field(default="email", description="Which mechanism to use to deliver the token")
    redirect: Optional[str] = Field(
        default=None, nullable=True, description="Where to redirect user after they have been issued JWT"
    )
    expires: Optional[datetime.datetime] = Field(
        default=None, nullable=True, description="Set non-default expiry datetime"
    )


class DBToken(DBBase):
    """Display/update token objects"""

    user: uuid.UUID = Field(description="UUID of the user token was issued to")
    sent_to: str = Field(description="Where the token was sent")
    redirect: Optional[str] = Field(
        default=None, nullable=True, description="If set redirect user here after issuing JWT"
    )
    expires: datetime.datetime = Field(description="Until when the token is still usable")
    used: Optional[datetime.datetime] = Field(
        default=None, nullable=True, description="When was the token used (if set)"
    )
    audit_meta: Dict[str, Any] = Field(description="Audit related metadata log")
