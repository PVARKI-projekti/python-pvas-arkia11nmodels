"""User model"""
from typing import ClassVar
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy as sa

from .base import BaseModel
from ..schemas.role import ACL, ACLItem


class User(BaseModel):  # pylint: disable=R0903
    """Users"""

    __tablename__ = "users"

    email = sa.Column(sa.String(), nullable=False, index=True, unique=True)
    sms = sa.Column(sa.String(), nullable=True, index=True, unique=True)
    displayname = sa.Column(sa.Unicode(), nullable=False, default=lambda ctx: ctx.current_parameters.get("email"))
    profile = sa.Column(JSONB, nullable=False, server_default="{}")

    default_acl: ClassVar[ACL] = ACL(
        [
            ACLItem(privilege="fi.arki.arkia11nmodels.user:read", target="self", action=True),
            ACLItem(privilege="fi.arki.arkia11nmodels.token:read", target="self", action=True),
            # Do we want to add users write privileges to their profile ?
            # ACLItem(privilege="fi.arki.arkia11nmodels.user.profile:update", target="self", action=True),
            # ACLItem(privilege="fi.arki.arkia11nmodels.user.displayname:update", target="self", action=True),
            # email and sms are critical fields used for token delivery so if someone manages to steal one token
            # they must not be allowed to change the delivery addresses for a full account takeover
        ]
    )
