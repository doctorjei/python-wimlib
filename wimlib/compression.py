from wimlib import _lib, _ffi, WimException

COMPRESSOR_FLAG_DESTRUCTIVE = 0x80000000
COMPRESSION_TYPE_NONE = 0
COMPRESSION_TYPE_XPRESS = 1
COMPRESSION_TYPE_LZX = 2
COMPRESSION_TYPE_LZMS = 3


class Compressor(object):
    def __init__(self, compression_type, block_size=0, level=0, dont_create=False):
        self.compression_type = compression_type
        self.block_size = block_size
        self.level = level
        self._compressor = None
        if not dont_create:
            self.create()

    def __del__(self):
        if self._compressor:
            _lib.wimlib_free_compressor(self._compressor)

    def create(self):
        compressor = _ffi.new("struct wimlib_compressor**")
        ret = _lib.wimlib_create_compressor(
            self.compression_type, self.block_size, self.level, compressor)
        if ret:
            raise WimException(ret)
        self._compressor = compressor[0]

    def compress(self, data):
        out_buffer = _ffi.new(
            "unsigned char[{0}]".format(self.block_size))
        out_size = _lib.wimlib_compress(
            data, len(data), out_buffer, self.block_size, self._compressor)
        return (out_size, bytes(_ffi.buffer(out_buffer, out_size)))

    def needed_memory(self):
        ret = _lib.wimlib_get_compressor_needed_memory(
            self.compression_type, self.block_size, self.level)
        if not ret:
            raise ValueError(
                "Error: compression type or block size are incorrect")


class Decompressor(object):
    def __init__(self, compression_type, block_size, dont_create=False):
        self.compression_type = compression_type
        self.block_size = block_size
        self._decompressor = None
        if not dont_create:
            self.create()

    def __del__(self):
        if self._decompressor:
            _lib.wimlib_free_decompressor(self._decompressor)

    def create(self):
        decompressor = _ffi.new("struct wimlib_decompressor**")
        ret = _lib.wimlib_create_decompressor(
            self.compression_type, self.block_size, decompressor)
        if ret:
            raise WimException(ret)
        self._decompressor = decompressor[0]

    def decompress(self, data, original_size):
        out_buffer = _ffi.new(
            "unsigned char[{0}]".format(original_size))
        ret = _lib.wimlib_decompress(
            data, len(data), out_buffer, original_size, self._decompressor)
        if ret:
            raise WimException("wimlib_decompress returned {0}.".format(ret))
        return bytes(_ffi.buffer(out_buffer, original_size))


def set_default_compression_level(compression_type, level):
    ret = _lib.wimlib_set_default_compression_level(
        compression_type, level)
    if ret:
        raise WimException(ret)


def get_compression_type_string(compression_type):
    return _ffi.string(_lib.wimlib_get_compression_type_string(compression_type))
