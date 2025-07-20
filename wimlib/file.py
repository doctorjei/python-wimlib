import wimlib
import wimlib.image
import wimlib.info

from wimlib import _backend
from wimlib.error import WIMError

# Image specificaion consts
NO_IMAGE = 0
ALL_IMAGES = -1


class WIMFile(object):
    def __del__(self):
        _backend.lib.wimlib_free(self._wim_struct)


    # Specialized constructor for calling backend functions easily.
    def __init__(self, loader, path="", has_baking_file=False):
        self._has_baking_file = has_baking_file
        self.path = path

        if (error := loader(wim_struct := _backend.ffi.new("WIMStruct **"))):
            raise WIMError(error)

        self._wim_struct = wim_struct[0]
        self.images = wimlib.image.ImageCollection(self)


    @staticmethod
    def new(compression=0):
        loader = lambda s: _backend.lib.wimlib_create_new_wim(compression, s)
        return WIMFile(loader)


    @staticmethod
    def from_file(path, flags=0, callback=None, context=None):
        path = path.encode() if type(path) is str else path
        if not callback:
            logging.debug(f"Loading WIMFile from {path}, non-progressive loader.")
            loader = lambda s: _backend.lib.wimlib_open_wim(path, flags, s)
        else:
            logging.debug(f"Loading WIMFile from {path}, progressive loader.")
            @_backend.ffi.callback("enum wimlib_progress_status(enum wimlib_progress_msg, union wimlib_progress_info*, void*)")
            def __wrapper(progress_msg, progress_info, user_context):
                user_context = _backend.ffi.from_handle(user_context)
                # TODO: Cast progress_info to a pythonic object instead of C union.
                ret_val = callback(progress_msg, progress_info, user_context)
                return ret_val if ret_val is not None else 0
            context = _backend.ffi.new_handle(context)
            loader = lambda s: _backend.lib.wimlib_open_wim_with_progress(path,
                                                     flags, s, __wrapper, context)
        return WIMFile(loader, path, flags)


    def write(self, fd=None, image=ALL_IMAGES, write_flags=None, threads=4):
        if self.path is None:
            raise WIMError("self.path is None, no file to write to.")

        path = _backend.ffi.new("char[]", self.path)
        write_flags = write_flags if write_flags is not None else 0

        if not self._has_baking_file:
            if fd:
                ret = _backend.lib.wimlib_write_to_fd(
                    self._wim_struct, fd.fileno(), image, write_flags, threads)
            else:
                ret = _backend.lib.wimlib_write(
                    self._wim_struct, path.encode(), image, write_flags, threads)
        else:
            ret = _backend.lib.wimlib_overwrite(
                self._wim_struct, write_flags, threads)

        if ret:
            raise WIMError(ret)


    def reference_resources(self, resource, ref_flags, wim_flags):
        """ Reference sources in other WIMs """
        # Filter resources into groups of files and wim objects
        wim_resources = list(filter(lambda res: isinstance(
            res, WIMFile), self.reference_resources))
        file_resources = list(
            filter(lambda res: isinstance(res, str), self.reference_resources))
        self._reference_resource_files(file_resources, ref_flags, wim_flags)
        self._reference_resources(wim_resources)


    def _reference_resources(self, resource_wims):
        # TODO: Implement this?
        raise NotImplementedError()


    def _reference_resource_files(self, resource_paths, ref_flags, wim_flags):
        # TODO: Implement this?
        raise NotImplementedError()


    @property
    def info(self):
        """ Get information about this WIM """
        info = _backend.ffi.new("struct wimlib_wim_info*")

        if (ret := _backend.lib.wimlib_get_wim_info(self._wim_struct, info)):
            raise WIMError(ret)

        return wimlib.info.Info(info)


    @info.setter
    def info(self, value):
        if not isinstance(value, wimlib.info.Info):
            raise ValueError(
                "Error: property info sould be set to type of Info().")
        ret = _backend.lib.wimlib_set_wim_info(
            self._wim_struct, value._info_struct)
        if ret:
            raise WIMError(ret)


    @property
    def xml_data(self, buffer_size=4096):
        """ Get the XML data from the file """
        out_buffer = _backend.ffi.new("void**")
        out_size = _backend.ffi.new("size_t*")
        ret = _backend.lib.wimlib_get_xml_data(
            self._wim_struct, out_buffer, out_size)
        if ret:
            raise WIMError(ret)
        return bytes(_backend.ffi.buffer(_backend.ffi.cast("char*", out_buffer[0]), out_size[0]))


    def extract_xml_data(self, file):
        raise NotImplementedError("Error: wimlib FILE* argument not supported.")


    def register_progress_funcion(self, callback, context):
        # TODO: Something?
        pass


    def verify(self, flags):
        ret = _backend.lib.wimlib_verify_wim(self._wim_struct, flags)
        if ret:
            raise WIMError(ret)

    def split(self, swm_name, part_size, flags):
        ret = _backend.lib.wimlib_split(self._wim_struct, swm_name, part_size, write_flags)
        if ret:
            raise WIMError(ret)


    def set_output_pack_compression_type(self, compression_type):
        ret = _backend.lib.wimlib_set_output_pack_compression_type(self._wim_struct, compression_type)
        if ret:
            raise WIMError(ret)


    def set_output_pack_chunk_size(self, chunk_size):
        ret = _backend.lib.wimlib_set_output_pack_chunk_size(self, chunk_size)
        if ret:
            raise WIMError(ret)


    def set_output_compression_type(self, compression_type):
        ret = _backend.lib.wimlib_set_output_compression_type(self._wim_struct, compression_type)
        if ret:
            raise WIMError(ret)


    def set_output_chunk_size(self, chunk_size):
        ret = _backend.lib.wimlib_set_output_chunk_size(self._wim_struct, chunk_size)
        if ret:
            raise WIMError(ret)


    def iterate_lookup_table(self, flags, callback, context):
        @_backend.ffi.callback("int(const struct wimlib_resource_entry, void*)")
        def __wrapper(resource_entry, user_context):
            user_context = _backend.ffi.from_handle(user_context)
            # TODO: Cast resource_entry to a pythonic object instead of C struct.
            ret_val = callback(resource_entry, user_context)
            return ret_val if ret_val is not None else 0
        context = _backend.ffi.new_handle(context)
        ret = _backend.lib.wimlib_iterate_lookup_table(self._wim_struct, flags, callback_wrapper, context)
        if ret:
            raise WIMError(ret)
            
