import cffi
import platform
import ctypes.util

fromt c_defs import WIMLIB_DEFAULT_CDEFS

# Init flags for wimlib_global_init
INIT_FLAG_DONT_ACQUIRE_PRIVILEGES = 0x00000002  # Windows only
INIT_FLAG_STRICT_CAPTURE_PRIVILEGES = 0x00000004  # Windown only
INIT_FLAG_STRICT_APPLY_PRIVILEGES = 0x00000008  # Windows only
INIT_FLAG_DEFAULT_CASE_SENSITIVE = 0x00000010
INIT_FLAG_DEFAULT_CASE_INSENSITIVE = 0x00000020


def global_init(init_flags=0):
    """ Initialization for wimlib; called with flags=0 when any other function is invoked"""
    if (ret := _backend.lib.wimlib_global_init(flags)):
        raise WimException(ret)


def get_error_string(error_num):
    return _backend.ffi.string(_backend.lib.wimlib_get_error_string(error_num))


def set_error_printing(self, state):
    if (ret := _backend.lib.wimlib_set_print_errors(bool(state))):
        raise WimException(ret)


def set_error_file_by_name(self, file_path):
    if (ret := _backend.lib.wimlib_set_error_file_by_name(file_path)):
        raise WimException(ret)


def set_error_file_by_handle(self, file):
    raise NotImplementedError("Error: wimlib functions with FILE* argument not supported yet")


class WIMBackend(object):
    """
    WIMBackend

    This class creates the ffi and lib objects used by other wimlib
    classes. This class is for internal use only.
    """

    def __init__(self):
        self.os_family = platform.system()
        self.ffi = cffi.FFI()
        # Add OS specific C wimlib declarations
        # for Windows and Linux wimlib_tchar defenition
        self.ffi.cdef(self._get_platform_cdefs())
        # Add default C wimlib declarations
        self.ffi.cdef(WIMLIB_DEFAULT_CDEFS)
        self.lib = self.ffi.dlopen(self._get_wimlib_path())
        self.encoding = self._get_platform_encoding()


    def _get_platform_encoding(self):
        if self.os_family == "Windows":
            return "utf-16-le"
        return "utf-8"


    def _get_platform_cdefs(self):
        if self.os_family == "Windows":
            # wimlib_tchar is a 'wchar' on windows
            return "typedef wchar_t wimlib_tchar;"
        # on any other platforms is a 'char'
        return "typedef char wimlib_tchar;"


    def _get_wimlib_path(self):
        return ctypes.util.find_library("wim")

#                if self.os_family == "Linux":
#                        return "/usr/lib/libwim.so"
#                elif self.os_family == "Darwin":
#                        pass
#                elif self.os_family == "Windows":
#                        pass

#                raise NotImplementedError("The current platform is not supported ({0}, {1}).".format(self.os_family, platform.architecture()))
