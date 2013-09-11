# vim: fileencoding=utf-8

from __future__ import print_function
from __future__ import unicode_literals

import os
import argparse
# import xml.etree.ElementTree as et
import lxml.etree as et


def create_qrc_file(subdir):
    qresource_elt = et.Element('qresource')
    for child in os.listdir(subdir):
        path = os.path.join(subdir, child)
        if not os.path.isfile(path):
            continue
        print('File found: {}'.format(child))
        alias, _ = os.path.splitext(child)
        file_elt = et.SubElement(qresource_elt, 'file', {'alias': alias})
        file_elt.text = os.path.relpath(path, os.getcwd())
    if len(qresource_elt):
        root = et.Element('RCC', {'version': '1.0'})
        root.append(qresource_elt)
        qrc_file_name = os.path.basename(subdir) + '.qrc'
        with open(qrc_file_name, 'w') as f:
            print('Writing to {}'.format(qrc_file_name))
            f.write(et.tostring(root,
                                encoding='utf-8',
                                pretty_print=True,
                                doctype='<!DOCTYPE RCC>'))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cwd', action='store_true',
                        help='change working directory to DIR before generating .qrc file')
    parser.add_argument('dir', nargs='?', default=os.curdir,
                        help='directory containing resources in separate folders')

    args = parser.parse_args()
    if not os.path.isdir(args.dir):
        raise Exception('"{}" is not a directory'.format(args.dir))

    if args.cwd:
        os.chdir(args.dir)

    dir_path = os.path.abspath(args.dir)
    for child in os.listdir(dir_path):
        child = os.path.join(dir_path, child)
        if os.path.isdir(child):
            print('Proceeding subdirectory: {}'.format(child))
            create_qrc_file(child)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        if __debug__:
            raise
        print(e.message)
        exit(1)