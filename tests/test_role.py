"""Test roles and linking"""
from typing import AsyncGenerator, List, Tuple
import logging
import json

import pytest
import pytest_asyncio
from asyncpg.exceptions import UniqueViolationError
from libadvian.binpackers import b64_to_uuid, uuid_to_b64
from pydantic import ValidationError

from arkia11nmodels.models import Role, User
from arkia11nmodels.models.role import UserRole
from arkia11nmodels.schemas.role import RoleCreate, DBRole, ACLItem, ACL
from arkia11nmodels.clickhelpers import get_by_uuid
from .test_token import with_user  # pylint: disable=W0611 # false positive

LOGGER = logging.getLogger(__name__)

# pylint: disable=W0621


@pytest_asyncio.fixture(scope="function")
async def with_role(dockerdb: str) -> AsyncGenerator[User, None]:
    """Create a role for tests"""
    _ = dockerdb  # consume the fixture to keep linter happy
    role = Role(displayname="Testing role")
    await role.create()
    yield role
    await UserRole.delete.where(UserRole.role == role.pk).gino.status()  # Nuke leftovers
    await role.delete()


@pytest.mark.asyncio
async def test_role_fixture(with_role: Role) -> None:
    """Just test the fixture"""
    assert with_role.displayname == "Testing role"


@pytest.mark.asyncio
async def test_role_pydantic_validators() -> None:
    """Test the pydantic schemas"""
    assert ACLItem.schema()
    assert ACL.schema()
    assert DBRole.schema()
    validaclitem = ACLItem.parse_obj(
        {
            "privilege": "fi.arki.superadmin",
            "action": True,
        }
    )
    assert validaclitem
    with pytest.raises(ValidationError):
        invalidaclitem = ACLItem.parse_obj(
            {"privilege": "fi.arki.superadmin", "action": True, "extrafield": "this should not be"}
        )
        assert not invalidaclitem

    validacl_sequence = ACL(
        [
            {
                "privilege": "fi.arki.superadmin",
                "action": True,
            }
        ]
    )
    assert validacl_sequence
    LOGGER.debug("validacl_sequence={}".format(repr(validacl_sequence)))
    acl_exported = validacl_sequence.dict()
    assert isinstance(acl_exported, list)
    LOGGER.debug("validacl_sequence.dict()={}".format(repr(acl_exported)))

    pdcrole = RoleCreate(
        displayname="Suur-Mestarit",
        acl=[
            {
                "privilege": "fi.arki.superadmin",
                "action": True,
            }
        ],
    )
    exported = pdcrole.dict()
    LOGGER.debug("exported={}".format(repr(exported)))
    assert pdcrole.displayname == exported["displayname"]
    ser = pdcrole.json()
    deser = json.loads(ser)
    assert deser["acl"][0]["privilege"] == "fi.arki.superadmin"

    with pytest.raises(ValidationError):
        invalidrole = RoleCreate(
            displayname="Suur-Mestarit",
            acl=[{"privilege": "fi.arki.superadmin", "action": True, "nosuchfield": "this should not be"}],
        )
        assert not invalidrole


@pytest.mark.asyncio
async def test_role_pydantic_db(dockerdb: str) -> None:
    """Test the pydantic schemas"""
    _ = dockerdb  # consume the fixture to keep linter happy
    # Test user creation via pydantic model
    pdcrole = RoleCreate(
        displayname="Suur-Mestarit",
        acl=[
            {
                "privilege": "fi.arki.superadmin",
                "action": True,
            }
        ],
    )
    LOGGER.debug("pdcrole.dict()={}".format(pdcrole.dict()))
    role = Role(**pdcrole.dict())
    await role.create()
    try:
        # Test pydantic instantiation from db, JSON serialisation
        pdrole = DBRole(**role.to_dict())
        pdrole_ser = pdrole.json()
        deser = json.loads(pdrole_ser)
        assert b64_to_uuid(deser["pk"]) == role.pk
        assert deser["displayname"] == pdcrole.displayname
        assert deser["acl"][0]["action"]
        assert pdcrole.displayname == role.displayname
    finally:
        # clean up
        await role.delete()


@pytest.mark.asyncio
async def test_role_crud() -> None:
    """Test that we can Create, Read, Update and Delete Roles"""
    # Create
    role = Role(displayname="Testing role")
    await role.create()
    assert isinstance(role.acl, list)
    assert not role.acl
    role_pk = str(role.pk)
    LOGGER.debug("role={}".format(role.to_dict()))

    new_acl = list(role.acl)
    new_acl.append({"target": "fi.pvarki.dummyservicle:read", "action": "grant"})
    await role.update(acl=new_acl).apply()

    fetched = await Role.get(role_pk)
    LOGGER.debug("fetched={}".format(fetched.to_dict()))
    assert fetched.created != fetched.updated
    assert fetched.acl[0]["target"] == "fi.pvarki.dummyservicle:read"

    # Test click-helper
    assert await get_by_uuid(Role, uuid_to_b64(fetched.pk))
    assert await get_by_uuid(Role, str(role.pk))
    # Check that non-existent uuids raise error
    with pytest.raises(ValueError):
        assert not await get_by_uuid(Role, "917813ec-9243-45df-a46e-0a8dacc5c0e0")

    # Delete
    await role.delete()
    fetched = await Role.get(role_pk)
    assert fetched is None


