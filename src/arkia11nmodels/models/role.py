"""Roles"""
from sqlalchemy.dialects.postgresql import UUID as saUUID, JSONB
import sqlalchemy as sa

from .base import BaseModel
from .user import User


class Role(BaseModel):
    """Role, ACLs (format TBDefined) stored as list of dicts in the JSON property"""

    __tablename__ = "roles"

    displayname = sa.Column(sa.Unicode(), nullable=False)
    acl = sa.Column(JSONB, nullable=False, server_default="[]")
    priority = sa.Column(sa.Integer, nullable=False, default=1000)  # merge priority, lower is more important

    async def assign_to(self, user: User) -> bool:
        """Assign this role to user, returns True if created, False if nothing was done (already assigned)"""
        role = await UserRole.query.where(UserRole.role == self.pk and UserRole.user == user.pk).gino.one_or_none()
        if role:
            return False
        # FIXME: check if role has deleted property set, if so, unset instead of attempting to create
        role = UserRole(role=self.pk, user=user.pk)
        await role.create()
        return True

    async def remove_from(self, user: User) -> bool:
        """Remove this role from user, returns True if deleted, False nothing was done"""
        role = await UserRole.query.where(UserRole.role == self.pk and UserRole.user == user.pk).gino.one_or_none()
        if role is None:
            return False
        # FIXME: mark as deleted by setting the deleted property instead
        await role.delete()
        return True


class UserRole(BaseModel):  # pylint: disable=R0903
    """Link Users and Roles"""

    __tablename__ = "userroles"

    user = sa.Column(saUUID(), sa.ForeignKey(User.pk))
    role = sa.Column(saUUID(), sa.ForeignKey(Role.pk))
    _idx = sa.Index("user_role_unique", "user", "role", unique=True)
