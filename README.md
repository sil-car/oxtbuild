# oxtbuild
Package files as a LibreOffice extension file (OXT). Specifically, this script
1. takes as input the path to a folder containing the files needing to be packaged
1. creates the required `META-INF/manifest.xml` file (Not all required filetypes
   are handled automatically, though. The user needs to verify that it's contents
   are complete once it's generated.)
1. creates the required `description.xml` file with required fields added
1. optionally, guides the user through entering data in the description fields

## Installation

Download source files, e.g. to `~/`, then install with:
```
$ python3 -m pip install ~/oxtbuild
```
