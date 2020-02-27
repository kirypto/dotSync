import sys as _sys
from argparse import HelpFormatter, OPTIONAL, ZERO_OR_MORE, SUPPRESS, ArgumentParser, Namespace
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


def setup_args() -> Namespace:
    parser = UsageOnErrorArgumentParser(formatter_class=RawTextWithDefaultsHelpFormatter)
    parser.usage = f"{parser.prog} [--version] [--help] <command> [<args>]"
    parser.add_argument("-v", "--version", action="version", help="shows the version and exits",
                        version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(title="File synchronization commands", required=True, dest="command")

    local_command_parser = subparsers.add_parser(
        "local",
        help="update local dot files to match those from the corresponding files in the repository",
        description="update local dot files to match those from the corresponding files in the repository",
        usage=f"{parser.prog} local [--fileName FILENAME]",
    )
    local_command_parser.add_argument("--fileName", help="only synchronize the dot file of the specified name")

    repo_command_parser = subparsers.add_parser(
        "repo",
        help="update repository files to match those from the corresponding local dot files",
        description="update repository files to match those from the corresponding local dot files",
        usage=f"{parser.prog} repo [--fileName FILENAME]",
    )
    repo_command_parser.add_argument("--fileName", help="only synchronize the dot file of the specified name")

    config_command_parser = subparsers.add_parser(
        "config",
        help=f"sets the configuration of {parser.prog}",
        description=f"sets the configuration of {parser.prog}",
        usage=f"{parser.prog} config [--location LOCATION]",
    ).add_mutually_exclusive_group(required=True)
    config_command_parser.add_argument("--location", type=to_path, help="sets the local dot file directory path to synchronize")

    return parser.parse_args()


def to_path(path_str: str) -> Path:
    return Path(path_str)


def _command_main_config():
    raise NotImplementedError("Command 'config' is not yet implemented.")


def _command_main_repo():
    raise NotImplementedError("Command 'repo' is not yet implemented.")


def _command_main_local():
    raise NotImplementedError("Command 'local' is not yet implemented.")


def _main():
    arguments = setup_args()

    command = arguments.command
    if command == "config":
        _command_main_config()
    elif command == "repo":
        _command_main_repo()
    elif command == "local":
        _command_main_local()


if __name__ == '__main__':
    _main()
