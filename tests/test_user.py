"""Test the user model"""
import json
import logging

import pytest
import pendulum
from asyncpg.exceptions import UniqueViolationError
from libadvian.binpackers import b64_to_uuid, uuid_to_b64
from pydantic import ValidationError

from arkia11nmodels.models import User
from arkia11nmodels.schemas.user import UserCreate, DBUser
from arkia11nmodels.clickhelpers import get_by_uuid

LOGGER = logging.getLogger(__name__)


# pylint: disable=W0621


def test_can_instantiate_user() -> None:
    """Make sure we can instantiate one and that defaults get filled properly"""
    user = User(email="foo@example.com")
    LOGGER.debug("user={}".format(user.to_dict()))
    assert user.email == "foo@example.com"
    # These default values only get set on insert/update since we're not using dataclasses
    # assert user.displayname == user.email
    # assert user.pk


@pytest.mark.asyncio
async def test_user_pydantic_validators() -> None:
    """Test the pydantic schemas"""
    pdcuser = UserCreate(email="foo@example.com")
    exported = pdcuser.dict()
    LOGGER.debug("exported={}".format(repr(exported)))
    assert pdcuser.email == pdcuser.displayname
    assert pdcuser.email == exported["email"]
    assert pdcuser.displayname == exported["displayname"]

    with pytest.raises(ValidationError):
        invaliduser = UserCreate(email="foo@example.com", nosuchfield="should not be")
        assert not invaliduser


@pytest.mark.asyncio
async def test_user_pydantic_db(dockerdb: str) -> None:
    """Test the pydantic schemas"""
    _ = dockerdb  # consume the fixture to keep linter happy
    # Test user creation via pydantic model
    pdcuser = UserCreate(email="foo@example.com")
    LOGGER.debug("pdcuser.dict()={}".format(pdcuser.dict()))
    user = User(**pdcuser.dict())
    await user.create()
    try:
        # Test pydantic instantiation from db, JSON serialisation
        pduser = DBUser(**user.to_dict())
        pduser_ser = pduser.json()
        deser = json.loads(pduser_ser)
        assert b64_to_uuid(deser["pk"]) == user.pk
        assert deser["displayname"] == pdcuser.displayname
        assert pdcuser.displayname == user.displayname
        assert pdcuser.displayname == user.email
    finally:
        # clean up
        await user.delete()


@pytest.mark.asyncio
async def test_user_crud(dockerdb: str) -> None:
    """Test that we can Create, Read, Update and Delete User"""
    _ = dockerdb  # consume the fixture to keep linter happy
    # Create
    user = User(email="foo@example.com")
    await user.create()
    LOGGER.debug("user={}".format(user.to_dict()))
    # make sure we can do aware comparisons
    assert pendulum.now().diff(user.created).in_seconds() < 0.2  # type: ignore
    assert user.pk
    assert user.email == "foo@example.com"
    fetch_pk = str(user.pk)
    assert user.displayname == user.email
    assert user.created == user.updated
    # Update
    await user.update(email="bar@example.com").apply()
    # Create
    fetched = await User.get(fetch_pk)
    LOGGER.debug("fetched={}".format(fetched.to_dict()))
    assert fetched.email == "bar@example.com"
    assert fetched.created != fetched.updated

    # Test click-helper
    assert await get_by_uuid(User, uuid_to_b64(fetched.pk))
    assert await get_by_uuid(User, str(user.pk))

    # Delete
    await fetched.delete()
    fetchfail = await User.get(fetch_pk)
    assert fetchfail is None


@pytest.mark.asyncio
async def test_user_profile(dockerdb: str) -> None:
    """Test the JSON profile"""
    _ = dockerdb  # consume the fixture to keep linter happy
    # Create
    user = User(email="zonk@example.com", profile={"key": "value", "nested": {"bool": True}})
    await user.create()
    LOGGER.debug("user={}".format(user.to_dict()))
    assert user.pk
    fetch_pk = str(user.pk)
    assert user.email == "zonk@example.com"
    # Mypy has false positives here with the magic getters
    assert user.profile["key"] == "value"  # type: ignore
    assert user.profile["nested"]["bool"] is True  # type: ignore

    # update by making a copy, updating the copy and using the .update()
    updated_profile = dict(user.profile)
    updated_profile.update({"anotherkey": "different value", "numbers": [1, 3, 3, 7]})
    await user.update(profile=updated_profile).apply()
    assert user.profile["anotherkey"] == "different value"  # type: ignore

    fetched = await User.get(fetch_pk)
    LOGGER.debug("fetched={}".format(fetched.to_dict()))
    # But there mypy is feeling fine ?
    assert fetched.profile["anotherkey"] == "different value"
    assert fetched.profile["numbers"][1] == 3

    await fetched.delete()


@pytest.mark.asyncio
async def test_user_email_unique(dockerdb: str) -> None:
    """Make sure email is unique"""
    _ = dockerdb  # consume the fixture to keep linter happy
    user1 = User(email="foo@example.com")
    await user1.create()

    with pytest.raises(UniqueViolationError):
        user2 = User(email="foo@example.com")
        await user2.create()

    await user1.delete()
