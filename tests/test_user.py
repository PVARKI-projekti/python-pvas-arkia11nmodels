"""Test the user model"""
import logging

import pytest
from asyncpg.exceptions import UniqueViolationError

from arkia11nmodels.models import User

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
async def test_user_crud(dockerdb: str) -> None:
    """Test that we can Create, Read, Update and Delete User"""
    _ = dockerdb  # consume the fixture to keep linter happy
    # Create
    user = User(email="foo@example.com")
    await user.create()
    LOGGER.debug("user={}".format(user.to_dict()))
    assert user.pk
    assert user.email == "foo@example.com"
    fetch_pk = str(user.pk)
    assert user.displayname == user.email
    # Update
    await user.update(email="bar@example.com").apply()
    # Create
    fetched = await User.get(fetch_pk)
    LOGGER.debug("fetched={}".format(fetched.to_dict()))
    assert fetched.email == "bar@example.com"
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
