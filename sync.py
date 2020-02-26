import argparse
from pathlib import Path

from _version import __version__


class RawTextWithDefaultsHelpFormatter(argparse.HelpFormatter):
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
        if '%(default)' not in action.help and action.default is not argparse.SUPPRESS:
            defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
            if action.option_strings or action.nargs in defaulting_nargs:
                arg_help += f"{prefix}<default: %(default)s>"
        return arg_help


def setup_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(formatter_class=RawTextWithDefaultsHelpFormatter)
    parser.usage = f"{parser.prog} [--version] [--help] <command> [<args>]"
    parser.add_argument("-v", "--version", action="version", help="shows the version and exits",
                        version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(title="File synchronization commands")
    subcommand_local = subparsers.add_parser("local", help="overwrites local dot files from the repository files")
    subcommand_repo = subparsers.add_parser("repo", help="overwrites dot repository files from the local files")
    subcommand_config = subparsers.add_parser("config", help=f"sets the configuration of {parser.prog}")
    config_command_options = subcommand_config.add_mutually_exclusive_group(required=True)
    config_command_options.add_argument("--location", type=Path, help="sets the local dot file directory path to synchronize")
    config_command_options.add_argument("--foo", help="sets the local dot file location to sync")

    # sync_command_group = parser.add_mutually_exclusive_group(required=True)
    # sync_command_group.add_argument("local", required=False, help="overwrites local dot files from the repository files")
    # sync_command_group.add_argument("repo", required=False, help="overwrites dot repository files from the local files")

    import sys
    if len(sys.argv) <= 1:
        parser.print_help()
        exit(1)
    return parser.parse_args()


def _main():
    args = setup_args()
    print(args.config.location)
    raise NotImplementedError("No functionality is implemented.")


if __name__ == '__main__':
    _main()
