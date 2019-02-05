#!/usr/bin/env python3

import xml.etree.ElementTree
import os.path
import argparse
import sys
import collections


MY_PATH = os.path.abspath(os.path.dirname(__file__))
GENERATE_PL_FILE_PATH = os.path.join(MY_PATH, 'generate-php.pl')


Syntax = collections.namedtuple('Syntax',
    ['name', 'extensions', 'firstLineGlobs', 'mimetype', 'priority', 'hidden'])


def parseSemicolonSeparatedList(line):
    return [item
            for item in line.split(';')
            if item]


def parseBoolAttribute(value):
    if value.lower() in ('true', '1'):
        return True
    elif value.lower() in ('false', '0'):
        return False
    else:
        raise UserWarning("Invalid bool attribute value '%s'" % value)


def safeGetRequiredAttribute(xmlElement, name, default):
    if name in xmlElement.attrib:
        return str(xmlElement.attrib[name])
    else:
        print("Required attribute '%s' is not set for element '%s'",
              name, xmlElement.tag, file=sys.stderr)
        return default


def loadLanguage(filePath):
    with open(filePath, 'r', encoding='utf-8') as definitionFile:
        try:
            root = xml.etree.ElementTree.parse(definitionFile).getroot()
        except Exception as ex:
            print('When opening %s:' % filePath, file=sys.stderr)
            raise ex

    highlightingElement = root.find('highlighting')

    return Syntax(
        name=safeGetRequiredAttribute(root, 'name', 'Error: .parser name is not set!!!'),
        extensions=parseSemicolonSeparatedList(safeGetRequiredAttribute(root, 'extensions', '')),
        firstLineGlobs=parseSemicolonSeparatedList(root.attrib.get('firstLineGlobs', '')),
        mimetype=parseSemicolonSeparatedList(root.attrib.get('mimetype', '')),
        priority=int(root.attrib.get('priority', '0')),
        hidden=parseBoolAttribute(root.attrib.get('hidden', 'false'))
    )


def _add_php(targetFileName, srcFileName):
    os.system("./generate-php.pl > syntax/{} < syntax/{}".format(targetFileName, srcFileName))


def load_language_db(xmlFilesPath):
    _add_php('javascript-php.xml', 'javascript.xml')
    _add_php('css-php.xml', 'css.xml')
    _add_php('html-php.xml', 'html.xml')

    xmlFileNames = [fileName
                    for fileName in os.listdir(xmlFilesPath)
                    if fileName.endswith('.xml')]

    languageNameToXmlFileName = {}
    mimeTypeToXmlFileName = {}
    extensionToXmlFileName = {}
    firstLineToXmlFileName = {}

    for xmlFileName in xmlFileNames:
        xmlFilePath = os.path.join(xmlFilesPath, xmlFileName)
        syntax = loadLanguage(xmlFilePath)
        if not syntax.name in languageNameToXmlFileName or \
           languageNameToXmlFileName[syntax.name][0] < syntax.priority:
            languageNameToXmlFileName[syntax.name] = (syntax.priority, xmlFileName)

        if syntax.mimetype:
            for mimetype in syntax.mimetype:
                if not mimetype in mimeTypeToXmlFileName or \
                   mimeTypeToXmlFileName[mimetype][0] < syntax.priority:
                    mimeTypeToXmlFileName[mimetype] = (syntax.priority, xmlFileName)

        if syntax.extensions:
            for extension in syntax.extensions:
                if extension not in extensionToXmlFileName or \
                   extensionToXmlFileName[extension][0] < syntax.priority:
                    extensionToXmlFileName[extension] = (syntax.priority, xmlFileName)

        if syntax.firstLineGlobs:
            for glob in syntax.firstLineGlobs:
                if not glob in firstLineToXmlFileName or \
                   firstLineToXmlFileName[glob][0] < syntax.priority:
                    firstLineToXmlFileName[glob] = (syntax.priority, xmlFileName)

    # remove priority, leave only xml file names
    for dictionary in (languageNameToXmlFileName,
                       mimeTypeToXmlFileName,
                       extensionToXmlFileName,
                       firstLineToXmlFileName):
        newDictionary = {}
        for key, item in dictionary.items():
            newDictionary[key] = item[1]
        dictionary.clear()
        dictionary.update(newDictionary)

    # Fix up php first line pattern. It contains <?php, but it is generated from html, and html doesn't contain it
    firstLineToXmlFileName['<?php*'] = 'html-php.xml'

    return {
        'languageNameToXmlFileName' : languageNameToXmlFileName,
        'mimeTypeToXmlFileName' : mimeTypeToXmlFileName,
        'extensionToXmlFileName' : extensionToXmlFileName,
        'firstLineToXmlFileName' : firstLineToXmlFileName,
    }


HEADER = """// This file is autogenerated by regenerate-language-db.py
// Do not edit it

#include <QMap>
#include <QString>

namespace Qutepart {"""

def write_syntax_db(out_file_path, syntax_db):
    with open(out_file_path, 'w') as out_file:
        print(HEADER, file=out_file)
        for key, valueMap in syntax_db.items():
            print('', file=out_file)
            print('QMap<QString,QString> create_{}() {{'.format(key), file=out_file)
            print('\tQMap<QString,QString> {}; '.format(key), file=out_file)
            for valKey, valValue in valueMap.items():
                print('\t{}["{}"] = "{}";'.format(key, valKey, valValue), file=out_file)
            print('\t return {};'.format(key), file=out_file)
            print('}}'.format(key), file=out_file)
            print('QMap<QString,QString> {} = create_{}();'.format(key, key), file=out_file)
        print ('}; // namespace Qutepart', file=out_file)


def parse_args():
    parser = argparse.ArgumentParser(description='Regenerate syntax db .cpp file')
    parser.add_argument('--xml_path', default='./syntax')
    parser.add_argument('--out_file', default='src/language_db_generated.cpp')
    return parser.parse_args()


def main():
    args = parse_args()

    syntax_db = load_language_db(args.xml_path)
    write_syntax_db(args.out_file, syntax_db)

    print('Done. Do not forget to commit the changes')


if __name__ == '__main__':
    main()
