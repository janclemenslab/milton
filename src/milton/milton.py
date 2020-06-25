import os
import shutil
from pprint import pprint
import yaml
import datetime
import random
import string
import glob
import defopt
import tqdm
import logging
from typing import Dict, List


# suppress defopt format warnings
logging.basicConfig(level=logging.ERROR)


def _confirm(question, default=True):
    """
    Ask user a yes/no question and return their response as True or False.

    ``question`` should be a simple, grammatically complete question such as
    "Do you wish to continue?", and will have a string similar to " [Y/n] "
    appended automatically. This function will *not* append a question mark for
    you.

    By default, when the user presses Enter without typing anything, "yes" is
    assumed. This can be changed by specifying ``default=False``.

    Modified from fabfic.contrib.console.confirm (v.1.14)
    """
    # Set up suffix
    if default:
        suffix = "Y/n"
    else:
        suffix = "y/N"
    # Loop till we get something we like
    while True:
        response = input("%s [%s] " % (question, suffix)).lower()
        # Default
        if not response:
            return default
        # Yes
        if response in ['y', 'yes']:
            return True
        # No
        if response in ['n', 'no']:
            return False
        # Didn't get empty, yes or no, so complain and loop
        print("I didn't understand you. Please specify '(y)es' or '(n)o'.")


def _random_exptname():
    """Generate randome expt name NNNNNNNN_NNNNNN, where N is any number 0..9"""
    r = ''.join(random.choice(string.digits) for _ in range(8))
    r = r + '_' + ''.join(random.choice(string.digits) for _ in range(6))
    return r


def _invert(mapping: Dict) -> Dict:
    """Invert dictionary {k: v} -> {v: k}."""
    return {target: source for source, target in mapping.items()}


def _copy_and_rename(source_trunk: str, target_trunk: str, mapping: Dict,
                    keep_source: bool = True, overwrite: bool = False,
                    file_mask: str = '*', mode: str = 'obfuscate'):
    """[summary]

    Args:
        source_trunk (str): [description]
        target_trunk (str): [description]
        mapping (Dict): [description]
        keep_source (bool, optional): [description]. Defaults to True.
        overwrite (bool, optional): [description]. Defaults to False.
        file_mask (str, optional): [description]. Defaults to '*'.
        mode (str, optional): [description]. Defaults to 'obfuscate'.
    """

    for source, target in tqdm.tqdm(mapping.items()):
        copy_from = os.path.join(source_trunk, 'localhost-' + source)
        copy_to = os.path.join(target_trunk, 'localhost-' + target)

        os.makedirs(copy_to, exist_ok=True)
        search_pattern = os.path.join(copy_from, file_mask)
        files = [os.path.basename(f) for f in glob.glob(search_pattern)]
        if not files:
            tqdm.tqdm.write(f'   nothing mathing {search_pattern}')
        for file in files:
            copyfile_from = os.path.join(os.path.join(copy_from, file))
            copyfile_to = os.path.join(os.path.join(copy_to, file.replace(source, target)))

            if os.path.exists(copyfile_to):
                if not overwrite:
                    tqdm.tqdm.write(f"      skipping existing {copyfile_to}.\n      Call with `-o` to force overwrite.")
                    continue
                else:
                    tqdm.tqdm.write(f"      overwriting {copyfile_to}.")
            else:
                if mode == 'restore':
                    tqdm.tqdm.write(f"    restoring {copyfile_to}.")

            if keep_source:
                shutil.copyfile(copyfile_from, copyfile_to)
            else:
                shutil.move(copyfile_from, copyfile_to)


def _clean(path):
    print(f"Cleaning {path}.")
    if not os.path.exists(path):
        print(f"{path} does not exist - quitting.")
        return

    dirlist = os.listdir(path)
    print(f"WARNING: This will delete all {len(dirlist)} in {path}!")
    pprint(dirlist)

    if confirm("Are you sure?", default=True):
        for d in dirlist:
            target = os.path.join(path, d)
            if os.path.isdir(target):
                shutil.rmtree(target)
            elif os.path.isfile(target):
                os.remove(target)


