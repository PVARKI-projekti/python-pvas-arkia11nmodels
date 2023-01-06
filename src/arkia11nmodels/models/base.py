"""The Gino baseclass with db connection wrapping"""
# This fancy lazy-loader thing will mess up IDE introspection and mypy
# from gino.ext.starlette import Gino
# Se we load the correct module properly
from gino_starlette import Gino

from .. import dbconfig

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
