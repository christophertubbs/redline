"""
Objects representing a specific redis command that may be invoked
"""
import typing
import collections.abc as generic
import pathlib
import logging


from redline import model

from redline.operations import simple


LOGGER: logging.Logger = logging.getLogger(pathlib.Path(__file__).stem)


def __get_commands() -> generic.Sequence[model.RedisCommand]:
    from dateutil.parser import parse as parse_date
    commands: list[model.RedisCommand] = []
    commands.append(
        model.RedisCommand(
            name="ping",
            description="Test the connection to the redis instance",
            function=simple.ping,
        )
    )
    commands.append(
        model.RedisCommand(
            name="GET",
            arguments=[
                model.CommandArgument(
                    name="key",
                    description="The key whose value to get"
                )
            ],
            function=simple.get,
            description="Get the value for a simple key"
        )
    )
    commands.append(
        model.RedisCommand(
            name="SET",
            arguments=[
                model.CommandArgument(
                    name="name",
                    description="The key to set"
                ),
                model.CommandArgument(
                    name="value",
                    description="The value for the key"
                ),
                model.ArgumentGroup(
                    arguments=[
                        model.CommandArgument(
                            name="nx",
                            key="--if-not-exists",
                            action="store_true",
                            description="Only set the value if the key does not exist"
                        ),
                        model.CommandArgument(
                            name="xx",
                            key="--if-exists",
                            action="store_true",
                            description="Only set the value if it exists"
                        )
                    ]
                ),
                model.CommandArgument(
                    name="return_value",
                    key="--get",
                    action="store_true",
                    description="Return the value of the key"
                ),
                model.ArgumentGroup(
                    arguments=[
                        model.CommandArgument(
                            name="ex",
                            key="--expire-in-seconds",
                            converter=int,
                            description="The seconds in the future to expire this value"
                        ),
                        model.CommandArgument(
                            name="px",
                            key="--expire-in-milliseconds",
                            converter=int,
                            description="The milliseconds in the future to expire this value"
                        ),
                        model.CommandArgument(
                            name="exat",
                            key="--expire-at",
                            converter=parse_date,
                            description="Datetime to expire at"
                        ),
                        model.CommandArgument(
                            name="keep_ttl",
                            key="--keep-ttl",
                            action="store_true",
                            description="Maintain the TTL of the key"
                        )
                    ]
                ),
            ],
            function=simple.set_value,
            description="Set a simple value"
        )
    )
    return commands


COMMANDS: generic.Sequence[model.RedisCommand] = __get_commands()
