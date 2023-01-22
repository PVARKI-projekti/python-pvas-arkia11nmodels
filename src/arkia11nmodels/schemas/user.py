"""Pydantic schema for models.User"""
from typing import Optional, Any, Dict
import logging
import uuid

from pydantic import Field, validator
from pydantic.networks import EmailStr  # pylint: disable=E0611 # false positive
from pydantic_collections import BaseCollectionModel
from libadvian.binpackers import ensure_str, uuid_to_b64

from .base import CreateBase, DBBase

# pylint: disable=R0903
LOGGER = logging.getLogger(__name__)


class UserCreate(CreateBase):
    """Create User objects"""

    email: EmailStr = Field(description="User email address")
    sms: Optional[str] = Field(
        default=None, nullable=True, description="SMS (or similar messaging platform number) for user"
    )
    displayname: Optional[str] = Field(description="User display name, defaults to the email if not given")
    profile: Optional[Dict[str, Any]] = Field(default={}, description="Arbitrary dictionary of 'profile' type info")

    @validator("displayname", always=True)
    @classmethod
    def displayname_defaults_to_email(cls, val: str, values: Dict[str, Any]) -> str:
        """If dn is not set, set to email"""
        LOGGER.debug("Called, val={} values={}".format(repr(val), repr(values)))
        if not val:
            return str(values["email"])
        return str(val)


class DBUser(UserCreate, DBBase):
    """Display/update user objects"""


class UserList(BaseCollectionModel[DBUser]):
    """List of Users"""

    class Config:
        """Pydantic configs"""

        extra = "forbid"
        json_encoders = {uuid.UUID: lambda val: ensure_str(uuid_to_b64(val))}
