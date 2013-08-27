# vim: fileencoding=utf-8

from __future__ import print_function
from __future__ import unicode_literals

import os
import argparse
# import xml.etree.ElementTree as et
import lxml.etree as et


def create_qrc_file(path):
    dirname = os.path.basename(path)
    qresource_elt = et.Element('qresource')
    for child in os.listdir(path):
        child = os.path.join(path, child)
        if not os.path.isfile(child):
            continue
        alias, _ = os.path.splitext(os.path.basename(child))
        file_elt = et.SubElement(qresource_elt, 'file', {'alias': alias})
        file_elt.text = os.path.relpath(child, os.getcwd())
    if len(qresource_elt):
        root = et.Element('RCC', {'version': '1.0'})
        root.append(qresource_elt)
        with open(dirname + '.qrc', 'w') as f:
            f.write(et.tostring(root,
                                encoding='utf-8',
                                pretty_print=True,
                                doctype='<!DOCTYPE RCC>'))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', nargs='?', default=os.curdir,
                        help='dirpath containing resource folders')

    args = parser.parse_args()
    if not os.path.isdir(args.dir):
        raise Exception('"{}" is not a dirpath'.format(args.dir))
    path = os.path.abspath(args.dir)
    for child in os.listdir(path):
        child = os.path.join(path, child)
        if os.path.isdir(child):
            create_qrc_file(os.path.join(path, child))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        if __debug__:
            raise
        print(e.message)
        exit(1)