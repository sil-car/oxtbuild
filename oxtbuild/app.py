#!/usr/bin/env python3

"""Package source folder as a LibreOffice extension file (OXT).
"""

# Ref:
#   - https://wiki.documentfoundation.org/Documentation/DevGuide/Extensions#File_Format

import sys
import zipfile

import xmltools

from util import get_args
from util import get_filtered_file_list


def verify_file_in_zip(oxt_zip, filerelpath):
    if filerelpath not in oxt_zip.namelist():
        print(f"Error: Required file missing: {filerelpath}")
        exit(1)

def main():
    args = get_args()
    required_files = {
        'manifest': 'META-INF/manifest.xml',
        'description': 'description.xml',
    }

    src_dir = args.folder
    if not src_dir.is_dir():
        print(f"Error: Not a directory: {src_dir}")
        exit(1)

    # Verify description.xml structure.
    xmltools.verify_description_template(src_dir / required_files.get('description'))
    xmltools.verify_description_data(src_dir / required_files.get('description'), args.guided)
    exit()

    src_parent_dir = src_dir.parent
    oxt_path = src_parent_dir / f"{src_dir.name}.oxt"

    # Generate manifest.xml file.
    manifest_exts = {
        '.xcu': '.configuration-data',
    }
    manifest_xml_file = src_dir / required_files.get('manifest')
    xmltools.generate_manifest(manifest_xml_file, manifest_exts)

    # Generate list of final OXT files.
    allowed_exts = [
        '.md',
        '.txt',
        '.xml',
    ]
    allowed_exts.extend(manifest_exts.keys())

    # # Generate/verify description.xml file.
    # xmltools.verify_description(src_dir / required_files.get('description'))

    # Create zipfile & verify contents.
    with zipfile.ZipFile(oxt_path, mode='w', compression=zipfile.ZIP_DEFLATED) as z:
        # for f in sorted(src_dir.glob('**/*')):
        for f in sorted(get_filtered_file_list(allowed_exts, src_dir)):
            if f.is_file(): # skip folders, which are added implicitly with files
                z.write(f, arcname=f.relative_to(src_dir))

        # Confirm required and manifested files.
        for p in required_files.values():
            verify_file_in_zip(z, p)
        manifest_xml = xmltools.get_xml_tree(z.open(required_files.get('manifest')))
        manifest_files = xmltools.list_manifest_filepaths(manifest_xml)
        for f in manifest_files:
            verify_file_in_zip(z, f)


if __name__ == '__main__':
    main()
