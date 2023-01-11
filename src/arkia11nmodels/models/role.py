"""Roles"""
import logging

from sqlalchemy.dialects.postgresql import UUID as saUUID, JSONB
import sqlalchemy as sa
import pendulum

from .base import BaseModel
from .user import User

LOGGER = logging.getLogger(__name__)
DEFAULT_PRIORITY = 1000


class Role(BaseModel):
    """Role, ACLs (format TBDefined) stored as list of dicts in the JSON property"""

    __tablename__ = "roles"

    displayname = sa.Column(sa.Unicode(), nullable=False)
    acl = sa.Column(JSONB, nullable=False, server_default="[]")
    priority = sa.Column(
        sa.Integer, nullable=False, default=DEFAULT_PRIORITY
    )  # merge priority, lower is more important

    async def assign_to(self, user: User) -> bool:
        """Assign this role to user, returns True if created, False if nothing was done (already assigned)"""
        user_role = await UserRole.query.where(UserRole.role == self.pk and UserRole.user == user.pk).gino.one_or_none()
        if user_role:
            if not user_role.deleted:
                LOGGER.info("Role {} already linked with user {}".format(self.displayname, user.displayname))
                return False
            LOGGER.info("Role {} link to user {} marked deleted, undeleting".format(self.displayname, user.displayname))
            await user_role.update(deleted=None)
            return True
        LOGGER.info("Role {} link to user {} not found, creating new link".format(self.displayname, user.displayname))
        user_role = UserRole(role=self.pk, user=user.pk)
        await user_role.create()
        return True

    async def remove_from(self, user: User) -> bool:
        """Remove this role from user, returns True if deleted, False nothing was done"""
        user_role = await UserRole.query.where(UserRole.role == self.pk and UserRole.user == user.pk).gino.one_or_none()
        if user_role is None or user_role.deleted:
            LOGGER.info("Role {} link with {} already gone".format(self.displayname, user.displayname))
            return False
        await user_role.update(deleted=pendulum.now("UTC")).apply()
        return True


class UserRole(BaseModel):  # pylint: disable=R0903
    """Link Users and Roles"""

    __tablename__ = "userroles"

    user = sa.Column(saUUID(), sa.ForeignKey(User.pk))
    role = sa.Column(saUUID(), sa.ForeignKey(Role.pk))
    _idx = sa.Index("user_role_unique", "user", "role", unique=True)
