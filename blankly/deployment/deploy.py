import os
import tempfile
import sys
import zipfile
from typing import List


def get_python_version():
    return '.'.join(str(i) for i in sys.version_info[:2])


def zip_dir(path, ignore_files):
    global temporary_zip_file
    temporary_zip_file = tempfile.TemporaryDirectory()
    dist_directory = temporary_zip_file.__enter__()

    # dist_directory = tempfile.TemporaryDirectory().__enter__()
    # with tempfile.TemporaryDirectory() as dist_directory:
    source = os.path.abspath(path)

    model_path = os.path.join(dist_directory, 'model.zip')
    zip_ = zipfile.ZipFile(model_path, 'w', zipfile.ZIP_DEFLATED)
    zipdir(source, zip_, ignore_files)
    zip_.close()

    return model_path


def zipdir(path, ziph, ignore_files: list):
    # From https://stackoverflow.com/a/1855118/8087739
    # Notice we're using this instead of shutil because it allows customization such as passwords and skipping
    # directories
    # ziph is zipfile handle

    filtered_ignore_files = []
    # Set all the ignored files to be absolute
    for i in range(len(ignore_files)):
        # Reject this case
        if ignore_files[i] == "":
            continue
        filtered_ignore_files.append(os.path.abspath(ignore_files[i]))

    for root, dirs, files in os.walk(path, topdown=True):
        for file in files:
            # (Modification) Skip everything that is in the blankly_dist folder
            filepath = os.path.join(root, file)

            if not (os.path.abspath(filepath) in filtered_ignore_files) and not (root in filtered_ignore_files):
                # This takes of the first part of the relative path and replaces it with /model/
                relpath = os.path.relpath(filepath,
                                          os.path.join(path, '..'))
                relpath = os.path.normpath(relpath).split(os.sep)
                relpath[0] = os.sep + 'model'
                relpath = os.path.join(*relpath)

                ziph.write(filepath, relpath)
