#!/usr/bin/env python3
"""
Deploy redline locally
"""
import collections.abc as generic
import subprocess
import logging
import os
import pathlib
import sys
import argparse
import shutil
import errno

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s : %(message}s",
    datefmt="%Y-%m-%d %H:%M:%S%z"
)

LOGGER: logging.Logger = logging.getLogger(pathlib.Path(__file__).stem)
"""A dedicated logger for this file"""

if not shutil.which("pyinstaller"):
    raise RuntimeError(f"Cannot build and deploy redline - `pyinstaller` is required and not found.")


def get_relevant_paths() -> list[pathlib.Path]:
    """
    Get all paths that have been assigned to the user and may hold applications that may be called by name
    """
    relevant_paths: list[pathlib.Path] = []

    for path in PATH:
        try:
            resolved_path: pathlib.Path = path.expanduser().resolve()
        except Exception:
            continue
        if not resolved_path.is_dir():
            continue
        if resolved_path.name.lower() in ("bin", "apps", "windowsapps", "apps"):
            relevant_paths.append(resolved_path)

    return relevant_paths


def get_default_path() -> pathlib.Path | None:
    """
    Determine a safe default location for where to place the built application so that it may be invoked
    with name only without the extension within the name
    :return: The simplest path to where the built application can be placed and easily invoked
    """
    relevant_paths: list[pathlib.Path] = get_relevant_paths()
    if relevant_paths:
        return relevant_paths[0]
    return None


APPLICATION_NAME: str = "redline"
"""The default name for the application"""
PATH: generic.Sequence[pathlib.Path] = tuple([
    pathlib.Path(path)
    for path in os.environ.get("PATH", "").split(os.pathsep)
    if path.strip()
])
"""All the directories in the user's PATH environment variable"""
DEFAULT_BINARY_PATH: pathlib.Path | None = get_default_path()
"""The default location for where to place the built application"""


class Arguments:
    """
    Concrete command line arguments for the application
    """
    def __init__(self):
        self.name: str = APPLICATION_NAME
        """What to call the application"""
        self.output_directory: pathlib.Path | None = DEFAULT_BINARY_PATH
        """Where to ultimately place the application"""
        self._parse()
        self._validate()

    def _validate(self):
        """Throw exceptions if the parameters aren't valid, beyond normal parsing logic"""
        if self.output_directory is None:
            raise ValueError(f"No value was given for the output directory")
        if self.output_directory.is_file():
            raise FileExistsError(
                f"The output directory at '{self.output_directory}' is a file, not a directory. "
                f"This is not a valid output directory."
            )

    def _parse(self):
        """Parse command line arguments"""
        parser: argparse.ArgumentParser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument(
            "-n",
            "--name",
            dest="name",
            default=self.name,
            help="The name of the produced application"
        )
        parser.add_argument(
            "-o",
            "--output-directory",
            type=pathlib.Path,
            default=self.output_directory,
            required=(self.output_directory is None),
            help="Where to place the built application"
        )

        parsed_parameters: argparse.Namespace = parser.parse_args()

        for parameter_key, parameter_value in vars(parsed_parameters).items():
            if hasattr(self, parameter_key):
                setattr(self, parameter_key, parameter_value)
            else:
                raise KeyError(
                    f"'{parameter_key}' is not a valid value for "
                    f"'{pathlib.Path(__file__).stem}.{self.__class__.__qualname__}'"
                )


def build_application(name: str = APPLICATION_NAME) -> pathlib.Path:
    """
    Create the executable for the application

    :param name: What to call the application
    :return: The path to where the executable was built
    """
    project_root: pathlib.Path = pathlib.Path(__file__).parent
    entrypoint_path: pathlib.Path = project_root / 'src' / 'redline' / 'cli.py'

    if not entrypoint_path.is_file():
        raise FileNotFoundError(f"Cannot build redline - the entrypoint cannot be found in '{entrypoint_path}'")

    args: list[str] = [
        "pyinstaller",
        "--onefile",
        "--name",
        name,
        str(entrypoint_path)
    ]
    subprocess.run(
        args,
        capture_output=True,
        check=True,
        text=True,
    )
    output_directory: pathlib.Path = project_root / "dist"

    if os.name == "nt":
        candidate: pathlib.Path = output_directory / f"{name}.exe"
    else:
        candidate: pathlib.Path = output_directory / name

    if not candidate.is_file():
        raise FileNotFoundError(f"Could not find the built executable")

    return candidate


def link_output(source: pathlib.Path, destination: pathlib.Path, use_relative: bool = True):
    """
    Link the built executable to the target location

    :param source: The path to the built executable
    :param destination: Where the link should lie
    :param use_relative: Whether to use relative pathing
    """
    source = source.expanduser().resolve()
    destination_directory: pathlib.Path = destination.expanduser().resolve().parent

    if destination.is_symlink():
        try:
            current_destination_string: str | None = os.readlink(destination)
        except OSError:
            current_destination_string: str | None = None

        if current_destination_string:
            current_target_absolute: pathlib.Path = (destination_directory / current_destination_string).resolve()
            if current_target_absolute == source:
                return

        destination.unlink(missing_ok=True)
    elif destination.is_dir():
        raise IsADirectoryError(f"Cannot link '{source}' to '{destination}' - '{destination}' is a directory")
    elif destination.is_file():
        destination.unlink(missing_ok=True)

    if use_relative:
        link_target: str = os.path.relpath(str(source), start=str(destination_directory))
    else:
        link_target: str = str(source)

    # Create a temporary link and replace it for safety
    temporary_link: pathlib.Path = destination.with_name(destination.name + ".tmp-link")
    try:
        if temporary_link.exists() or temporary_link.is_symlink():
            temporary_link.unlink()

        if os.name == "nt":
            try:
                os.symlink(link_target, str(temporary_link), target_is_directory=source.is_dir(),)
            except OSError as exception:
                if exception.errno in {errno.EPERM, errno.EACCES, errno.ENOTSUP, getattr(errno, "ERROR_PRIVILEGE_NOT_HELD", 1314)}:
                    if source.is_dir():
                        raise IsADirectoryError(f"Cannot copy built application if the application is a directory")
                    shutil.copy2(str(source), str(destination))
                    return
                raise
        else:
            os.symlink(link_target, str(temporary_link))
        os.replace(str(temporary_link), str(destination))
    finally:
        if temporary_link.exists() or temporary_link.is_symlink():
            try:
                temporary_link.unlink(missing_ok=True)
            except OSError:
                pass


def main() -> int:
    """
    The main application logic
    :return: The exit code
    """
    arguments: Arguments = Arguments()

    try:
        build_path: pathlib.Path = build_application(name=arguments.name)
    except Exception as e:
        LOGGER.error(f"Could not build redline: {e}", exc_info=True)
        return 1

    try:
        arguments.output_directory.resolve().mkdir(parents=True, exist_ok=True)
        link_output(build_path.resolve(), (arguments.output_directory / build_path.name).resolve())
    except Exception as e:
        LOGGER.error(f"Could not move the built redline to a linked location: {e}", exc_info=True)
        return 1

    if arguments.output_directory in PATH:
        LOGGER.info(
            f"'{build_path.name}' was written to '{arguments.output_directory}'. It may be invoked in a terminal "
            f"session by just calling '{arguments.name}'"
        )
    else:
        LOGGER.info(
            f"'{build_path.name}' was written to '{arguments.output_directory}', which is not on your PATH. "
            f"It must be directly referenced by path, name, and extension in order to be invoked in the terminal"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
