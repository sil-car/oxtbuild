import re

from lxml import etree

from . import config 
from .util import get_filtered_file_list


DESCRIPTION_DATA = {
    '/xmlns:description': {},
    '/xmlns:description/xmlns:identifier': {
        'attrib': {
            'value': "OXT unique identifier: ",
        },
    },
    '/xmlns:description/xmlns:version': {
        'attrib': {
            'value': "OXT release version: ",
        },
    },
    '/xmlns:description/xmlns:platform': {
        'attrib': {
            'value': "OXT platform [all]: ",
        },
    },
    '/xmlns:description/xmlns:registration': {},
    '/xmlns:description/xmlns:registration/xmlns:simple-license': {
        'attrib': {
            'accept-by': "Approval level admin/user? [admin]: ",
            'suppress-on-update': "Suppress license agreement on update? [true]: ",
        },
    },
    '/xmlns:description/xmlns:registration/xmlns:simple-license/xmlns:license-text': {
        'attrib': {
            'xlink:href': "License filename (en): ",
            'lang': 'en',
        },
    },
    '/xmlns:description/xmlns:dependencies': {},
    '/xmlns:description/xmlns:dependencies/xmlns:OpenOffice.org-minimal-version': {
        'attrib': {
            'value': "Minimun OpenOffice.org version [3.0]: ",
            'dep:name': "Minimum version name [OpenOffice.org 3.0]: ",
        },
    },
    '/xmlns:description/xmlns:publisher': {},
    '/xmlns:description/xmlns:publisher/xmlns:name': {
        'attrib': {
            'xlink:href': "Publisher's URL (en): ",
            'lang': 'en',
        },
        'text': "Publisher's name (en): ",
    },
    '/xmlns:description/xmlns:display-name': {},
    '/xmlns:description/xmlns:display-name/xmlns:name': {
        'attrib': {
            'lang': 'en',
        },
        'text': "OXT display name (en): ",
    },
}

NSMAP_GEN = {
    None: "http://openoffice.org/extensions/description/2006",
    'dep': "http://openoffice.org/extensions/description/2006",
    'xlink': "http://www.w3.org/1999/xlink",
}

COMMENT_PKG = f"Packaged by oxtbuild v{config.VERSION}, {config.URL}"
INCOMPLETE_TEXT = '[incomplete]'


def ask(question):
    default = re.sub(r'.*\[(.*)\].*', r'\1', question)
    try:
        answer = input(question).strip('"').strip("'")
    except KeyboardInterrupt:
        print('\nInterrupted with Ctrl+C')
        exit(1)
    return answer if len(answer) > 1 else default

