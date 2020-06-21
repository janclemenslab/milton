# _Milton_
Obfuscate and restore filenames for blinded annotation.

## Installation
Run: `pip install git+https://github.com/janclemenslab/milton` to install. Requires python 3.7+.

## Usage
Use via two shell commands:
- `milton obfuscate` for obfuscating files
- `milton restore` for restoring obfuscated files.

Run `milton obfuscate --help` and `milton restore --help` for a complete list of command line arguments.

## Example
```shell
milton obfuscate dat/localhost-20200619*
```
will obfuscate all experiments from June 19th 2020 in `dat`. The experimental and results folders (from `dat` and `res`) will be copied into a subfolder in `~/dat_blind/` (the path can be changed via `--target`), named after the current date and time. E.g. it will create `~/dat_blind/20201231_115900/dat/localhost-20200619_120544` and `~/dat_blind/20201231_115900/res/localhost-20200619_120544`, but with `20200619_120544` in all folder and file names obfuscated.

To restore annotation results, provide the path to the obfuscation folder and a mask to select which files to restore back to the original folders:
```shell
milton restore ~/dat_blind/20201231_115900/ -m *annotated.txt
```
`milton` will load the info required for restoration and look for all files in `res` that match the mask (in this case `*songmanual.zarr`, which is also the default). It will not touch the contents of `dat`.


