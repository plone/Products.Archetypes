from Products.Archetypes.utils import basename
import re
import os, os.path


bin_search_path = [
    '/usr/bin',
    '/usr/local/bin',
    ]


def bin_search(binary):
    """search the bin_path defined in __init__ for a given binary
    returning its fullname or None"""
    result = None
    mode   = os.R_OK | os.X_OK
    for p in bin_search_path:
        path = os.path.join(p, binary)
        if os.access(path, mode) == 1:
            result = path
            break
    return result




_bodyre = re.compile('<body.*?>', re.DOTALL|re.I)
_endbodyre = re.compile('</body', re.DOTALL|re.I)

def bodyfinder(text):
    bod = _bodyre.search(text)
    if not bod: return text

    end = _endbodyre.search(text)
    if not end: return text
    else:
        return text[bod.end():end.start()]

_stylere    = re.compile(r'^\s*<html.*<style.*?>', re.DOTALL|re.I)
_endstylere = re.compile(r'</style', re.DOTALL|re.I)

def stylefinder(text):
    bod = _stylere.search(text)
    if not bod: return ''

    end = _endstylere.search(text)
    if not end: return ''
    else: return text[bod.end():end.start()]


EvilMicroSoftTagRE = re.compile("((<!--\[)|(<!\[)).*?((\]-->)|(\]>))", re.M)
EvilMSXMLRE        = re.compile("<[ovwxp]:.*?/>", re.M)
def stripMSTags(text):
    text = re.sub(EvilMicroSoftTagRE, '', text)
    text = re.sub(EvilMSXMLRE, '', text)

    #IE honors line-height so setting the default font doesn't really help
    text = re.sub("line-height:.*?;", '', text)

    return text
