"""pytest automagics"""
from typing import Generator
import logging
import asyncio

import pytest
from libadvian.logging import init_logging

from arkia11nmodels.testhelpers import monkeysession, db_is_responsive, dockerdb  # pylint: disable=W0611

init_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)


# pylint: disable=W0621


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """return event loop, made session scoped fixture to allow db connections to persists between tests"""
    loop = asyncio.get_event_loop()
    yield loop
