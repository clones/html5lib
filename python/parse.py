#!/usr/bin/env python
"""usage: %prog [options] filename

Parse a document to a simpletree tree, with optional profiling
"""
#RELEASE move ./examples/

import sys
import os
from optparse import OptionParser

#RELEASE remove
from src import html5parser, liberalxmlparser
from src import treebuilders, serializer, treewalkers
#END RELEASE
#RELEASE add
#from html5lib import html5parser, liberalxmlparser
#from html5lib import treebuilders, serializer, treewalkers
#END RELEASE

def parse():
    optParser = getOptParser()
    opts,args = optParser.parse_args()

    try:
        f = args[-1]
        # Try opening from the internet
        if f.startswith('http://'):
            try:
                import urllib
                f = urllib.urlopen(f).read()
            except: pass
        else:
            try:
                # Try opening from file system
                f = open(f)
            except IOError: pass
    except IndexError:
        sys.stderr.write("No filename provided. Use -h for help\n")
        sys.exit(1)

    treebuilder = treebuilders.getTreeBuilder(opts.treebuilder)

    if opts.xml:
        p = liberalxmlparser.XHTMLParser(tree=treebuilder)
    else:
        p = html5parser.HTMLParser(tree=treebuilder)

    if opts.fragment:
        parseMethod = p.parseFragment
    else:
        parseMethod = p.parse

    if opts.profile:
        import hotshot
        import hotshot.stats
        prof = hotshot.Profile('stats.prof')
        prof.runcall(parseMethod, f)
        prof.close()
        # XXX - We should use a temp file here
        stats = hotshot.stats.load('stats.prof')
        stats.strip_dirs()
        stats.sort_stats('time')
        stats.print_stats()
    elif opts.time:
        import time
        t0 = time.time()
        document = parseMethod(f)
        t1 = time.time()
        printOutput(p, document, opts)
        t2 = time.time()
        sys.stdout.write("\n\nRun took: %fs (plus %fs to print the output)"%(t1-t0, t2-t1))
    else:
        document = parseMethod(f)
        printOutput(p, document, opts)

def printOutput(parser, document, opts):
    if opts.encoding:
        print "Encoding:", parser.tokenizer.stream.charEncoding
    if not opts.no_tree:
        if opts.xml:
            sys.stdout.write(document.toxml("utf-8"))
        elif opts.html:
            tokens = treewalkers.getTreeWalker(opts.treebuilder)(document)
            for text in serializer.HTMLSerializer().serialize(tokens, encoding='utf-8'):
                sys.stdout.write(text)
        elif opts.hilite:
            sys.stdout.write(document.hilite("utf-8"))
        else:
            print document
            if not hasattr(document,'__iter__'): document = [document]
            for fragment in document:
                print parser.tree.testSerializer(fragment).encode("utf-8")
    if opts.error:
        errList=[]
        for pos, message in parser.errors:
            errList.append("Line %i Col %i"%pos + " " + message)
        sys.stdout.write("\nParse errors:\n" + "\n".join(errList)+"\n")

def getOptParser():
    parser = OptionParser(usage=__doc__)

    parser.add_option("-p", "--profile", action="store_true", default=False,
                      dest="profile", help="Use the hotshot profiler to "
                      "produce a detailed log of the run")
    
    parser.add_option("-t", "--time",
                      action="store_true", default=False, dest="time",
                      help="Time the run using time.time (may not be accurate on all platforms, especially for short runs)")
    
    parser.add_option("", "--no-tree", action="store_true", default=False,
                      dest="no_tree", help="Do not print output tree")
    
    parser.add_option("-b", "--treebuilder", action="store", type="string",
                      dest="treebuilder", default="simpleTree")

    parser.add_option("-e", "--error", action="store_true", default=False,
                      dest="error", help="Print a list of parse errors")

    parser.add_option("-f", "--fragment", action="store_true", default=False,
                      dest="fragment", help="Parse as a fragment")

    parser.add_option("-x", "--xml", action="store_true", default=False,
                      dest="xml", help="Output as xml")
    
    parser.add_option("", "--html", action="store_true", default=False,
                      dest="html", help="Output as html")
    
    parser.add_option("", "--hilite", action="store_true", default=False,
                      dest="hilite", help="Output as formatted highlighted code.")
    
    parser.add_option("-c", "--encoding", action="store_true", default=False,
                      dest="encoding", help="Print character encoding used")
    return parser

if __name__ == "__main__":
    parse()