"""Helpers to use with click"""
from typing import Any, List, Dict, Union, Type, cast
import logging
import uuid
import json
import datetime

import click
from libadvian.binpackers import b64_to_uuid, ensure_utf8, ensure_str, uuid_to_b64

from . import dbconfig, models
from .models.base import BaseModel


LOGGER = logging.getLogger(__name__)

# FIXME: move to libadvian.hashinghelpers
class DateTimeEncoder(json.JSONEncoder):
    """Handle datetimes in JSON"""

    def default(self, o: Any) -> Any:
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat().replace("+00:00", "Z")
        return super().default(o)


class UUIDEncoder(json.JSONEncoder):
    """Handle UUIDs in JSON (encode as base64)"""

    def default(self, o: Any) -> Any:
        if isinstance(o, uuid.UUID):
            return ensure_str(uuid_to_b64(o))
        return super().default(o)


class DBTypesEncoder(DateTimeEncoder, UUIDEncoder):
    """All the encoders we need"""


async def bind_db() -> None:
    """Bind the db"""
    await models.db.set_bind(dbconfig.DSN)


async def get_by_uuid(klass: Type[BaseModel], pkin: Union[bytes, str]) -> BaseModel:
    """Get a db object by its klass and UUID (base64 or hex str)"""
    try:
        getpk = b64_to_uuid(ensure_utf8(pkin))
    except ValueError:
        getpk = uuid.UUID(ensure_str(pkin))
    obj = await klass.get(getpk)
    if not obj:
        raise ValueError(f"{klass} with {ensure_str(pkin)} not found")
    return cast(BaseModel, obj)


async def get_and_print_json(klass: Type[BaseModel], pkin: Union[bytes, str]) -> None:
    """helper to get and dump as JSON object of type klass"""
    obj = await get_by_uuid(klass, pkin)
    click.echo(json.dumps(obj.to_dict(), cls=DBTypesEncoder))


async def create_and_print_json(klass: Type[BaseModel], init_kwargs: Dict[str, Any]) -> None:
    """helper to create and dump as JSON object of type klass with init args from init_kwargs"""
    obj = klass(**init_kwargs)
    await obj.create()
    click.echo(json.dumps(obj.to_dict(), cls=DBTypesEncoder))


async def list_and_print_json(klass: Type[BaseModel]) -> None:
    """helper to list and dump as JSON all objects of type klass"""
    dbobjs = await models.db.all(klass.query)
    ret: List[Dict[str, Any]] = []
    for dbobj in dbobjs:
        ret.append(dbobj.to_dict())
    click.echo(json.dumps(ret, cls=DBTypesEncoder))
