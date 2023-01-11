"""Pydantic schemas for models.Role"""
from typing import Optional, Sequence
import logging
import uuid

from pydantic import Field
from pydantic.main import BaseModel  # pylint: disable=E0611 # false positive
from pydantic_collections import BaseCollectionModel
from libadvian.binpackers import ensure_str, uuid_to_b64

from .base import CreateBase, DBBase


# pylint: disable=R0903
LOGGER = logging.getLogger(__name__)
DEFAULT_PRIORITY = 1000


class ACLItem(BaseModel, extra="forbid"):
    """ACL item"""

    privilege: str = Field(description="Name of the privilege, something like fi.arki.superadmin")
    action: Optional[bool] = Field(
        default=False, description="True for granting, False for denying, None for 'inherit'"
    )
    target: Optional[str] = Field(
        default=None, nullable=True, description="Target (if not null=global), start with FQDN"
    )


class ACL(BaseCollectionModel[ACLItem]):
    """Sequence of ACLItems"""


class RoleCreate(CreateBase):
    """Create Role objects"""

    displayname: str = Field(description="Name of the role")
    acl: Sequence[ACLItem] = Field(default_factory=list, description="List of ACL definitions, see ACLItem")
    priority: int = Field(default=DEFAULT_PRIORITY, description="Merge priority, lower is more important")


class DBRole(RoleCreate, DBBase):
    """Display/update Role objects"""


class RoleList(BaseCollectionModel[DBRole]):
    """List of Roles"""

    class Config:
        """Pydantic configs"""

        extra = "forbid"
        json_encoders = {uuid.UUID: lambda val: ensure_str(uuid_to_b64(val))}
