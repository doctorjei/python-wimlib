from wimlib import _backend, WIMError

# Init flags for wimlib_global_init
INIT_FLAG_DONT_ACQUIRE_PRIVILEGES = 0x00000002  # Windows only
INIT_FLAG_STRICT_CAPTURE_PRIVILEGES = 0x00000004  # Windown only
INIT_FLAG_STRICT_APPLY_PRIVILEGES = 0x00000008  # Windows only
INIT_FLAG_DEFAULT_CASE_SENSITIVE = 0x00000010
INIT_FLAG_DEFAULT_CASE_INSENSITIVE = 0x00000020

def global_init(init_flags=0):
    """ Initialization function for wimlib, called by default with flags=0"""
    ret = _backend.lib.wimlib_global_init(flags)
    if ret:
        raise WIMError(ret)
