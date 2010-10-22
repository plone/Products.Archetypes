import inspect
import os
import sys
import traceback
import pprint
from types import StringType
import warnings
import logging

from Products.Archetypes.config import DEBUG


logger = logging.getLogger('Archetypes')

class SafeFileWrapper:
    def __init__(self, fp):
        self.fp = fp

    def write(self, msg):
        """If for some reason we can't log, just deal with it"""
        try:
            self.fp.write(msg)
        except IOError, E:
            pass

    def close(self):
        self.fp.close()

    def __getattr__(self, key):
        return getattr(self.fp, key)


class Log:
    closeable = 0
    fp = None

    def __init__(self, target=sys.stderr):
        self.target = target
        self._open()

    def _open(self):
        if self.fp is not None and not self.fp.closed:
            return self.fp

        if type(self.target) is StringType:
            fp = open(self.target, "a+")
            self.closeable = 1
        else:
            fp = self.target

        self.fp = SafeFileWrapper(fp)


    def _close(self):
        if self.closeable:
            self.fp.close()

    def munge_message(self, msg, **kwargs):
        """Override this to messge with the message for subclasses"""
        return msg

    def log(self, msg, *args, **kwargs):
        self._open()
        self.fp.write("%s\n" % (self.munge_message(msg, **kwargs)))
        for arg in args:
            self.fp.write("%s\n" % pprint.pformat(arg))
        self._close()

    def log_exc(self, msg=None, *args, **kwargs):
        self.log(''.join(traceback.format_exception(*sys.exc_info())), offset=1)
        if msg: self.log(msg, collapse=0, deep=0, *args, **kwargs)


    def __call__(self, msg):
        self.log(msg)


class NullLog(Log):
    def __init__(self, target):
        pass
    def log(self, msg, **kwargs): pass

class ClassLog(Log):
    last_frame_msg = None

    def _process_frame(self, frame):
        path = frame[1] or '<string>'
        index = path.find("Products")
        if index != -1:
            path = path[index:]

        frame = "%s[%s]:%s\n" % (path, frame[2], frame[3])

        return frame

    def generateFrames(self, start=None, end=None):
        try:
            return inspect.stack()[start:end]
        except IndexError:
            # NOTE: this is required for OS-X Tiger somehow
            return []
        except TypeError:
            # NOTE: this is required for psyco compatibility
            #       since inspect.stack is broken after psyco is imported
            return []

    def munge_message(self, msg, **kwargs):
        deep = kwargs.get("deep", 1)
        collapse = kwargs.get("collapse", 1)
        offset   = kwargs.get("offset", 0) + 3

        frame = ''
        try:
            frames = self.generateFrames(offset, offset+deep)
            res = []
            for f in frames:
                res.insert(0, self._process_frame(f))
            frame = ''.join(res)
        finally:
            try:
                del frames
            except:
                pass

        if collapse == 1:
            if frame == self.last_frame_msg:
                frame = ''
            else:
                self.last_frame_msg = frame

        msg = "%s%s" %(frame, msg)
        return msg


class ZPTLogger(ClassLog):
    def generateFrames(self, start=None, end=None):
        frames = inspect.stack()
        for f in frames:
            # We want to look for either <script...
            # or <template...
            print f
        return frames

class ZLogger(ClassLog):
    def log(self, msg, *args, **kwargs):
        level = kwargs.get('level', logging.INFO)
        msg = "%s\n" % (self.munge_message(msg, **kwargs))
        for arg in args:
            msg += "%s\n" % pprint.pformat(arg)
        logger.log(level, msg)

    def log_exc(self, msg=None, *args, **kwargs):
        logger.exception(msg)

def warn(msg, level=3):
    # level is the stack level
    #   1: the line below
    #   2: the line calling this function
    #   3: the line calling the function that
    #      called this function
    if DEBUG:
        warnings.warn(msg, UserWarning, level)

def deprecated(msg, level=3):
    # level is the stack level
    #   1: the line below
    #   2: the line calling this function
    #   3: the line calling the function that
    #      called this function
    if DEBUG:
        warnings.warn(msg, DeprecationWarning, level)

_default_logger = ClassLog()
_zlogger = ZLogger()

log = zlog = _zlogger.log
log_exc    = _zlogger.log_exc
