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


__version__ = "0.1"


def confirm(question, default=True):
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


def random_exptname():
    r = ''.join(random.choice(string.digits) for _ in range(8))
    r = r + '_' + ''.join(random.choice(string.digits) for _ in range(6))
    return r


def invert(mapping):
    return {target: source for source, target in mapping.items()}


def copy_and_rename(source_trunk, target_trunk, mapping,
                    keep_source=True, overwrite=False,
                    file_mask='*', mode='obfuscate'):

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


def clean(*, path: str = 'dat_blind'):
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


def obfuscate(source: str, *, target: str = 'HOME_FOLDER/dat_blind') -> str:
    """Obfuscate experiments for blinded annotation.

    'milton obfuscate SOURCE -t TARGET'

    Will look for directories matching SOURCE into
    subfolders with obfuscated name in TARGET.

    SOURCE can contain wildcards.
    E.g. when in a rig-specific folder on the lab volume,
    "milton obfuscate 'dat/localhost-20200619*'" will match all directories from June 19th 2020.
    Will move matching directories into '~/dat_blind/CURRENT_DATETIME/'
    and obfuscate their names.

    The root folder to store obfuscated directories in can be changed
    from  '~/dat_blind' via '--target PATH'.

    Annotations should be saved to the obfuscated data folder
    '~/dat_blind/CURRENT_DATETIME/OBFUSCATED_NAME', not in a 'res' folder.

    Information for restoring the files will be created at
    '~/dat_blind/CURRENT_DATETIME/CURRENT_DATETIME.yaml'.

    Restore with the created obfuscation folder as an argument:
    "milton restore "~/dat_blind/CURRENT_DATETIME".

    Args:
        source (str): Name pattern for selecting which experiments to obfuscate.
                      Use wildcards! E.g. 'dat/localhost-2020619*' will obfuscate
                      all experiments from Juneteenth 2020.
        target (str): Root directory to copy obfuscated files into.

    Returns:
        str: Name of the obfuscation folder.
    """
    if target == 'HOME_FOLDER/dat_blind':
        target = os.path.expanduser('~/dat_blind')

    source_trunk = os.path.dirname(os.path.abspath(source))
    obfuscate_trunk = os.path.abspath(target)

    # search_pattern = os.path.join(source_trunk, mask)
    dirlist = [os.path.basename(d)
            for d in glob.glob(source)
            if os.path.isdir(d)]
    suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    obfuscate_trunk = os.path.join(obfuscate_trunk, suffix)

    print(f"Found {len(dirlist)} directories matching {source}.")
    pprint(dirlist)
    print(f"These files will be obfuscated to {obfuscate_trunk}/.")
    if confirm("Do you want to continue?", default=True):
        mapping = {d.replace('localhost-', ''): random_exptname() for d in dirlist}
        obfuscate_info = {'source_trunk': source_trunk,
                          'obfuscate_trunk': obfuscate_trunk,
                          'mapping': mapping}
        pprint(obfuscate_info)
        restore_file = os.path.join(obfuscate_info['obfuscate_trunk'], suffix + '.yaml')
        os.makedirs(obfuscate_info['obfuscate_trunk'], exist_ok=True)

        print(f"Saving restoration info to {restore_file}.")
        with open(restore_file, 'w') as f:
            yaml.safe_dump(obfuscate_info, f)

        # obfuscate
        copy_and_rename(obfuscate_info['source_trunk'],
                        obfuscate_info['obfuscate_trunk'],
                        obfuscate_info['mapping'])
        return obfuscate_trunk


# def restore(restore_file: str, *, restore_trunk: str = 'res', restore_overwrite: bool = False, restore_mask: str = '*_songmanual.zarr'):
def restore(source: str, *, mask: str = '*_songmanual.zarr', target: str = 'res', overwrite: bool = False):
    """Restore obfuscated results.

    'milton SOURCE -m MASK -t TARGET'

    Will restore the original names of all obfuscated files
    in SOURCE matching MASK and move them to TARGET.

    To be useful, MASK should contain wildcards. By default, all files
    ending in '_songmanual.zarr' will be restored.

    If called from within the rig-specific folder on the lab volume,
    files will be restored to their respective subfolders in the 'res'.

    Args:
        source (str): Folder with the obfuscated directories.
        mask (str): Selects file types to be restored.
        target (str): Root directory into which the files should restored.
        overwrite (bool): Overwrite existing files.
    """
    obfuscate_trunk = os.path.normpath(os.path.abspath(source))
    restore_file = os.path.basename(obfuscate_trunk) + '.yaml'
    restore_file = os.path.join(obfuscate_trunk, restore_file)
    restore_trunk = os.path.abspath(target)

    with open(restore_file, 'r') as f:
        restore_info = yaml.safe_load(f)
    print(f"Found {len(restore_info['mapping'])} directories in {restore_file}.")
    print(f"Files in these folders matching {mask} will be restored")
    print(f"to the following folders in {restore_trunk}")
    pprint(["localhost-" + k for k in restore_info['mapping'].keys()])

    if overwrite:
        print(f"Existing files *WILL BE OVERWRITTEN* (call with `--no-overwrite` prevent overwrites).")
    else:
        print(f"Existing files will *NOT* be overwritten (call with `-o` force overwrites).")

    if confirm("Do you want to continue?", default=True):
        copy_and_rename(restore_info['obfuscate_trunk'],
                        restore_trunk,
                        invert(restore_info['mapping']),
                        overwrite=overwrite,
                        file_mask=mask,
                        mode='restore')


def cli():
    defopt.run([obfuscate, restore])


if __name__ == "__main__":
    cli()
