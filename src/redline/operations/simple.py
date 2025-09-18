"""
Simple redis commands
"""
import typing
import pathlib
import collections.abc as generic
import logging

from datetime import datetime
from datetime import timedelta

import redis

LOGGER: logging.Logger = logging.getLogger(pathlib.Path(__file__).stem)


def ping(connection: redis.Redis, **kwargs):
    return connection.ping(**kwargs)


def get(connection: redis.Redis, key: str) -> str | None:
    value: bytes | str | None = connection.get(key)
    if isinstance(value, bytes):
        value = value.decode()
    return value


def set_value(
    connection: redis.Redis,
    name: str,
    value: bytes | str | int | float,
    nx: bool = False,
    xx: bool = False,
    return_value: bool = False,
    keep_ttl: bool = False,
    ex: int | None = None,
    px: int | None = None,
    exat: datetime | None = None,
    pxat: datetime | None = None,
) -> str | int | None:
    if not isinstance(value, (str, bytes, int, float)):
        raise TypeError(f"Cannot store a value of '{value}' (type={value}) as a simple value.")

    return_value = connection.set(name, value, nx=nx, xx=xx, ex=ex, px=px, get=return_value, keepttl=keep_ttl, exat=exat, pxat=pxat)
    if isinstance(return_value, bytes):
        return_value = return_value.decode()
    return return_value
