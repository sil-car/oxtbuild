import re

from lxml import etree


DESCRIPTION_DATA = {
    '/xmlns:identifier': {
        'attrib': {
            'value': "OXT unique identifier: ",
        },
    },
    '/xmlns:version': {
        'attrib': {
            'value': "OXT release version: ",
        },
    },
    '/xmlns:platform': {
        'attrib': {
            'value': "OXT platform [all]: ",
        },
    },
    '/xmlns:registration': {},
    '/xmlns:registration/xmlns:simple-license': {
        'attrib': {
            'accept-by': "Approval level admin/user? [admin]: ",
            'suppress-on-update': "Suppress license agreement on update? [true]: ",
        },
    },
    '/xmlns:registration/xmlns:simple-license/xmlns:license-text': {
        'attrib': {
            'xlink:href': "License filename (en): ",
            'lang': 'en',
        },
    },
    '/xmlns:dependencies': {},
    '/xmlns:dependencies/xmlns:OpenOffice.org-minimal-version': {
        'attrib': {
            'value': "Minimun OpenOffice.org version [3.0]: ",
            'dep:name': "Minimum version name [OpenOffice.org 3.0]: ",
        },
    },
    '/xmlns:publisher': {},
    '/xmlns:publisher/xmlns:name': {
        'attrib': {
            'xlink:href': "Publisher's URL (en): ",
            'lang': 'en',
        },
        'text': "Publisher's name (en): ",
    },
    '/xmlns:display-name': {},
    '/xmlns:display-name/xmlns:name': {
        'attrib': {
            'lang': 'en',
        },
        'text': "OXT display name (en): ",
    },
}

def ask(question):
    default = re.sub(r'.*\[(.*)\].*', r'\1', question)
    answer = input(question).strip('"').strip("'")
    return answer if len(answer) > 1 else default

def write_xml_file(filepath_obj, xml_tree, docstring=None):
    xml_tree.write(
        filepath_obj,
        pretty_print=True,
        xml_declaration=True,
        encoding='UTF-8',
        doctype=docstring
        )

def print_xml(xml_tree, docstring=None):
    print(
        etree.tostring(
            xml_tree.getroot(),
            pretty_print=True,
            xml_declaration=True,
            doctype=docstring,
            encoding='UTF-8'
            ).decode()
        )

def xpath_strip_ns(ns_xpath):
    xpath_parts = ns_xpath.split('/') # list path components
    xpath_simple = [p.split(':')[-1] for p in xpath_parts] # strip ns from each component
    return '/'.join(xpath_simple)

def xml_path_in_tree(xml_tree, ns_xpath, nsmap):
    exists = False
    # In order to use absolute path, "find" must be used on tree instead of element.
    if xml_tree.find(ns_xpath, namespaces=nsmap) is not None:
        exists = True
    return exists

def verify_description(description_file):
    nsmap_gen = {
        None: "http://openoffice.org/extensions/description/2006",
        'dep': "http://openoffice.org/extensions/description/2006",
        'xlink': "http://www.w3.org/1999/xlink",
    }
    
    if description_file.is_file():
        print("Verifying existing \"description.xml\".")
        tree = etree.parse(description_file)
        root = tree.getroot()
    else:
        print("Creating new \"description.xml\".")
        root = etree.Element("description", nsmap=nsmap_gen)
        tree = etree.ElementTree(root)
    tree_str_init = etree.tostring(tree)
    nsmap = {k if k is not None else 'xmlns': v for k, v in root.nsmap.items()}
    for xpath, d in DESCRIPTION_DATA.items():
        xpath_simple = xpath_strip_ns(xpath)
        # xpath_simple = xpath
        if not xml_path_in_tree(tree, xpath, nsmap):
            xpath_parts = xpath_simple.split('/')
            tag = xpath_parts[-1].split(':')[-1]
            xpath_parent = '/'.join(xpath_parts[:-1])
            if xpath_parent == '':
                parent = root
            else:
                # When searching for subelement created by this script, 'parent'
                #   xpath should not include namespace info.
                parent = tree.find(xpath_parent, namespaces=nsmap)
            attribs = {}
            for a, v in d.get('attrib', {}).items():
                a_parts = a.split(':')
                if len(a_parts) > 1:
                    a = f"{{{nsmap.get(a_parts[0])}}}{a_parts[1]}"
                # Get & set data.
                if v[-2:] == ': ':
                    attribs[a] = ask(v)
                else:
                    attribs[a] = v
            elem = etree.SubElement(parent, tag, attribs, nsmap=nsmap_gen)
            t = d.get('text')
            if t:
                if t[-2:] == ': ':
                    elem.text = ask(t)
                else:
                    elem.text = t

    # print_xml(tree)
    if etree.tostring(tree) != tree_str_init: # don't overwrite if unchanged
        write_xml_file(description_file, tree)

def generate_manifest(src_dir):
    manifest_file = src_dir / 'META-INF/manifest.xml'
    nsmap = {'manifest': "http://openoffice.org/2001/manifest"}
    mime_base = 'application/vnd.sun.star'
    supported_exts = {
        '.xcu': '.configuration-data',
    }
    # Find all files required to be listed in manifest.xml.
    m_files = []
    for ext in supported_exts.keys():
        m_files.extend(src_dir.glob(f'**/*{ext}'))
    # Convert to relative paths.
    m_files = [p.relative_to(src_dir) for p in m_files]
    # Generate XML.
    docstring = '<!DOCTYPE manifest:manifest PUBLIC "-//OpenOffice.org//DTD Manifest 1.0//EN" "Manifest.dtd">'
    manifest = etree.Element(f"{{{nsmap.get('manifest')}}}manifest", nsmap=nsmap)
    for m_file in m_files:
        ext = m_file.suffix
        manifest.append(etree.Element(
            f"{{{nsmap.get('manifest')}}}file-entry",
            {
                f"{{{nsmap.get('manifest')}}}media-type": f"{mime_base}{supported_exts.get(ext)}",
                f"{{{nsmap.get('manifest')}}}full-path": str(m_file),
            },
            nsmap=nsmap,
            ))
    # print_xml(etree.ElementTree(manifest))
    write_xml_file(manifest_file, etree.ElementTree(manifest), docstring=docstring)

def list_manifest_filepaths(xml_tree):
    root = xml_tree.getroot()
    nsmap = {k if k is not None else 'xmlns': v for k, v in root.nsmap.items()}
    file_entries = xml_tree.findall('.//manifest:file-entry', nsmap)
    return [e.xpath('@manifest:full-path', namespaces=nsmap)[0] for e in file_entries]    

def get_xml_tree(data):
    return etree.parse(data)
