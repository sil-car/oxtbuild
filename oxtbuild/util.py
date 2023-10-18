import argparse

from pathlib import Path


def get_args():
    parser = argparse.ArgumentParser(
        prog='oxtbuild',
        description='Build an OXT package from a source directory. The required "META-INF/manifest.xml" file is automatically generated, and the required "description.xml" file is generated and/or structurally verified.',
        # epilog='[TBD]',
    )
    parser.add_argument(
        '-g', '--guided',
        action='store_true',
        help='add required data to descrtiption.xml by responding to a list of questions',
    )
    parser.add_argument(
        '-s', '--strict',
        action='store_true',
        help='only allow approved filetypes to be packaged',
    )
    parser.add_argument(
        'folder',
        type=Path,
        help='source directory containing files to package as OXT',
    )
    return parser.parse_args()

def get_filtered_file_list(extensions, src_dir):
    file_list = []
    for ext in extensions:
        file_list.extend(src_dir.glob(f'**/*{ext}'))
    return file_list
