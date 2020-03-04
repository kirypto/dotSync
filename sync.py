import sys as _sys
from argparse import HelpFormatter, OPTIONAL, ZERO_OR_MORE, SUPPRESS, ArgumentParser, Namespace
from enum import Enum
from pathlib import Path
from typing import Dict, Any, NoReturn, Text, Set, List

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
    LOCAL = "local"
    REPO = "repo"
    CONFIG = "config"

    def __str__(self) -> str:
        return self.value


class _ConfigLineEnding(Enum):
    NONE = "none"
    LF = "lf"
    CRLF = "crlf"

    def __str__(self) -> str:
        return self.value

    @staticmethod
    def choices() -> List[str]:
        return [ending.value for ending in _ConfigLineEnding]


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
        usage=f"{parser.prog} config [--list] [--location PATH] [--lineEnding ENDING]",
        formatter_class=RawTextWithDefaultsHelpFormatter
    ).add_mutually_exclusive_group(required=True)
    config_command_parser.add_argument("--location", metavar="PATH", help="sets the local dot file directory path to synchronize")
    config_command_parser.add_argument("--lineEnding", metavar="ENDING", choices=_ConfigLineEnding.choices(),
                                       help=f"sets what line ending to normalize repo files with: {', '.join(_ConfigLineEnding.choices())}")
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
        if len(config) == 0:
            print("<EMPTY CONFIG>")
        else:
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

    elif arguments.lineEnding:
        config["lineEnding"] = _ConfigLineEnding(arguments.lineEnding).value
        _write_config(config)

    else:
        raise RuntimeError(f"Command '{_SyncCommand.CONFIG}' failed, no operation could be identified")
    exit(0)


def _command_main_repo(arguments: Namespace) -> NoReturn:
    config = _read_config()

    stored_dot_files = {path.name: path for path in Path("DotFiles").iterdir()}
    file_names_to_sync: Set[str]

    if arguments.fileName:
        if arguments.fileName not in stored_dot_files:
            raise ValueError(f"No stored file matches the name '{arguments.fileName}'")
        file_names_to_sync = {arguments.fileName}
    else:
        file_names_to_sync = set(stored_dot_files.keys())

    repo_files_by_name: Dict[str, Path] = {path.name: path for name, path in stored_dot_files.items()
                                           if path.name in file_names_to_sync}
    local_files_by_name: Dict[str, Path] = {path.name: path for path in Path(config["location"]).iterdir()
                                            if path.name in file_names_to_sync}

    if local_files_by_name.keys() != repo_files_by_name.keys():
        missing_files = ", ".join({f"'{name}'" for name in file_names_to_sync if name not in local_files_by_name.keys()})
        raise ValueError(f"Could not find local file(s) matching: {missing_files}")

    for file_name in file_names_to_sync:
        print(f" - Overwriting repo's '{file_name}' with local version ... ", end="")
        local_content_bytes = local_files_by_name[file_name].read_bytes()

        line_ending_normalization_setting = _ConfigLineEnding(config["lineEnding"]) if "lineEnding" in config else _ConfigLineEnding.NONE
        if line_ending_normalization_setting == _ConfigLineEnding.LF:
            local_content_bytes = local_content_bytes.replace(b"\r\n", b"\n")
        elif line_ending_normalization_setting == _ConfigLineEnding.CRLF:
            local_content_bytes = local_content_bytes.replace(b"\n", b"\r\n").replace(b"\r\r", b"\r")

        repo_files_by_name[file_name].write_bytes(local_content_bytes)
        print("Done!")
    exit(0)


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
        raise e
