"""Pydantic schema for models.User"""
from typing import Optional, Any, Dict
import logging

from pydantic import Field, validator
from pydantic.networks import EmailStr  # pylint: disable=E0611 # false positive

from .base import CreateBase, DBBase

LOGGER = logging.getLogger(__name__)

# pylint: disable=R0903
class UserCreate(CreateBase):
    """Create User objects"""

    email: EmailStr
    sms: Optional[str] = Field(default=None, nullable=True)
    displayname: Optional[str]
    profile: Optional[Dict[str, Any]] = Field(default={})

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
