"""
Graphviz local object referencs, allows any refrerenceable object to
produce a graph and a client side map. When we can export this as SVG
(and expect clients to handle it) it will be much easier to style to
the look of the site.

Inspired by code from Andreas Jung
"""


from urllib import unquote
from cStringIO import StringIO
from popen2 import popen2
from config import HAS_GRAPHVIZ, GRAPHVIZ_BINARY

def obj2id(obj):
    """ convert an issue to an ID """
    str = obj.absolute_url(1)
    return str2id(str)

def str2id(str):
    id = unquote(str)
    id = id.replace('-', '_')
    id = id.replace('/', '_')
    id=  id.replace(' ', '_')
    id=  id.replace('.', '_')
    return id



class Node:
    """ simple node class """

    def __init__(self, inst):
        self.id = obj2id(inst)
        self.url = inst.absolute_url()
        self.uid = inst.UID()
        self.title = inst.title_or_id()
        self.text = '%s: %s' % (inst.getId(), inst.Title())

    def __str__(self):
        return self.id

    __repr__ = __str__

class Edge:
    """ simple edge class """

    def __init__(self, src, dest, reference):
        self.src = src
        self.dest = dest
        self.relationship = reference.relationship

    def __str__(self):
        return '%s -> %s [label="%s", href="%s/reference_graph"]' % (self.src,
                                                    self.dest,
                                                    self.relationship,
                                                    self.src.url)
    def __hash__(self):
        return hash((self.src.uid,  self.dest.uid, self.relationship))

    __repr__ = __str__

def local_reference_graph(inst):
    nodes  = {}
    graphs = { 'forward' : {},
               'backward' : {},
               }

    rc = inst.reference_catalog

    references = rc.getReferences(inst)
    back_references = rc.getBackReferences(inst)

    node = Node(inst)
    nodes[inst.UID()] = node

    for ref in references:
        tob = ref.getTargetObject()
        target = Node(tob)
        if tob.UID() not in nodes:
            nodes[tob.UID()] = target

        e = Edge(node, target, ref)
        graphs['forward'].setdefault(ref.relationship, []).append(e)

    for ref in back_references:
        sob = ref.getSourceObject()
        source = Node(sob)
        if sob.UID() not in nodes:
            nodes[sob.UID()] = source

        e = Edge(source, node, ref)
        graphs['backward'].setdefault(ref.relationship, []).append(e)

    return graphs

# typo, but keep API
local_refernece_graph = local_reference_graph

def build_graph(graphs, inst):
    fp = StringIO()
    print >>fp, 'digraph G {'
    uid = inst.UID()
    seen = {}
    shown = {}
    for direction, graph in graphs.iteritems(): #forw/back
        for relationship, edges in graph.iteritems():
            rel_id = "unqualified"
            if relationship: rel_id = str2id(relationship)
            print >>fp, 'subgraph cluster_%s {' % rel_id


            for e in iter(edges):
                for n in e.src, e.dest:
                    if n not in seen:
                        seen[n] = 1
                        print >>fp, '\t%s [label="%s", href="%s"' % (n.id,
                                                                   n.title,
                                                                   n.url),
                        if uid == n.uid:
                            print >>fp, '\tstyle=filled, fillcolor=blue',
                        print >>fp, ']'

            for e in iter(edges):
                if e in shown: continue
                if direction == "forward":
                    print >>fp, '\t%s -> %s [label="%s", href="%s/reference_graph"]' % (
                    e.src,
                    e.dest,
                    e.relationship,
                    e.dest.url)
                else:
                    print >>fp, '\t%s -> %s [label="%s", href="%s/reference_graph"]' % (
                    e.src,
                    e.dest,
                    e.relationship,
                    e.src.url)
                shown[e] = e

            print >>fp, '\t}\n'

    print >>fp, "}"
    return fp.getvalue()




if HAS_GRAPHVIZ:
    def getDot(inst):
        g = local_reference_graph(inst)
        data = build_graph(g, inst)
        return data

    def get_image(inst, fmt):
        data = getDot(inst)

        stdout, stdin = popen2('%s -Gpack -T%s' % (GRAPHVIZ_BINARY, fmt))
        stdin.write(data)
        stdin.close()
        output = stdout.read()
        return output

    def get_png(inst): return get_image(inst, fmt="png")

    def get_cmapx(inst):
        data = getDot(inst)

        stdout, stdin = popen2('%s -Gpack -Tcmapx ' % GRAPHVIZ_BINARY)
        stdin.write(data)
        stdin.close()
        output = stdout.read()
        return output


else:
    def get_png(inst): return None
    def get_cmapx(inst): return None
