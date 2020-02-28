import sys as _sys
from argparse import HelpFormatter, OPTIONAL, ZERO_OR_MORE, SUPPRESS, ArgumentParser, Namespace
from enum import Enum
from pathlib import Path
from typing import NoReturn, Text, Any

from _version import __version__


class RawTextWithDefaultsHelpFormatter(HelpFormatter):
    """Help message formatter which adds default values to argument help and does not force specific newline positions.
    """

    def _split_lines(self, text, width):
        return text.splitlines()

    def _get_help_string(self, action):
        arg_help = action.help
        prefix = "\n" if "\n" in arg_help else " "
        if action.required:
            arg_help += f"{prefix}<required>"
            return arg_help
        if '%(default)' not in action.help and action.default is not SUPPRESS:
            defaulting_nargs = [OPTIONAL, ZERO_OR_MORE]
            if action.option_strings or action.nargs in defaulting_nargs:
                arg_help += f"{prefix}<default: %(default)s>"
        return arg_help


class UsageOnErrorArgumentParser(ArgumentParser):
    def error(self, message: Text) -> NoReturn:
        self.print_usage(_sys.stderr)
        self.exit(2, f"!! ERROR {message}")

    def parse_args(self, args: Any = None, namespace: Any = None) -> Namespace:
        if len(_sys.argv) <= 1:
            self.print_help()
            exit(1)
        return super().parse_args(args=args, namespace=namespace)


class _SyncCommand(Enum):
    LOCAL = 'local'
    REPO = 'repo'
    CONFIG = 'config'

    def __str__(self) -> str:
        return self.value


def _parse_program_arguments() -> Namespace:
    parser = UsageOnErrorArgumentParser(formatter_class=RawTextWithDefaultsHelpFormatter)
    parser.usage = f"{parser.prog} [--version] [--help] <command> [<args>]"
    parser.add_argument("-v", "--version", action="version", help="shows the version and exits",
                        version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(title="File synchronization commands", required=True, dest="command")

    local_command_parser = subparsers.add_parser(
        f"{_SyncCommand.LOCAL}",
        help="update local dot files to match those from the corresponding files in the repository",
        description="update local dot files to match those from the corresponding files in the repository",
        usage=f"{parser.prog} local [--fileName FILENAME]",
    )
    local_command_parser.add_argument("--fileName", help="only synchronize the dot file of the specified name")

    repo_command_parser = subparsers.add_parser(
        f"{_SyncCommand.REPO}",
        help="update repository files to match those from the corresponding local dot files",
        description="update repository files to match those from the corresponding local dot files",
        usage=f"{parser.prog} repo [--fileName FILENAME]",
    )
    repo_command_parser.add_argument("--fileName", help="only synchronize the dot file of the specified name")

    config_command_parser = subparsers.add_parser(
        f"{_SyncCommand.CONFIG}",
        help=f"sets the configuration of {parser.prog}",
        description=f"sets the configuration of {parser.prog}",
        usage=f"{parser.prog} config [--location LOCATION]",
    ).add_mutually_exclusive_group(required=True)
    config_command_parser.add_argument("--location", help="sets the local dot file directory path to synchronize")

    return parser.parse_args()


def _command_main_config(arguments: Namespace) -> NoReturn:
    if "location" in arguments:
        dot_file_location = Path(arguments.location)
        if not dot_file_location.exists():
            raise ValueError(f"Provided location '{dot_file_location.resolve()}' does not exist")
        elif not dot_file_location.is_dir():
            raise ValueError(f"Provided location '{dot_file_location.resolve()}' is not a directory")

        print(f"It works! (path is: {dot_file_location.resolve()})")
    else:
        raise RuntimeError(f"Command '{_SyncCommand.REPO}' failed, no operation could be identified")
    exit(0)


def _command_main_repo(arguments: Namespace) -> NoReturn:
    raise NotImplementedError(f"Command '{_SyncCommand.REPO}' is not yet implemented.")


def _command_main_local(arguments: Namespace) -> NoReturn:
    raise NotImplementedError(f"Command '{_SyncCommand.LOCAL}' is not yet implemented.")


def _main():
    arguments = _parse_program_arguments()

    command = _SyncCommand(arguments.command)
    if command == _SyncCommand.CONFIG:
        _command_main_config(arguments)
    elif command == _SyncCommand.REPO:
        _command_main_repo(arguments)
    elif command == _SyncCommand.LOCAL:
        _command_main_local(arguments)


if __name__ == '__main__':
    _main()
