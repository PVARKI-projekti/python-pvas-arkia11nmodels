"""Roles"""
from typing import AsyncGenerator, List
import logging

from sqlalchemy.dialects.postgresql import UUID as saUUID, JSONB
import sqlalchemy as sa
import pendulum

from .base import BaseModel, db
from .user import User
from ..schemas.role import DEFAULT_PRIORITY, ACL

LOGGER = logging.getLogger(__name__)


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
        user_role = (
            await UserRole.query.where(UserRole.role == self.pk).where(UserRole.user == user.pk).gino.one_or_none()
        )
        if user_role:
            if user_role.role != self.pk:
                raise ValueError(
                    f"Got UserRole with wrong role pk {user_role.role} vs {self.pk}, user_role={user_role.to_dict()}"
                )
            if user_role.user != user.pk:
                raise ValueError(
                    f"Got UserRole with wrong user pk {user_role.user} vs {user.pk}, user_role={user_role.to_dict()}"
                )
            if not user_role.deleted:
                LOGGER.info("Role {} already linked with user {}".format(self.displayname, user.displayname))
                return False
            LOGGER.info("Role {} link to user {} marked deleted, undeleting".format(self.displayname, user.displayname))
            await user_role.update(deleted=None).apply()
            return True
        LOGGER.info("Role {} link to user {} not found, creating new link".format(self.displayname, user.displayname))
        user_role = UserRole(role=self.pk, user=user.pk)
        await user_role.create()
        return True

    async def remove_from(self, user: User) -> bool:
        """Remove this role from user, returns True if deleted, False nothing was done"""
        user_role = (
            await UserRole.query.where(UserRole.role == self.pk).where(UserRole.user == user.pk).gino.one_or_none()
        )
        if user_role:
            if user_role.role != self.pk:
                raise ValueError(
                    f"Got UserRole with wrong role pk {user_role.role} vs {self.pk}, user_role={user_role.to_dict()}"
                )
            if user_role.user != user.pk:
                raise ValueError(
                    f"Got UserRole with wrong user pk {user_role.user} vs {user.pk}, user_role={user_role.to_dict()}"
                )
            if user_role.deleted:
                LOGGER.info("Role {} link with {} already gone".format(self.displayname, user.displayname))
                return False
        LOGGER.info("Role {} link to user {} found, marking deleted".format(self.displayname, user.displayname))
        await user_role.update(deleted=pendulum.now("UTC")).apply()
        return True

    async def iter_role_users(self) -> AsyncGenerator[User, None]:
        """Return iterator for users with this role"""
        async with db.acquire() as conn:  # Cursors need transaction
            async with conn.transaction():
                async for lnk in UserRole.load(user=User).query.where(UserRole.role == self.pk).where(
                    UserRole.deleted == None  # pylint: disable=C0121 ; # "is None" will create invalid query
                ).order_by(User.displayname).gino.iterate():
                    yield lnk.user

    async def list_role_users(self) -> List[User]:
        """Consumes the iterator from iter_role_users and returns a list. NOTE: This might get *very* expensive"""
        ret = []
        async for user in self.iter_role_users():
            ret.append(user)
        return ret

    @classmethod
    async def iter_user_roles(cls, user: User) -> AsyncGenerator["Role", None]:
        """Resolve roles user has (sorted in descending priority so they're easier to merge) and yields one by one"""
        async with db.acquire() as conn:  # Cursors need transaction
            async with conn.transaction():
                async for lnk in UserRole.load(role=Role).query.where(UserRole.user == user.pk).where(
                    UserRole.deleted == None  # pylint: disable=C0121 ; # "is None" will create invalid query
                ).order_by(Role.priority.desc()).gino.iterate():
                    yield lnk.role

    @classmethod
    async def list_user_roles(cls, user: User) -> List["Role"]:
        """Consumes the iterator from iter_user_roles and returns a list"""
        ret = []
        async for role in cls.iter_user_roles(user):
            ret.append(role)
        return ret

    @classmethod
    async def resolve_user_acl(cls, user: User) -> ACL:
        """Merge ACL from users' roles"""
        by_privilege = {item.privilege: item for item in User.default_acl}
        prev_priority = 10000
        async for role in cls.iter_user_roles(user):
            for item in ACL(role.acl):
                if item.privilege not in by_privilege:
                    by_privilege[item.privilege] = item
                    continue
                if role.priority < prev_priority:  # lower priority number is more important
                    by_privilege[item.privilege] = item
                    continue
                if item.action is False:
                    by_privilege[item.privilege] = item  # DENY actions are more important
                if not by_privilege[item.privilege] is False and item.privilege:
                    by_privilege[item.privilege] = item
            prev_priority = role.priority
        return ACL(list(by_privilege.values()))


class UserRole(BaseModel):  # pylint: disable=R0903
    """Link Users and Roles"""

    __tablename__ = "userroles"

    user = sa.Column(saUUID(), sa.ForeignKey(User.pk))
    role = sa.Column(saUUID(), sa.ForeignKey(Role.pk))
    _idx = sa.Index("user_role_unique", "user", "role", unique=True)
