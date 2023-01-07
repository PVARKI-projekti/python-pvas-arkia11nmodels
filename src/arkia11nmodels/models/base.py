"""The Gino baseclass with db connection wrapping"""
from typing import Any
import uuid

# This fancy lazy-loader thing will mess up IDE introspection and mypy
# from gino.ext.starlette import Gino
# Se we load the correct module properly
from gino_starlette import Gino
from sqlalchemy.dialects.postgresql import UUID as saUUID
import sqlalchemy as sa


from .. import dbconfig

utcnow = sa.func.current_timestamp()
db = Gino(
    dsn=dbconfig.DSN,
    pool_min_size=dbconfig.POOL_MIN_SIZE,
    pool_max_size=dbconfig.POOL_MAX_SIZE,
    echo=dbconfig.ECHO,
    ssl=dbconfig.SSL,
    use_connection_for_request=dbconfig.USE_CONNECTION_FOR_REQUEST,
    retry_limit=dbconfig.RETRY_LIMIT,
    retry_interval=dbconfig.RETRY_INTERVAL,
)
DBModel: Any = db.Model  # workaround mypy being unhappy about using @property as baseclass


class BaseModel(DBModel):  # pylint: disable=R0903
    """Baseclass with common fields"""

    __table_args__ = {"schema": "a11n"}

    pk = sa.Column(saUUID(), primary_key=True, default=uuid.uuid4)
    created = sa.Column(sa.DateTime(timezone=True), default=utcnow, nullable=False)
    updated = sa.Column(sa.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    deleted = sa.Column(sa.DateTime(timezone=True), nullable=True)