@pytest.mark.asyncio
async def test_role_assign_remove(with_user: User, with_role: Role) -> None:
    """Check that the helpers work"""
    user2 = User(email="assign2@example.com")
    await user2.create()
    user2 = await User.get(user2.pk)

    assert await with_role.assign_to(with_user)
    assert await with_role.assign_to(user2)
    assert not await with_role.assign_to(with_user)
    assert await with_role.remove_from(with_user)
    assert await with_role.remove_from(user2)
    assert await with_role.assign_to(with_user)
    assert await with_role.remove_from(with_user)
    assert not await with_role.remove_from(with_user)


@pytest.mark.asyncio
async def test_userrole_unique(with_user: User, with_role: Role) -> None:
    """Make sure the uniqueness is enforces"""
    link1 = UserRole(role=with_role.pk, user=with_user.pk)
    await link1.create()

    with pytest.raises(UniqueViolationError):
        link2 = UserRole(role=with_role.pk, user=with_user.pk)
        await link2.create()

    await link1.delete()


RoleTestDbType = Tuple[User, User, Role, Role, Role]


@pytest_asyncio.fixture
async def role_test_db(dockerdb: str) -> AsyncGenerator[RoleTestDbType, None]:
    """Setup DB for user role helpers"""
    _ = dockerdb  # consume the fixture to keep linter happy
    # Create all new users and roles for this mess
    user1 = User(email="persona@example.com")
    await user1.create()
    user1 = await User.get(user1.pk)
    user2 = User(email="nongratta@example.com")
    await user2.create()
    user2 = await User.get(user2.pk)

    role_1000 = Role(displayname="Priority 1000", priority=1000)
    await role_1000.create()
    role_1000 = await Role.get(role_1000.pk)
    role_1 = Role(displayname="Priority 1", priority=1)
    await role_1.create()
    role_1 = await Role.get(role_1.pk)
    role_100 = Role(displayname="Priority 1", priority=100)
    await role_100.create()
    role_100 = await Role.get(role_100.pk)

    assert await role_100.assign_to(user1)
    assert await role_1.assign_to(user1)
    assert await role_1000.assign_to(user1)
    lnks1 = await UserRole.query.where(UserRole.user == user1.pk).gino.all()
    LOGGER.debug("lnks1={}".format(lnks1))
    assert lnks1

    assert await role_1.assign_to(user2)
    assert await role_1000.assign_to(user2)
    lnks2 = await UserRole.query.where(UserRole.user == user2.pk).gino.all()
    LOGGER.debug("lnks2={}".format(lnks2))
    assert lnks2

    yield user1, user2, role_1, role_100, role_1000

    # clean up
    await UserRole.delete.where(UserRole.role == role_1000.pk).gino.status()
    await role_1000.delete()
    await UserRole.delete.where(UserRole.role == role_100.pk).gino.status()
    await role_100.delete()
    await UserRole.delete.where(UserRole.role == role_1.pk).gino.status()
    await role_1.delete()


@pytest.mark.asyncio
async def test_user_roles(role_test_db: RoleTestDbType) -> None:
    """Test user roles resolving"""

    user1, user2, role_1, role_100, role_1000 = role_test_db

    user1_roles = await Role.list_user_roles(user1)
    user1_role_dicts = [role.to_dict() for role in user1_roles]
    LOGGER.debug("user1_role_dicts={}".format(user1_role_dicts))
    assert user1_roles[2].priority == 1
    assert user1_roles[1].priority == 100
    assert user1_roles[0].priority == 1000

    user2_roles = await Role.list_user_roles(user2)
    user2_role_dicts = [role.to_dict() for role in user2_roles]
    LOGGER.debug("user2_role_dicts={}".format(user2_role_dicts))
    assert user2_roles[0].priority == 1000
    assert user2_roles[1].priority == 1

    def user_in_lst(user: User, lst: List[User]) -> bool:
        for lstuser in lst:
            if lstuser.pk == user.pk:
                return True
        return False

    # Test listing of users by role
    users_1 = await role_1.list_role_users()
    assert user_in_lst(user2, users_1)
    assert user_in_lst(user1, users_1)
    users_1000 = await role_1000.list_role_users()
    assert user_in_lst(user2, users_1000)
    assert user_in_lst(user1, users_1000)
    users_100 = await role_100.list_role_users()
    assert not user_in_lst(user2, users_100)
    assert user_in_lst(user1, users_100)
