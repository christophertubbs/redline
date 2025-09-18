"""
Object models for use throughout the application
"""
import typing
import collections.abc as generic
import pathlib
import logging
import dataclasses
import argparse

from datetime import datetime

from dateutil.parser import parse as parse_date

LOGGER: logging.Logger = logging.getLogger(pathlib.Path(__file__).stem)
ParamSpec = typing.ParamSpec("ParamSpec")

if typing.TYPE_CHECKING:
    import redis


@dataclasses.dataclass
class CommandArgument:
    name: str
    description: str
    key: str = dataclasses.field(default=None)
    converter: generic.Callable = dataclasses.field(default=None)
    default: typing.Any = dataclasses.field(default=None)
    action: str = dataclasses.field(default=None)
    extra: dict[str, typing.Any] = dataclasses.field(default_factory=dict)

    def add_to_parser(self, parser: argparse._ActionsContainer) -> argparse._ActionsContainer:
        new_argument_parameters: dict[str, typing.Any] = {
            "help": self.description,
            "default": self.default,
            **self.extra
        }

        if self.converter is not None:
            new_argument_parameters['type'] = self.converter

        if self.action:
            new_argument_parameters['action'] = self.action

        if self.key is None:
            parameter_name = self.name
        else:
            new_argument_parameters['dest'] = self.name
            if self.action not in ("store_true", "store_false"):
                new_argument_parameters['metavar'] = self.name

            parameter_name = self.key
            while not (parameter_name.startswith("--") and len(parameter_name) > 1 or parameter_name.startswith("-")):
                parameter_name = f"-{parameter_name}"

        try:
            parser.add_argument(parameter_name, **new_argument_parameters)
        except:
            LOGGER.error(f"Could not add the '{repr(self)}' argument.")
        return parser


@dataclasses.dataclass
class ArgumentGroup:
    arguments: list[CommandArgument]
    required: bool = dataclasses.field(default=False)

    def add_to_parser(self, parser: argparse._ActionsContainer) -> argparse._ActionsContainer:
        group = parser.add_mutually_exclusive_group(required=self.required)

        for argument in self.arguments:
            group = argument.add_to_parser(parser=group)

        return parser


@dataclasses.dataclass
class RedisCommand:
    name: str
    description: str
    function: generic.Callable[typing.Concatenate["redis.Redis", ParamSpec], typing.Any]
    arguments: list[CommandArgument|ArgumentGroup] = dataclasses.field(default_factory=list)

    def add_to_parser(self, subparsers: argparse._SubParsersAction) -> argparse._SubParsersAction:
        parser = subparsers.add_parser(
            name=self.name,
            description=self.description,
            help=self.description
        )
        for argument in self.arguments:
            parser = argument.add_to_parser(parser=parser)

        return subparsers

    def __call__(self, connection: "redis.Redis", *args, **kwargs) -> typing.Any:
        return self.function(connection, *args, **kwargs)