def write_xml_file(filepath_obj, xml_tree, docstring=None):
    filepath_obj.parent.mkdir(exist_ok=True)
    xml_tree.write(
        str(filepath_obj),
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
    simple_xpath = [p.split(':')[-1] for p in xpath_parts] # strip ns from each component
    return '/'.join(simple_xpath)

def get_element_from_xpath(xml_tree, nsmap, xpath):
    # print('ns:', xpath)
    elem = None
    elems = xml_tree.xpath(xpath, namespaces=nsmap)
    if len(elems) > 0:
        elem = elems[0]
    else:
        xpath = xpath_strip_ns(xpath)
        # print('simple:', xpath)
        elems = xml_tree.xpath(xpath, namespaces=nsmap)
        if len(elems) > 0:
            elem = elems[0]
    return elem

def initialize_xml_tree():
    root = etree.Element("description", nsmap=NSMAP_GEN)
    return etree.ElementTree(root)

def ensure_comment(parent, comment):
    comment_exists = False
    for n in parent.iter():
        if type(n) == etree._Comment and n.text == comment:
            comment_elem = n
            comment_exists = True
    if not comment_exists:
        parent.insert(0, etree.Comment(comment))
    else:
        cwords = comment_elem.text.split()
        if cwords[:3] == COMMENT_PKG[:3]:
            # Update packaging comment.
            comment_elem.text = COMMENT_PKG

def verify_description_template(description_file):
    description_file_string = str(description_file)
    # Get or initialize XML tree.
    if description_file.is_file():
        print("Verifying existing \"description.xml\".")
        try:
            tree = etree.parse(description_file_string)
        except etree.XMLSyntaxError as e:
            if len(description_file.read_text()) == 0: # file is empty
                tree = initialize_xml_tree()
            else:
                print(f"Error: {e}")
                exit(1)
    else:
        print("Creating new \"description.xml\".")
        tree = initialize_xml_tree()

    root = tree.getroot()
    tree_str_init = etree.tostring(tree)

    # Ensure top-level comments.
    doc_comment = 'Reference: https://wiki.documentfoundation.org/Documentation/DevGuide/Extensions#description.xml'
    ensure_comment(root, doc_comment)
    ensure_comment(root, COMMENT_PKG)

    nsmap = {k if k is not None else 'xmlns': v for k, v in root.nsmap.items()}
    for xpath, d in DESCRIPTION_DATA.items():
        elem = get_element_from_xpath(tree, nsmap, xpath)

        if elem is None:
            xpath_parts = xpath.split('/')
            tag = xpath_parts[-1].split(':')[-1]
            xpath_parent = '/'.join(xpath.split('/')[:-1])
            # print(f"{xpath_parent = }")
            parent = root
            if len(xpath_parent) > 0:
                parent = get_element_from_xpath(tree, nsmap, xpath_parent)

            # print(f"creating {parent.tag}/{tag}")
            elem = etree.SubElement(parent, tag, nsmap=NSMAP_GEN)

    # print_xml(tree)
    if etree.tostring(tree) != tree_str_init: # don't overwrite if unchanged
        write_xml_file(description_file, tree)

def verify_description_data(description_file, guided):
    """Check that each required attribute and text value is not empty.
    If "guided" option has been used, walk user through data entry.
    """
    description_file_string = str(description_file)
    tree = etree.parse(description_file_string)
    root = tree.getroot()
    tree_str_init = etree.tostring(tree)

    nsmap = {k if k is not None else 'xmlns': v for k, v in root.nsmap.items()}
    for xpath, d in DESCRIPTION_DATA.items():
        elem = get_element_from_xpath(tree, nsmap, xpath)

        for a, v in d.get('attrib', {}).items():
            a_parts = a.split(':')
            if len(a_parts) > 1:
                a = f"{{{nsmap.get(a_parts[0])}}}{a_parts[1]}"
            if elem.attrib.get(a, INCOMPLETE_TEXT) == INCOMPLETE_TEXT:
                if guided:
                    if len(v.split(':')) > 1:
                        elem.attrib[a] = ask(v)
                    else:
                        elem.attrib[a] = v
                else:
                    elem.attrib[a] = INCOMPLETE_TEXT

        t = d.get('text')
        if t:
            if elem.text == '' or elem.text == INCOMPLETE_TEXT:
                if guided:
                    if t[-2:] == ': ':
                        elem.text = ask(t)
                    else:
                        elem.text = t
                else:
                    elem.text = INCOMPLETE_TEXT

    # print_xml(tree)
    if etree.tostring(tree) != tree_str_init: # don't overwrite if unchanged
        write_xml_file(description_file, tree)

def generate_manifest(manifest_file, manifest_exts):
    # manifest_file = src_dir / 'META-INF/manifest.xml'
    nsmap = {'manifest': "http://openoffice.org/2001/manifest"}
    mime_base = 'application/vnd.sun.star'
    src_dir = manifest_file.parents[1]

    # Get list of files to include in manifest.
    file_list = get_filtered_file_list(manifest_exts.keys(), src_dir)
    m_files = [p.relative_to(src_dir) for p in file_list]

    # Generate XML.
    docstring = '<!DOCTYPE manifest:manifest PUBLIC "-//OpenOffice.org//DTD Manifest 1.0//EN" "Manifest.dtd">'
    manifest = etree.Element(f"{{{nsmap.get('manifest')}}}manifest", nsmap=nsmap)
    for m_file in m_files:
        ext = m_file.suffix
        manifest.append(etree.Element(
            f"{{{nsmap.get('manifest')}}}file-entry",
            {
                f"{{{nsmap.get('manifest')}}}media-type": f"{mime_base}{manifest_exts.get(ext)}",
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
