import re
from TAL import ndiff

def normalize_html(s):
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"/>", ">", s)
    return s

def nicerange(lo, hi):
    if hi <= lo+1:
        return str(lo+1)
    else:
        return "%d,%d" % (lo+1, hi)

def showdiff(a, b):
    cruncher = ndiff.SequenceMatcher(ndiff.IS_LINE_JUNK, a, b)
    for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
        if tag == "equal":
            continue
        print nicerange(alo, ahi) + tag[0] + nicerange(blo, bhi)
        ndiff.dump('<', a, alo, ahi)
        if a and b:
            print '---'
        ndiff.dump('>', b, blo, bhi)
