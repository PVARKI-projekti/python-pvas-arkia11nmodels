"""Helpers for tests"""
from typing import Generator, Any
import logging
import asyncio

import pytest
import sqlalchemy


from arkia11nmodels.dbdevhelpers import create_all

LOGGER = logging.getLogger(__name__)


# pylint: disable=W0621

# FIXME: should be moved to libadvian.testhelpers
@pytest.fixture(scope="session")
def monkeysession() -> Any:  # while we wait for the type come out of _pytest
    """session scoped monkeypatcher"""
    with pytest.MonkeyPatch.context() as mpatch:
        yield mpatch


def db_is_responsive(url: sqlalchemy.engine.url.URL) -> bool:
    """Check if we can connect to the db"""
    engine = sqlalchemy.create_engine(url)
    try:
        LOGGER.debug("Trying to connect to {}".format(url))
        engine.connect()

        async def create_tables() -> None:
            """Init the schemas and tables"""
            from arkia11nmodels.models import db  # pylint: disable=C0415

            await db.set_bind(url)
            await create_all()

        asyncio.get_event_loop().run_until_complete(create_tables())

        inspector = sqlalchemy.inspect(engine)
        schemas = inspector.get_schema_names()
        if "a11n" not in schemas:
            LOGGER.warning("a11n schema not found")
            return False
        tables = inspector.get_table_names(schema="a11n")
        if "users" not in tables:
            LOGGER.warning("users table not found")
            return False

        return True
    except sqlalchemy.exc.OperationalError:
        # While waiting for db to come up we get this error a bunch
        return False


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """return event loop, made session scoped fixture to allow db connections to persists between tests"""
    loop = asyncio.get_event_loop()
    yield loop


@pytest.fixture(scope="session")
def dockerdb(docker_ip: str, docker_services: Any, monkeysession: Any) -> Generator[str, None, None]:
    """start docker container for db"""
    LOGGER.debug("Monkeypatching env")
    from arkia11nmodels import dbconfig  # pylint: disable=C0415

    mp_values = {
        "HOST": docker_ip,
        "PORT": docker_services.port_for("db", 5432),
        "PASSWORD": "modelstestpwd",  # pragma: allowlist secret
        "USER": "postgres",
        "DATABASE": "modelstest",
    }
    for key, value in mp_values.items():
        monkeysession.setenv(f"DB_{key}", str(value))
        monkeysession.setattr(dbconfig, key, value)

    new_dsn = sqlalchemy.engine.url.URL(
        drivername=dbconfig.DRIVER,
        username=dbconfig.USER,
        password=dbconfig.PASSWORD,
        host=dbconfig.HOST,
        port=dbconfig.PORT,
        database=dbconfig.DATABASE,
    )
    monkeysession.setattr(dbconfig, "DSN", new_dsn)

    LOGGER.debug("Waiting for db")
    docker_services.wait_until_responsive(timeout=30.0, pause=0.5, check=lambda: db_is_responsive(dbconfig.DSN))

    yield str(dbconfig.DSN)
