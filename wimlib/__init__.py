import atexit
from wimlib.backend import WimBackend

__version__ = "0.1.2"
_backend = WimBackend()
_lib = _backend.lib
_ffi = _backend.ffi

# Init flags for wimlib_global_init
INIT_FLAG_DONT_ACQUIRE_PRIVILEGES = 0x00000002  # Windows only
INIT_FLAG_STRICT_CAPTURE_PRIVILEGES = 0x00000004  # Windown only
INIT_FLAG_STRICT_APPLY_PRIVILEGES = 0x00000008  # Windows only
INIT_FLAG_DEFAULT_CASE_SENSITIVE = 0x00000010
INIT_FLAG_DEFAULT_CASE_INSENSITIVE = 0x00000020

# For debugging; some library functions fail / silently crash program, so we'll
# use the command line tools as a substitute in those cases.
_use_executable_mount = False


def initialize(init_flags=0):
    atexit.register(shutdown)


def shutdown():
    """ Cleanup function for wimlib, call is optional. """
    _lib.wimlib_global_cleanup()


def wimlib_version():
    """ Get wimlib version number as tuple of (MAJOR, MINOR, PATCH) """
    ver = _lib.wimlib_get_version()
    return (ver >> 20, (ver >> 10) & 0x3ff, ver & 0x3ff)


class WimException(Exception):
    def __init__(self, error):
        self.error = error
        if type(error) == int:
            super(WimException, self).__init__(get_error_string(self.error))
        else:
            super(WimException, self).__init__(self.error)


def get_error_string(error_num):
    return _ffi.string(_lib.wimlib_get_error_string(error_num))


def global_init(init_flags=0):
    """ Initialization for wimlib; called with flags=0 when any other function is invoked"""
    if (ret := _lib.wimlib_global_init(flags)):
        raise WimException(ret)


def set_error_printing(state):
    if (ret := _lib.wimlib_set_print_errors(bool(state))):
        raise WimException(ret)


def set_error_file_by_name(file_path):
    if (ret := _lib.wimlib_set_error_file_by_name(file_path)):
        raise WimException(ret)


def set_error_file_by_handle(file):
    raise NotImplementedError("Error: wimlib functions with FILE* argument not supported yet")


def join():
    raise NotImplementedError()


def join_with_progress():
    raise NotImplementedError()


def set_memory_allocator():
    raise NotImplementedError()


initialize()
