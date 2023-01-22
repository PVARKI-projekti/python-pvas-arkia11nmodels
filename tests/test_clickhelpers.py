"""Just test they don't blow up"""
import logging

import pytest

from arkia11nmodels.models import User, Role
from arkia11nmodels.clickhelpers import list_and_print_json, get_and_print_json, create_and_print_json
from .test_token import with_user  # pylint: disable=W0611 # false positive
from .test_role import with_role  # pylint: disable=W0611 # false positive

LOGGER = logging.getLogger(__name__)

# pylint: disable=W0621


@pytest.mark.asyncio
async def test_get_and_print(with_user: User, with_role: Role) -> None:
    """Test with two objects"""
    # TODO: create a click context for output, capture it and check for primary keys
    await get_and_print_json(User, str(with_user.pk))
    await get_and_print_json(Role, str(with_role.pk))


@pytest.mark.asyncio
async def test_list_and_print(with_user: User, with_role: Role) -> None:
    """Test with two objects"""
    # Consume the fixtures, we need those in db
    _ = with_user
    _ = with_role
    # TODO: create a click context for output, capture it and check for primary keys
    await list_and_print_json(User)
    await list_and_print_json(Role)


@pytest.mark.asyncio
async def test_create_and_print(dockerdb: str) -> None:
    """Test with two objects"""
    _ = dockerdb
    # TODO: create a click context for output, capture it and check for the email and dn
    await create_and_print_json(User, {"email": "clicktest@example.com"})
    await create_and_print_json(Role, {"displayname": "Click test Role"})
