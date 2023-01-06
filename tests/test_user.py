"""Test the user model"""
import logging

from arkia11nmodels.models import User

LOGGER = logging.getLogger(__name__)


def test_can_instantiate_user() -> None:
    """Make sure we can instantiate one and that defaults get filled properly"""
    user = User(email="foo@example.com")
    LOGGER.debug("user={}".format(user.to_dict()))
    assert user.email == "foo@example.com"
    # These default values only get set on insert/update since we're not using dataclasses
    # assert user.displayname == user.email
    # assert user.pk
