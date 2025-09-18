#!/usr/bin/env python3
"""
Run commands against a redis instance
"""
import typing
import collections.abc as generic
import pathlib
import logging
import argparse
import sys

from pprint import pprint

import redis

from redline import redis_pass
from redline import model

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)] %(levelname)s : %(message}s",
    datefmt="%Y-%m-%d %H:%M:%S%z"
)

from redline.commands import COMMANDS

LOGGER: logging.Logger = logging.getLogger(pathlib.Path(__file__).stem)


class Arguments:
    def __init__(self):
        self.command: str = ""
        self.host: str | None = None
        self.port: int | None = None
        self.username: str | None = None
        self.password: str | None = None
        self.db: int = 0
        self.args: dict[str, typing.Any] = {}
        self.__parse()

    def __parse(self):
        parser: argparse.ArgumentParser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument(
            "--host",
            "-H",
            default=None,
            dest="host",
            help="The host to connect to",
        )
        parser.add_argument(
            "-u",
            "--username",
            default=None,
            dest="username",
            help="A specific username to use to connect"
        )
        parser.add_argument(
            "-p",
            "--password",
            dest="password",
            default=None,
            help="A specific password to use to connect"
        )
        parser.add_argument(
            "--db",
            dest="db",
            default=self.db,
            type=int,
            help="The data namespace to connect to"
        )
        parser.add_argument(
            "-P",
            "--port",
            dest="port",
            type=int,
            default=None,
            help="The specific port to connect to"
        )

        subparsers: argparse._SubParsersAction = parser.add_subparsers(required=True, dest="command")

        for command in COMMANDS:
            subparsers = command.add_to_parser(subparsers=subparsers)

        parsed_arguments: argparse.Namespace = parser.parse_args()

        argument_map: dict[str, typing.Any] = dict(vars(parsed_arguments))

        self.host = argument_map.pop("host", None)
        self.port = argument_map.pop("port", None)
        self.password = argument_map.pop("password", None)
        self.username = argument_map.pop("username", None)
        self.db = argument_map.pop("db", self.db)
        self.command = argument_map.pop('command')
        self.args.update(argument_map)


def main() -> int:
    """The main application logic"""
    arguments: Arguments = Arguments()

    matching_commands: list[model.RedisCommand] = list(filter(lambda cmd: cmd.name == arguments.command, COMMANDS))

    if not matching_commands:
        raise KeyError(f"Could not find a command to execute named '{arguments.command}'")

    command: model.RedisCommand = matching_commands[0]

    connection_arguments: dict[str, typing.Any] = {
        "db": arguments.db
    }

    if arguments.host:
        connection_arguments['host'] = arguments.host

    if arguments.port:
        connection_arguments['port'] = arguments.port

    if arguments.password:
        connection_arguments['password'] = arguments.password

    if arguments.username:
        connection_arguments['username'] = arguments.username

    connection: redis.Redis | None = redis_pass.get_connection(**connection_arguments)

    if connection is None:
        raise Exception(f"Could not find a redis connection. Register one via redis-pass in order to use this.")

    result = command(connection, **arguments.args)
    pprint(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
