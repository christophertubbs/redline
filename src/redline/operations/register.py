"""
Register Credentials
"""
import typing
import collections.abc as generic
import logging
import pathlib

import redis

from redline import redis_pass

LOGGER: logging.Logger = logging.getLogger(pathlib.Path(__name__).stem)


def register_connection(connection: redis.Redis) -> str:
    try:
        if connection.ping():
            credential: redis_pass.Credential = redis_pass.register(connection=connection)
            return f"Connection to '{credential}' registered."
        else:
            return f"Could not register connection - a connection could not be made"
    except Exception as e:
        return f"Could not register connection: {e}"
