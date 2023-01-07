"""Test the token model"""
from typing import AsyncGenerator
import logging
import asyncio

import pytest
import pytest_asyncio
import pendulum

from arkia11nmodels.models import Token, User

LOGGER = logging.getLogger(__name__)


# pylint: disable=W0621


@pytest_asyncio.fixture(scope="module")
async def with_user(dockerdb: str) -> AsyncGenerator[User, None]:
    """Create a user for token tests"""
    _ = dockerdb  # consume the fixture to keep linter happy
    user = User(email="tokentest@example.com")
    await user.create()
    yield user
    await Token.delete.where(Token.user == user.pk).gino.status()  # Nuke leftovers
    await user.delete()


@pytest.mark.asyncio
async def test_user_fixture(with_user: User) -> None:
    """Just test the fixture"""
    assert with_user.email == "tokentest@example.com"


@pytest.mark.asyncio
async def test_token_crud(with_user: User) -> None:
    """Test that we can Create, Read, Update and Delete Tokens"""
    # Create
    token = Token.for_user(with_user)
    token.sent_to = with_user.email
    await token.create()
    token_pk = str(token.pk)
    LOGGER.debug("token={}".format(token.to_dict()))
    assert token.is_valid()

    # Update
    await asyncio.sleep(0.01)
    await token.mark_used()
    fetched = await Token.get(token_pk)
    assert not fetched.is_valid()
    assert fetched.updated != fetched.created

    # Delete
    await token.delete()
    fetched = await Token.get(token_pk)
    assert fetched is None


@pytest.mark.asyncio
async def test_token_expires_duration(with_user: User) -> None:
    """check that we can set expiry via duration"""
    token = Token.for_user(with_user, pendulum.duration(seconds=2.0))
    token.sent_to = with_user.email
    await token.create()
    LOGGER.debug("token={}".format(token.to_dict()))
    assert token.is_valid()
    assert pendulum.now().diff(token.expires).in_seconds() < 2.0  # type: ignore

    await asyncio.sleep(2.0)
    assert not token.is_valid()


@pytest.mark.asyncio
async def test_token_expires_datetime(with_user: User) -> None:
    """check that we can set expiry via duration"""
    expires = pendulum.now("UTC") + pendulum.duration(seconds=2.0)
    token = Token.for_user(with_user, expires)
    token.sent_to = with_user.email
    await token.create()
    LOGGER.debug("token={}".format(token.to_dict()))
    assert token.is_valid()
    assert pendulum.now().diff(token.expires).in_seconds() < 2.0  # type: ignore

    await asyncio.sleep(2.0)
    assert not token.is_valid()
