"""schema baseclasses"""
from typing import Optional
import uuid
import datetime

from libadvian.binpackers import uuid_to_b64, ensure_str

from pydantic import BaseModel, Field  # pylint: disable=E0611  # false-positive

# pylint: disable=R0903


class SchemaBase(BaseModel):
    """Common encoders and validators"""

    class Config:
        """Pydantic configs"""

        json_encoders = {uuid.UUID: lambda val: ensure_str(uuid_to_b64(val))}


class CreateBase(SchemaBase):
    """Creation baseclass"""


class DBBase(SchemaBase):
    """Base for object that came from database"""

    pk: uuid.UUID
    created: datetime.datetime
    updated: datetime.datetime
    deleted: Optional[datetime.datetime] = Field(default=None, nullable=True)