def obfuscate(sources: List[str], *, target: str = 'HOME_FOLDER/dat_blind') -> str:
    """Obfuscate experiments for blinded annotation.

    Will look for folders matching SOURCES and
    obfuscate the corresponding folders from "res" and "dat".

    SOURCES can be a list and may contain wildcards. E.g., when in a
    rig-specific folder on the lab volume,
    "milton obfuscate 'dat/localhost-20200619*'" will match and obfuscate
    all folders from June 19th 2020.
    "milton obfuscate dat/localhost-20200619_161734 dat/localhost-20200619_190710" will
    obfuscate data from the two specified folders. Also accepts absolute paths.

    A new folder in TARGET named after the current date and time will
    be created and the matches in "res" and "dat" will be
    copied with obfuscated names.

    Restore with the created obfuscation folder as an argument:
    "milton restore "~/dat_blind/CURRENT_DATE_TIME".

    Args:
        sources (List[str]): Name pattern(s) for selecting which experiments to obfuscate.
        target (str): Root folder to copy obfuscated files into.

    Returns:
        str: Name of the obfuscation folder.
    """
    if target == 'HOME_FOLDER/dat_blind':
        target = os.path.expanduser('~/dat_blind')
    obfuscate_trunk = os.path.abspath(target)
    dirlist = []
    source_trunks = []
    for source in sources:
        # normalize source_trunk to point to dat even if we select files based on res
        source_trunk = os.path.dirname(os.path.abspath(source))
        if source_trunk.endswith('res'):
            source_trunk = source_trunk[:-3] + 'dat'
        source_trunks.append(source_trunk)
        # list all folders that match the source pattern
        dirlist.extend([os.path.basename(d)
                        for d in glob.glob(source)
                        if os.path.isdir(d)])

    if len(set(source_trunks)) > 1:
        raise ValueError(f"Sources need have the same parent directory.\nYou provided sources from {len(set(source_trunks))} parents:\n{set(source_trunks)}.")

    suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    obfuscate_trunk = os.path.join(obfuscate_trunk, suffix)
    breakpoint()

    print(f"Found {len(dirlist)} folders matching {sources}.")
    pprint(dirlist)
    print(f"Files in dat and res for these folders will be obfuscated to {obfuscate_trunk}/.")
    if _confirm("Do you want to continue?", default=True):
        # generate random names
        mapping = {d.replace('localhost-', ''): _random_exptname() for d in dirlist}

        # store all information required to restore files in a yaml file
        obfuscate_info = {'source_trunk': source_trunk,
                        'obfuscate_trunk': obfuscate_trunk,
                        'mapping': mapping}
        restore_file = os.path.join(obfuscate_info['obfuscate_trunk'], suffix + '.yaml')
        os.makedirs(obfuscate_info['obfuscate_trunk'], exist_ok=True)
        with open(restore_file, 'w') as f:
            yaml.safe_dump(obfuscate_info, f)

        # obfuscate files in dat and res
        for typ in ['dat', 'res']:
            _copy_and_rename(obfuscate_info['source_trunk'].replace('dat', typ),
                            os.path.join(obfuscate_info['obfuscate_trunk'], typ),
                            obfuscate_info['mapping'])
    return obfuscate_trunk


def restore(source: str, *, mask: str = '*songmanual.zarr',
            overwrite: bool = False, delete: bool = False) -> None:
    """Restore obfuscated results.

    "milton restore SOURCE -m MASK"

    Will restore the obfuscated files in SOURCE/res
    that match MASK to their original folder. Will not
    touch SOURCE/dat

    To be useful, MASK should contain wildcards. Defaults to match
    manual annotation files (`*songmanual.zarr`).

    Example:
    `milton restore dat_blind/20200621_110046 *_tuna.h5`
    will restore all files from "~/dat_blind/20200621_110046/res/"
    end in "_tuna.h5".

    Args:
        source (str): Folder with the obfuscated folder structure.
        mask (str): Selects file types to be restored.
        overwrite (bool): Overwrite existing files.
        delete (bool): Delete the *whole* obfuscated folder after restoration.
    """
    obfuscate_trunk = os.path.normpath(os.path.abspath(source))
    restore_file = os.path.basename(obfuscate_trunk) + '.yaml'
    restore_file = os.path.join(obfuscate_trunk, restore_file)

    with open(restore_file, 'r') as f:
        restore_info = yaml.safe_load(f)

    # use the original folder as destination for restore
    restore_trunk = os.path.abspath(restore_info['source_trunk'])
    # we only want to restore files in 'res' - replace dat with res at the end
    restore_trunk = restore_trunk[:-3] + 'res'

    print(f"Found {len(restore_info['mapping'])} obfuscated folders in '{obfuscate_trunk}/res',")
    print(f"All files in these folders matching {mask} will be restored to their original in {restore_trunk}:")
    pprint(["localhost-" + k for k in restore_info['mapping'].keys()])

    if overwrite:
        print(f"Existing files *WILL BE OVERWRITTEN* (call with `--no-overwrite` prevent overwrites).")
    else:
        print(f"Existing files will *NOT* be overwritten (call with `-o` force overwrites).")

    if _confirm("Do you want to continue?", default=True):
        _copy_and_rename(os.path.join(restore_info['obfuscate_trunk'], 'res'),
                        restore_trunk,
                        _invert(restore_info['mapping']),
                        overwrite=overwrite,
                        file_mask=mask,
                        mode='restore')
        if delete and _confirm(f"Do you really want to delete the folder {obfuscate_trunk}?", default=True):
            shutil.rmtree(obfuscate_trunk, ignore_errors=False)


def cli():
    defopt.run([obfuscate, restore])


if __name__ == "__main__":
    cli()
