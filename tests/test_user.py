"""Test the user model"""
import logging

import pytest

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
