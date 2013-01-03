#!/usr/bin/env python

import os.path
import json

from qutepart.syntax.syntax import SyntaxManager
from qutepart.syntax.loader import loadSyntax

def main():
    xmlFilesPath = os.path.join(os.path.dirname(__file__), 'qutepart', 'syntax')
    xmlFileNames = [fileName for fileName in os.listdir(xmlFilesPath) \
                        if fileName.endswith('.xml')]
    
    syntaxNameToXmlFileName = {}
    mimeTypeToXmlFileName = {}
    extensionToXmlFileName = {}

    for xmlFileName in xmlFileNames:
        xmlFilePath = os.path.join(xmlFilesPath, xmlFileName)
        syntax = loadSyntax(SyntaxManager(), xmlFilePath)
        if not syntax.name in syntaxNameToXmlFileName or \
           syntaxNameToXmlFileName[syntax.name][0] < syntax.priority:
            syntaxNameToXmlFileName[syntax.name] = (syntax.priority, xmlFileName)
        
        for mimetype in syntax.mimetype:
            if not mimetype in mimeTypeToXmlFileName or \
               mimeTypeToXmlFileName[mimetype][0] < syntax.priority:
                mimeTypeToXmlFileName[mimetype] = (syntax.priority, xmlFileName)
        
        for extension in syntax.extensions:
            if not extension in extensionToXmlFileName or \
               extensionToXmlFileName[extension][0] < syntax.priority:
                extensionToXmlFileName[extension] = (syntax.priority, xmlFileName)
        
    # remove priority, leave only xml file names
    for dictionary in (syntaxNameToXmlFileName, mimeTypeToXmlFileName, extensionToXmlFileName):
        newDictionary = {}
        for key, item in dictionary.items():
            newDictionary[key] = item[1]
        dictionary.clear()
        dictionary.update(newDictionary)
    
    result = {}
    result['syntaxNameToXmlFileName'] = syntaxNameToXmlFileName
    result['mimeTypeToXmlFileName'] = mimeTypeToXmlFileName
    result['extensionToXmlFileName'] = extensionToXmlFileName

    with open(os.path.join(xmlFilesPath, 'syntax_db.json'), 'w') as syntaxDbFile:
        json.dump(result, syntaxDbFile, sort_keys=True, indent=4)
    
    print 'Done. Do not forget to commit the changes'

if __name__ == '__main__':
    main()