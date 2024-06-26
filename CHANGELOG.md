### DotSync Changelog

---

#### 2020.0.0 _(Initial release)_

- Added `dotSync` python program
- Added `config` sub-command for configuring `dotSync` 
- Added `repo` sub-command for updating the files in the repo from local files
- Added `local` sub-command for updating local files from those in the repo
- Added documentation for main program and sub-commands

---

#### 2020.0.1

- Added Git integration
   - Added `--pull` flag for `local` sub-command
   - Added `--push` flag for `repo` sub-command
   - Added `--commitOnly` flag for `repo` sub-command

---

#### 2020.0.2

- Added support for multiple local dot file locations via comma delimited `localPaths` config
- Changed `config` sub-command `--location` to `--localPaths`
- Changed config property `location` to `localPaths` 
- Fixed file reading and writing to be relative to the `dotSync.py` install 
  directory instead of wherever the script is run from

---
