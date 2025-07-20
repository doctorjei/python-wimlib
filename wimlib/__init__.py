import atexit
from wimlib.backend import WIMBackend

__version__ = "0.1.2"
_backend = WIMBackend()


def wimlib_version():
    """ Get wimlib version number as tuple of (MAJOR, MINOR, PATCH) """
    ver = _backend.lib.wimlib_get_version()
    return (ver >> 20, (ver >> 10) & 0x3ff, ver & 0x3ff)


def initialize(init_flags=0):
    atexit.register(shutdown)


def shutdown():
    """ Cleanup function for wimlib, call is optional. """
    _backend.lib.wimlib_global_cleanup()


class WimException(Exception):
    def __init__(self, error):
        self.error = error
        if type(error) == int:
            super(WimException, self).__init__(get_error_string(self.error))
        else:
            super(WimException, self).__init__(self.error)


def join():
    raise NotImplementedError()


def join_with_progress():
    raise NotImplementedError()


def set_memory_allocator():
    raise NotImplementedError()


initialize()
