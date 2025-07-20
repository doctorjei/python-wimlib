import logging

from wimlib import _lib, _ffi, WimException
from wimlib.image import ImageCollection
from wimlib.info import WimInfo


#Shorthand names

# Image specificaion consts
NO_IMAGE = 0
ALL_IMAGES = -1


class WimFile(object):
    # Specialized constructor for calling backend functions easily.
    def __init__(self, loader, path="", has_baking_file=False):
        self._has_baking_file = has_baking_file
        self.path = path = str(path)

        if (error := loader(path.encode(), wim_struct := _ffi.new("WIMStruct **"))):
            raise WimException(error)

        self._wim_struct = wim_struct[0]
        self.images = ImageCollection(self)


    def __del__(self):
        _lib.wimlib_free(self._wim_struct)


    @staticmethod
    def new(compression=0):
        loader = lambda p, s: _lib.wimlib_create_new_wim(compression, s)
        return WimFile(loader)


    @staticmethod
    def from_file(path, flags=0, callback=None, context=None):
        if not callback:
            logging.debug(f"Loading WimFile from {path}, non-progressive loader.")
            loader = lambda p, s: _lib.wimlib_open_wim(p, flags, s)
        else:
            logging.debug(f"Loading WimFile from {path}, progressive loader.")
            @_ffi.callback("enum wimlib_progress_status(enum wimlib_progress_msg, union wimlib_progress_info*, void*)")
            def __wrapper(progress_msg, progress_info, user_context):
                user_context = _ffi.from_handle(user_context)
                # TODO: Cast progress_info to a pythonic object instead of C union.
                ret_val = callback(progress_msg, progress_info, user_context)
                return ret_val if ret_val is not None else 0

            loader = lambda p, s: _lib.wimlib_open_wim_with_progress(p, flags,
                                             s, __wrapper, _ffi.new_handle(context))
        return WimFile(loader, path, flags)


    def write(self, fd=None, image=ALL_IMAGES, flags=None, threads=4):
        if not self.path:
            raise WimException("No path / file to write to.")

        path = _ffi.new("char[]", self.path)
        flags = flags if flags is not None else 0

        if not self._has_baking_file:
            if fd:
                ret = _lib.wimlib_write_to_fd(self._wim_struct, fd.fileno(), image, flags, threads)
            else:
                ret = _lib.wimlib_write(self._wim_struct, path, image, flags, threads)
        else:
            ret = _lib.wimlib_overwrite(self._wim_struct, flags, threads)

        if ret:
            raise WimException(ret)


    def reference_resources(self, resource, ref_flags, wim_flags):
        """ Reference sources in other WIMs """
        # Filter resources into groups of files and wim objects
        wim_res = list(filter(lambda res: isinstance(res, WimFile), self.reference_resources))
        file_res = list(filter(lambda res: isinstance(res, str), self.reference_resources))
        self._reference_resource_files(file_res, ref_flags, wim_flags)
        self._reference_resources(wim_res)


    def _reference_resources(self, resource_wims):
        # TODO: Implement this?
        raise NotImplementedError()


    def _reference_resource_files(self, resource_paths, ref_flags, wim_flags):
        # TODO: Implement this?
        raise NotImplementedError()


    def reference_template(self, new_index, template_image, template_wim=None, flags=0):
        """ Declare that newly added image as mostly the same as a prior one -
            i.e., reference an existing template image."""
        if not template_wim and not isinstance(template_image, Image):
            raise ValueError("Error: Image() instance or template_wim required.")

        if isinstance(template_image, Image):
            template_wim = template_image._wim_struct

        if (ret := _lib.wimlib_reference_template_image(self._wim_struct,
                     new_index, template_wim._wim_struct, int(template_image), flags)):
            raise WimException(ret)


    @property
    def info(self):
        """ Get information about this WIM """
        wim_info = _ffi.new("struct wimlib_wim_info*")

        if (ret := _lib.wimlib_get_wim_info(self._wim_struct, wim_info)):
            raise WimException(ret)

        logging.debug(f"Fetched wim_info for {self._wim_struct} from backend.")
        return WimInfo(wim_info)


    @info.setter
    def info(self, value):
        if not isinstance(value, WimInfo):
            raise ValueError("Error: property info sould be set to type of Info().")

        if (ret := _lib.wimlib_set_wim_info(self._wim_struct, value._info_struct)):
            raise WimException(ret)


    @property
    def xml_data(self, buffer_size=4096):
        """ Get the XML data from the file """
        out_buffer = _ffi.new("void**")
        out_size = _ffi.new("size_t*")
        if (ret := _lib.wimlib_get_xml_data(self._wim_struct, out_buffer, out_size)):
            raise WimException(ret)

        return bytes(_ffi.buffer(_ffi.cast("char*", out_buffer[0]), out_size[0]))


    def extract_xml_data(self, file):
        raise NotImplementedError("Error: wimlib FILE* argument not supported.")


    def register_progress_funcion(self, callback, context):
        # TODO: Something?
        pass


    def verify(self, flags):
        if (ret := _lib.wimlib_verify_wim(self._wim_struct, flags)):
            raise WimException(ret)


    def split(self, name, size, flags):
        if (ret := _lib.wimlib_split(self._wim_struct, name, size, flags)):
            raise WimException(ret)


    def set_output_pack_compression_type(self, cmp_type):
        if (ret := _lib.wimlib_set_output_pack_compression_type(self._wim_struct, cmp_type)):
            raise WimException(ret)


    def set_output_pack_chunk_size(self, chunk_size):
        if (ret := _lib.wimlib_set_output_pack_chunk_size(self, chunk_size)):
            raise WimException(ret)


    def set_output_compression_type(self, cmp_type):
        if (ret := _lib.wimlib_set_output_compression_type(self._wim_struct, cmp_type)):
            raise WimException(ret)


    def set_output_chunk_size(self, chunk_size):
        if (ret := _lib.wimlib_set_output_chunk_size(self._wim_struct, chunk_size)):
            raise WimException(ret)


    def iterate_lookup_table(self, flags, callback, context):
        context = _ffi.new_handle(context)

        @_ffi.callback("int(const struct wimlib_resource_entry, void*)")
        def __wrapper(resource_entry, user_context):
            user_context = _ffi.from_handle(user_context)
            # TODO: Cast resource_entry to a pythonic object instead of C struct.
            ret_val = callback(resource_entry, user_context)
            return ret_val if ret_val is not None else 0

        if _lib.wimlib_iterate_lookup_table(self._wim_struct, flags, __wrapper, context):
            raise WimException(ret)
