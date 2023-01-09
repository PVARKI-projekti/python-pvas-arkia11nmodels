"""Test the token model"""
from typing import AsyncGenerator
import logging
import asyncio
import json

import pytest
import pytest_asyncio
import pendulum
from pydantic import ValidationError
from libadvian.binpackers import b64_to_uuid, uuid_to_b64

from arkia11nmodels.models import Token, User
from arkia11nmodels.schemas.token import TokenRequest, DBToken
from arkia11nmodels.clickhelpers import get_by_uuid

LOGGER = logging.getLogger(__name__)


# pylint: disable=W0621


@pytest_asyncio.fixture(scope="module")
async def with_user(dockerdb: str) -> AsyncGenerator[User, None]:
    """Create a user for token tests"""
    _ = dockerdb  # consume the fixture to keep linter happy
    user = User(email="tokentest@example.com")
    await user.create()
    # refresh from db
    dbuser = await User.get(user.pk)
    yield dbuser
    await Token.delete.where(Token.user == dbuser.pk).gino.status()  # Nuke leftovers
    await dbuser.delete()


@pytest.mark.asyncio
async def test_user_fixture(with_user: User) -> None:
    """Just test the fixture"""
    assert with_user.email == "tokentest@example.com"


@pytest.mark.asyncio
async def test_token_pydantic_validators() -> None:
    """Test the pydantic schemas"""
    req = TokenRequest(target="tokentest@example.com")
    exported = req.dict()
    LOGGER.debug("exported={}".format(repr(exported)))
    assert req.deliver_via == "email"
    with pytest.raises(ValidationError):
        invalidreq = TokenRequest(target="tokentest@example.com", deliver_via="nosuchvalue")
        assert not invalidreq


@pytest.mark.asyncio
async def test_token_pydantic_db(with_user: User) -> None:
    """Test the pydantic schemas"""
    token = Token.for_user(with_user)
    token.sent_to = with_user.email
    await token.create()
    try:
        # Test pydantic instantiation from db, JSON serialisation
        pdtoken = DBToken(**token.to_dict())
        pdtoken_ser = pdtoken.json()
        deser = json.loads(pdtoken_ser)
        assert b64_to_uuid(deser["pk"]) == token.pk
        assert b64_to_uuid(deser["user"]) == with_user.pk
        assert deser["expires"] == token.expires.isoformat()
        assert not deser["used"]
        # Mark used
        await token.mark_used()
        # refresh
        token = await Token.get(token.pk)
        # Check again
        pdtoken = DBToken(**token.to_dict())
        pdtoken_ser = pdtoken.json()
        deser = json.loads(pdtoken_ser)
        assert token.used
        assert deser["used"] == token.used.isoformat()
        assert b64_to_uuid(deser["pk"]) == token.pk
        assert b64_to_uuid(deser["user"]) == with_user.pk
    finally:
        # clean up
        await token.delete()


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

    # Test click-helper
    assert await get_by_uuid(Token, uuid_to_b64(fetched.pk))
    assert await get_by_uuid(Token, str(token.pk))

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
