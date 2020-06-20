# _Milton_
Obfuscate and restore filenames for blinded annotation.

## Installation
Run: `pip install git+https://github.com/janclemenslab/milton` to install. Requires python 3.7+.

## Usage
Use via two shell commands:
- `milton obfuscate` for obfuscating files
- `milton restore` for restoring obfuscated files.

Run `milton obfuscate --help` and `milton restore --help` for a complete list of command line arguments.

### Obfuscate
`milton obfuscate dat/localhost-20200619*` will obfuscate all experiments from June 19th. The experimental folders will be copied into a subfolder in `~/dat_blind/` (the path can be changed via `--target`), named after the current date and time (e.g. `~/dat_blind/20201231_115900`). Information for restoring the obfuscated files will be stored in `~/dat_blind/20201231_115900/20201231_115900.yaml`.

### Restore
`milton restore ~/dat_blind/20201231_115900/ -m *annotated.txt` will restore all files ending in `annotated.txt` in all sub-directories of `~/dat_blind/20201231_115900`.


