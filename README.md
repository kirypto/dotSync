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

## Setup

When first running the script, use the `config` sub-command to specify the
local configuration file location. For example:  
`dotSync config --location "/path/to/user/home/"`

## Requirements

The script makes use of the following requirements:
- Python3
- Python3 packages: `typing`, `pathlib`, `enum`, `argparse`, `sys`

## License

See [LICENSE.txt](./LICENSE.txt) for complete details.







