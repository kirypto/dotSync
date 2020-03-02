import sys as _sys
from argparse import HelpFormatter, OPTIONAL, ZERO_OR_MORE, SUPPRESS, ArgumentParser, Namespace
from enum import Enum
from pathlib import Path
from typing import Dict, Any, NoReturn, Text

from _version import __version__


class RawTextWithDefaultsHelpFormatter(HelpFormatter):
    """Help message formatter which adds default values to argument help and does not force specific newline positions.
    """

    def __init__(self, prog, indent_increment=2, max_help_position=30, width=None):
        super().__init__(prog, indent_increment=indent_increment, max_help_position=max_help_position, width=width)

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
    parser = UsageOnErrorArgumentParser(formatter_class=RawTextWithDefaultsHelpFormatter, )
    parser.usage = f"{parser.prog} [--version] [--help] <command> [<args>]"
    parser.add_argument("-v", "--version", action="version", help="shows the version and exits",
                        version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(title="File synchronization commands", required=True, dest="command")

    local_command_parser = subparsers.add_parser(
        f"{_SyncCommand.LOCAL}",
        help="update local dot files to match those from the corresponding files in the repository",
        description="update local dot files to match those from the corresponding files in the repository",
        usage=f"{parser.prog} local [--fileName FILENAME]",
        formatter_class=RawTextWithDefaultsHelpFormatter
    )
    local_command_parser.add_argument("--fileName", help="only synchronize the dot file of the specified name")

    repo_command_parser = subparsers.add_parser(
        f"{_SyncCommand.REPO}",
        help="update repository files to match those from the corresponding local dot files",
        description="update repository files to match those from the corresponding local dot files",
        usage=f"{parser.prog} repo [--fileName FILENAME]",
        formatter_class=RawTextWithDefaultsHelpFormatter
    )
    repo_command_parser.add_argument("--fileName", help="only synchronize the dot file of the specified name")

    config_command_parser = subparsers.add_parser(
        f"{_SyncCommand.CONFIG}",
        help=f"sets the configuration of {parser.prog}",
        description=f"sets the configuration of {parser.prog}",
        usage=f"{parser.prog} config [--location [LOCATION]]",
        formatter_class=RawTextWithDefaultsHelpFormatter
    ).add_mutually_exclusive_group(required=True)
    config_command_parser.add_argument("--location", help="sets the local dot file directory path to synchronize")
    config_command_parser.add_argument("--list", action="store_true", help="display current configuration")

    return parser.parse_args()


def _read_config() -> Dict[Text, Text]:
    from edn_format import loads
    config_file_path = Path("dotSync.edn")
    raw_config = config_file_path.read_text(encoding="UTF-8") if config_file_path.exists() else "{}"
    return dict(loads(raw_config))


def _write_config(config: Dict[Text, Text]):
    from edn_format import dumps
    config_file_path = Path("dotSync.edn")
    config_file_path.write_text(dumps(config), encoding="UTF-8")


def _command_main_config(arguments: Namespace) -> NoReturn:
    config = _read_config()

    if arguments.list:
        width = max([len(key) for key in config.keys()])
        for key, value in config.items():
            print(f"{key.ljust(width)} = {value}")

    elif arguments.location:
        dot_file_location = Path(arguments.location)
        if not dot_file_location.exists():
            raise ValueError(f"Provided location '{dot_file_location.resolve()}' does not exist")
        elif not dot_file_location.is_dir():
            raise ValueError(f"Provided location '{dot_file_location.resolve()}' is not a directory")

        config["location"] = str(dot_file_location.resolve())
        _write_config(config)

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
    try:
        _main()
    except Exception as e:
        print(f"!! {type(e).__name__}: {e}", file=_sys.stderr)
