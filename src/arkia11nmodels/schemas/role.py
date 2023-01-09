"""Pydantic schemas for models.Role"""
from typing import Optional, Sequence
import logging

from pydantic import Field
from pydantic.main import BaseModel  # pylint: disable=E0611 # false positive
from pydantic_collections import BaseCollectionModel

from .base import CreateBase, DBBase
from ..models.role import DEFAULT_PRIORITY

# pylint: disable=R0903
LOGGER = logging.getLogger(__name__)


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
