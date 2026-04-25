# Dot Sync

A tool designed to simplify the process of maintaining 'dot files' and other
configuration files across multiple machines and home directories via the use
of personal git repositories.  

## Usage

Usage of `dotSync.py` is meant to work along side a git repository, and thus
has been written to behave similar to how git behaves on the command line.
Running `dotSync.py` or `dotSync.py --help` will print the usage and guide the
user. 

Similar to git, `dotSync` consists of a sub-command usage structure, currently
with the following implemented commands:

- **`local`**: Used to update the local config/dot files to match the
  corresponding files in the repository.
- **`repo`**: Used to update the config/dot files in the git repository to 
  match the corresponding local files.
- **`config`**: Used to configure the `dotSync` tool.

## Requirements

The script makes use of the following requirements:
- Python3 (with pip)
- An existing git repository (with ssh key or other auth setup so it can be fetched / pushed without entering credentials)
  
## Setup

- Clone this repository.
- Add the newly cloned directory to your `PATH` environment variable.
- Make sure `.PY` is in your `PATHEXT` environment variable. This allows `dotsync --help` to function instead of `dotsync.py`.
- Run `pip install -r .\path\to\dotSync\requirements.txt`.
- Run `dotsync config --repositoryPath .\path\to\dotFilesRepository`.
  - Ensure that your dot files repository has configured `user.name` and `user.email`.
- Run `dotsync config --localPaths "PATHS HERE"`, specifying all directories *containing* the files you want synced as comma separated paths.

## Other

- Licensed under GNU General Public License v3.0. See
  [LICENSE.txt](./LICENSE.txt) for complete details.
- Changelog can be found in the [CHANGELOG.md](./CHANGELOG.md) file.







