import re
from TAL import ndiff

def normalize_html(s):
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"(?s)\s+<", "<", s)
    s = re.sub(r"(?s)>\s+", ">", s)
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

def start_http(address, port):
    import sys
    from ZServer import asyncore
    from ZServer import zhttp_server, zhttp_handler
    import socket
    from ZServer import setNumberOfThreads
    setNumberOfThreads(4)

    try:
        hs = zhttp_server(
            ip=address,
            port=port,
            resolver=None,
            logger_object=None)
    except socket.error, why:
        if why[0] == 98: # address in use
            raise port_err % {'port':port,
                              'socktype':'TCP',
                              'protocol':'HTTP',
                              'switch':'-w'}
        raise
    # Handler for a published module. zhttp_handler takes 3 arguments:
    # The name of the module to publish, and optionally the URI base
    # which is basically the SCRIPT_NAME, and optionally a dictionary
    # with CGI environment variables which override default
    # settings. The URI base setting is useful when you want to
    # publish more than one module with the same HTTP server. The CGI
    # environment setting is useful when you want to proxy requests
    # from another web server to ZServer, and would like the CGI
    # environment to reflect the CGI environment of the other web
    # server.
    zh = zhttp_handler('Zope', '', {})
    zh._force_connection_close = 1
    hs.install_handler(zh)
    sys.ZServerExitCode=0
    asyncore.loop()
    sys.exit(sys.ZServerExitCode)
