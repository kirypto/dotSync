"""
    dotSync.py  A tool to simplify maintaining dot files repositories.
    Copyright (C) 2020  Garrett Hansen

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys as _sys
from argparse import HelpFormatter, OPTIONAL, ZERO_OR_MORE, SUPPRESS, ArgumentParser, Namespace
from enum import Enum
from pathlib import Path
from typing import Dict, Any, NoReturn, Text, Set, List, Tuple

from git import Repo, InvalidGitRepositoryError

from _dotSyncVersion import __version__


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
        usage=f"{parser.prog} local [--fileName FILENAME] [--pull]",
        formatter_class=RawTextWithDefaultsHelpFormatter
    )
    local_command_parser.add_argument("--fileName", help="only synchronize the dot file of the specified name")
    local_command_parser.add_argument("--pull", action="store_true", help="pulls changes from the remote before synchronizing")

    repo_command_parser = subparsers.add_parser(
        f"{_SyncCommand.REPO}",
        help="update repository files to match those from the corresponding local dot files",
        description="update repository files to match those from the corresponding local dot files",
        usage=f"{parser.prog} repo [--fileName FILENAME] [--push]",
        formatter_class=RawTextWithDefaultsHelpFormatter
    )
    repo_command_parser.add_argument("--fileName", help="only synchronize the dot file of the specified name")
    repo_command_parser.add_argument("--push", action="store_true", help="pushes changes to the remote after synchronizing")

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
    config_file_path = Path("dotSync.properties")
    raw_config = config_file_path.read_text(encoding="UTF-8") if config_file_path.exists() else ""

    if "\\\n" in raw_config or "\r\n\\" in raw_config:
        raise ValueError("Multi-line properties are not supported")

    raw_config_lines = [[txt.strip() for txt in prop_line.split("=")] for prop_line in raw_config.splitlines(keepends=False)
                        if not prop_line.strip().startswith("#") and prop_line.count("=") == 1]

    return {key: val for key, val in raw_config_lines}


def _write_config(config: Dict[Text, Text]):
    for key, val in config.items():
        if len(val.splitlines()) > 1:
            raise ValueError(f"Multi-line properties are not supported")

    raw_config_lines = [f"{key} = {val}" for key, val in config.items()]

    raw_config = "\n".join(raw_config_lines)

    config_file_path = Path("dotSync.properties")
    config_file_path.write_text(raw_config, encoding="UTF-8")


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
        dot_file_location = Path(arguments.location).resolve().absolute()
        if not dot_file_location.exists():
            raise ValueError(f"Provided location '{dot_file_location.as_posix()}' does not exist")
        elif not dot_file_location.is_dir():
            raise ValueError(f"Provided location '{dot_file_location.as_posix()}' is not a directory")

        config["location"] = dot_file_location.as_posix()
        _write_config(config)

    elif arguments.lineEnding:
        config["lineEnding"] = _ConfigLineEnding(arguments.lineEnding).value
        _write_config(config)

    else:
        raise RuntimeError(f"Command '{_SyncCommand.CONFIG}' failed, no operation could be identified")
    exit(0)


def _prepare_for_sync(arguments: Namespace, config: Dict[str, str]) -> Tuple[Set[str], Dict[str, Path], Dict[str, Path]]:
    if "location" not in config:
        raise ValueError(f"The local dot file location must be configured before synchronization")

    dot_files_repo_dir = Path("DotFiles").resolve().absolute()
    if not dot_files_repo_dir.exists():
        raise ValueError(f"Repository location '{dot_files_repo_dir.as_posix()}' does not exist")
    elif not dot_files_repo_dir.is_dir():
        raise ValueError(f"Repository location '{dot_files_repo_dir.as_posix()}' is not a directory")
    try:
        Repo(dot_files_repo_dir)
    except InvalidGitRepositoryError:
        raise ValueError(f"Repository location '{dot_files_repo_dir.as_posix()}' is not a git repository")

    stored_dot_files = {path.name: path for path in dot_files_repo_dir.iterdir()
                        if path.name != ".git" and path.is_file()}
    if len(stored_dot_files) == 0:
        raise ValueError("No files found in the repo to update")
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

    return file_names_to_sync, local_files_by_name, repo_files_by_name


def _pull_repo_changes_from_remote() -> Tuple[bool, str]:
    repo = Repo("DotFiles")
    pull_result = repo.git.pull()
    return pull_result != "Already up to date.", pull_result


def _push_repo_changes_to_remote():
    repo = Repo("DotFiles")
    repo.git.push()


def _commit_dot_file_changes() -> Tuple[bool, str]:
    repo = Repo("DotFiles")
    modified_file_list: str = repo.git.ls_files(modified=True)
    if "" == modified_file_list:
        return False, "No changes to commit"
    committed_file_names = [f"'{Path(path).name}'" for path in modified_file_list.splitlines()]
    repo.git.add(update=True)
    commit_message = f"[dotSync] Updating dot files: {', '.join(committed_file_names)}"
    repo.index.commit(commit_message)
    return True, commit_message


def _command_main_repo(arguments: Namespace) -> NoReturn:
    config = _read_config()
    file_names_to_sync, local_files_by_name, repo_files_by_name = _prepare_for_sync(arguments, config)

    if arguments.push:
        print(" - Checking remote in case of changes ... ", end="", flush=True)
        files_updated, git_log = _pull_repo_changes_from_remote()
        if not files_updated:
            print("done")
        else:
            print(f"\n{git_log}")
            raise ValueError("Aborting overwriting repo's dot files due them changing from 'git pull' (Repeat command if overwrite is desired)")

    for file_name in file_names_to_sync:
        print(f" - Updating repo's '{file_name}' from local version ... ", end="", flush=True)
        local_content_bytes = local_files_by_name[file_name].read_bytes()

        line_ending_normalization_setting = _ConfigLineEnding(config["lineEnding"]) if "lineEnding" in config else _ConfigLineEnding.NONE
        if line_ending_normalization_setting == _ConfigLineEnding.LF:
            local_content_bytes = local_content_bytes.replace(b"\r\n", b"\n")
        elif line_ending_normalization_setting == _ConfigLineEnding.CRLF:
            local_content_bytes = local_content_bytes.replace(b"\n", b"\r\n").replace(b"\r\r", b"\r")

        if repo_files_by_name[file_name].read_bytes() == local_content_bytes:
            print("no changes")
        else:
            repo_files_by_name[file_name].write_bytes(local_content_bytes)
            print("overwritten")

    if arguments.push:
        print(" - Committing changes ... ", end="", flush=True)
        commit_successful, message = _commit_dot_file_changes()
        if commit_successful:
            print("done")
            print(" - Pushing to remote ...", end="", flush=True)
            _push_repo_changes_to_remote()
            print("done")
        else:
            print(f"{message}")
    exit(0)


def _command_main_local(arguments: Namespace) -> NoReturn:
    config = _read_config()

    if arguments.pull:
        files_updated, git_log = _pull_repo_changes_from_remote()
        if files_updated:
            print(git_log)
        else:
            print(" - Repo is up to date")

    file_names_to_sync, local_files_by_name, repo_files_by_name = _prepare_for_sync(arguments, config)

    for file_name in file_names_to_sync:
        print(f" - Updating local's '{file_name}' with repository version ... ", end="", flush=True)
        repo_content_bytes = repo_files_by_name[file_name].read_bytes()

        if local_files_by_name[file_name].read_bytes() == repo_content_bytes:
            print("no changes")
        else:
            local_files_by_name[file_name].write_bytes(repo_content_bytes)
            print("overwritten")
    exit(0)


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
