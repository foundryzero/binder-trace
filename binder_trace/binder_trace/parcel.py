"""Parcel parser."""

from __future__ import annotations

import functools
import logging
import struct
from typing import TYPE_CHECKING, Any, Callable, Optional

from binder_trace import constants, loggers

# All the functions here need to be camelCase because they need to match the ones on the Java side to be matched with
# getattr. Ideally the structures would contain tags that mapped to function names rather than actual function names.
from binder_trace.parsedParcel import Field, FieldData
from binder_trace.parseerror import ParseError

if TYPE_CHECKING:
    from binder_trace.structure import StructureStore

parsing_log = logging.getLogger(loggers.PARSING_LOG)
log = logging.getLogger(loggers.LOG)


class ParcelParser:
    """A parser capable of reading data types that make up a parcel from a buffer."""

    def __init__(self, struct_store: StructureStore, data: Any, android_version: int):
        """Create ParcelParser.

        :param struct_store: Structure store
        :param data: Parcel data
        :param android_version: Android version
        """
        self.struct_store = struct_store
        self.data = data
        self.pos = 0
        self.android_version = android_version

    def parse_field(
        self,
        name: str,
        type_name: str,
        read_func: Callable[[Field], Any],
        parent: Optional[Field] = None,
    ) -> Field:
        """Parse a field.

        :param name: Field name
        :param type_name: Field type
        :param read_func: Parsing function for field
        :param parent: field parent, defaults to None
        :return: Parsed field
        """
        field = Field(name, [], type_name, None, parent)

        if parent:
            parent.content.append(field)

        start = self.pos
        read_func(field)
        end = self.pos

        field.position = FieldData(start, end)
        return field

    def add(self, i: int) -> None:
        """Move the current read offset.

        Note that no checks are made to prevent moving past the end or before the start of the buffer, although all of
        the 'struct' functions check anyway.

        Args:
            i: The amount to move by. May be negative

        Returns: None
        """
        self.pos += i

    def align4(self) -> None:
        """Align the current position with a 4-byte boundary."""
        currentIndex = self.pos % 4
        if currentIndex != 0:
            self.add(4 - currentIndex)

    def align8(self) -> None:
        """Align the current position with a 8-byte boundary."""
        currentIndex = self.pos % 8
        if currentIndex != 0:
            self.add(8 - currentIndex)

    def _read_unaligned_byte(self) -> int:
        b = struct.unpack_from("<B", self.data, self.pos)
        return int(b[0])

    # Bytes are given 4 bytes of space by default (unless they're in a vector)
    def readByte(self, parent: Field) -> None:
        """Read a byte from a field.

        :param parent: parent field
        """
        b = self._read_unaligned_byte()
        self.add(1)
        self.align4()
        parent.content = b

    def readBytes(self, length: int, parent: Field) -> None:
        """Read several bytes from a field.

        :param length: Number of bytes to read
        :param parent: _description_
        """
        buffer = self._readBytes(length)
        parent.content = buffer

    def _readBytes(self, length: int) -> bytes:
        self._bounds_check(length)

        buffer: bytes = self.data[self.pos : self.pos + length]
        self.add(length)
        return buffer

    def readByteUnaligned(self, parent: Field) -> None:
        """Read an unaligned byte.

        :param parent: parent field
        """
        parent.content = self._read_unaligned_byte()
        self.add(1)

    def readDouble(self, parent: Field) -> None:
        """Read a double from a field.

        :param parent: parent field
        """
        b = struct.unpack_from("<d", self.data, self.pos)
        self.add(8)
        parent.content = b[0]

    def readFloat(self, parent: Field) -> None:
        """Read a float from a field.

        :param parent: parent field
        """
        b = struct.unpack_from("<f", self.data, self.pos)
        self.add(4)
        parent.content = b[0]

    def readInt32(self, parent: Field) -> None:
        """Read an Int32 from a field.

        :param parent: parent field
        """
        b = struct.unpack_from("<i", self.data, self.pos)
        self.add(4)
        parent.content = b[0]

    def readUint32(self, parent: Field) -> None:
        """Read an UInt32 from a field.

        :param parent: parent field
        """
        parent.content = self._read_uint32()

    def _read_uint32(self) -> int:
        b = struct.unpack_from("<I", self.data, self.pos)
        self.add(4)
        return b[0]

    def readInt64(self, parent: Field) -> None:
        """Read an Int64 from a field.

        :param parent: parent field
        """
        b = struct.unpack_from("<q", self.data, self.pos)
        self.add(8)
        parent.content = b[0]

    def readUint64(self, parent: Field) -> None:
        """Read an UInt64 from a field.

        :param parent: parent field
        """
        b = struct.unpack_from("<Q", self.data, self.pos)
        self.add(8)
        parent.content = b[0]

    def readChar(self, parent: Field) -> None:
        """Read a char from a field.

        :param parent: parent field
        """
        b = self.data[self.pos : self.pos + 4].decode("utf_16_le")
        self.add(4)
        parent.content = b

    def readCString8(self, parent: Field) -> None:
        """Read a UTF8 C string from a field.

        :param parent: parent field
        """
        s = b""
        while True:
            next_char = struct.unpack_from("<c", self.data, self.pos)
            self.add(1)
            s += b"".join(next_char)
            if next_char == (b"\x00",):
                break
        self.align4()
        parent.content = s.decode("utf_8")

    def _bounds_check(self, length: int) -> None:
        if self.pos + length > len(self.data):
            raise ParseError(f"Runaway string started at {self.pos:#x}, length {length}")

    def _read_string(self, encoding: str, char_size: int, parent: Field) -> None:
        # Strings have a length field and null terminated (the null terminator is not included in the length)
        # self.parse_field("Length", "uint32", parent)
        length_field = self.parse_field("Length", "uint32", self.readInt32, parent)

        if not isinstance(length_field.content, int):
            raise ParseError("Expected integer field")

        length = length_field.content

        if parent.content != -1:
            start = self.pos
            s = self._readBytes(length * char_size)
            self.add(1 * char_size)  # Null terminator
            end = self.pos
            self.align4()

            parent.content.append(
                Field(
                    "Value",
                    s.decode(encoding, errors="replace"),
                    encoding,
                    FieldData(start, end),
                    parent,
                )
            )

    def readString16(self, parent: Field) -> None:
        """Read a UTF16 string from a field.

        :param parent: parent field
        """
        self._read_string("utf_16_le", 2, parent)

    def readString8(self, parent: Field) -> None:
        """Read a UTF8 string from a field.

        :param parent: parent field
        """
        self._read_string("utf-8", 1, parent)

    def read_interface_token(self, parent: Field) -> None:
        """Read an interface token from a field.

        :param parent: parent field
        """
        self.parse_field("Strict Mode Policy", "uint32", self.readUint32, parent)
        if self.android_version >= 11:
            self.parse_field("Work Source UID", "uint32", self.readUint32, parent)
            self.parse_field("Version Header", "uint32", self.readUint32, parent)
        elif self.android_version == 10:
            self.parse_field("Work Source UID", "uint32", self.readUint32, parent)
        self.parse_field("Token Descriptor", "string", self.readString16, parent)
        self.align4()

    def read_app_op_exception_header(self, parent: Field) -> None:
        """Read an app op exception header from a field.

        :param parent: parent field
        """
        # TODO: For now, I'm just ignoring the data here, exceptions across binder are rare
        # and I've never actually seen one of these appops things
        self.parse_field("tag", "string", self.readString16, parent)
        self.parse_field("raw0", "int64", self.readInt64, parent)
        self.parse_field("tag", "int64", self.readInt64, parent)

    def read_app_op_exception(self, parent: Field) -> None:
        """Read an app op exception from a field.

        :param parent: parent field
        """
        self.parse_field("numAppOps", "int32", self.readInt32, parent)

        if not isinstance(parent.content[-1].content, int):
            raise ParseError("Expected int32 field")

        num_app_ops = parent.content[-1].content

        for i in range(num_app_ops):
            self.parse_field(str(i), "", self.read_app_op_exception_header, parent)

    def readException(self, parent: Field) -> None:
        """Read an exception from a field.

        :param parent: parent field
        """
        self.parse_field("code", "int32", self.readInt32, parent)

        if not isinstance(parent.content[-1].content, int):
            raise ParseError("Expected int32 field")

        code = parent.content[-1].content

        # TODO: We need to put this description somewhere. Maybe an ExceptionField or a description property?
        # exception_names = {
        #     constants.EX_SECURITY: "Security Exception",
        #     constants.EX_BAD_PARCELABLE: "Bad Parcelable Exception",
        #     constants.EX_ILLEGAL_ARGUMENT: "Illegal Argument Exception",
        #     constants.EX_NULL_POINTER: "Null Pointer Exception",
        #     constants.EX_ILLEGAL_STATE: "Illegal State Exception",
        #     constants.EX_NETWORK_MAIN_THREAD: "Network on Main Thread Exception",
        #     constants.EX_UNSUPPORTED_OPERATION: "Unsupported Operation Exception",
        #     constants.EX_HAS_NOTED_APPOPS_REPLY_HEADER: "AppOps Exception",
        #     constants.EX_HAS_STRICTMODE_REPLY_HEADER: "Exception With Strict Mdoe Reply Header",
        #     constants.EX_SERVICE_SPECIFIC: "Exception Service Specific Exception Code",
        # }

        # type_description = exception_names.get(code, "Unknown Exception")
        # code_field.name = f"{type_description} ({code:#x})"

        if code == constants.EX_HAS_NOTED_APPOPS_REPLY_HEADER:
            self.parse_field(
                "App Ops Reply Header",
                "EX_HAS_NOTED_APPOPS_REPLY_HEADER",
                self.read_app_op_exception,
                parent,
            )
            self.parse_field("", "Exception", self.readException, parent)
        elif code == constants.EX_HAS_STRICTMODE_REPLY_HEADER:
            self.parse_field("Header Length", "int32", self.readInt32, parent)
            self.parse_field("Header Bytes", "byte[]", self.readBytes, parent)
            # TODO: Support for this type isn't full implemented yet
        elif code != 0:
            self.parse_field("Message", "string", self.readString16, parent)
            self.parse_field("Remote Stack Size", "uint32", self.readUint32, parent)

            if not isinstance(parent.content[-1].content, int):
                raise ParseError("Expected uint32 field")

            stack_size_field = parent.content[-1].content

            if stack_size_field > 0:
                self.parse_field("Remote Stack", "string", self.readString16, parent)

            if code == constants.EX_SERVICE_SPECIFIC:
                self.parse_field("Exception Code", "uint32", self.readUint32, parent)

    def readBool(self, parent: Field) -> None:
        """Read a bool from a field.

        :param parent: parent field
        """
        parent.content = self._read_uint32()

    def readBlob(self, length, parent: Field) -> None:
        """Read a blob from a field.

        :param parent: parent field
        """
        self.parse_field("blob-type", "int32", self.readInt32, parent)

        if not isinstance(parent.content[-1].content, int):
            raise ParseError("Expected int32 field")

        type_field = parent.content[-1].content

        if type_field == constants.BlobType.BLOB_INPLACE:
            self.parse_field(
                "Blob Bytes",
                "byte[]",
                functools.partial(self.readBytes, length),
                parent,
            )
        else:
            # The blob is stored in ASHMEM, which we can't (currently) read, so for now just return the fd number
            self.parse_field(
                "ASHMEM File Descriptor",
                "file-descriptor",
                self.readFileDescriptor,
                parent,
            )

    # Some parcelables read from java code, which I'm calling 'dynamic', have the type encoded in a header directly
    # Additionally, there is no null check on the parcelable itself
    def readDynamicParcelable(self, parent: Field) -> None:
        """Read and parse a dynamic parcelable.

        A dynamic parcelable is sometimes created in android java code. It has a String16 header that contains the
        type of the parcelable, followed by the normal parcelable data. Often these have no null check, but this is
        handled in the struct conditional file anyway.
        """
        type_name = self.parse_field("parcelable-type", "", self.readString16, parent)

        parsing_log.debug(f"Reading dynamic parcelable of type {type_name.content}")
        if type_name.content[0].content != -1:
            self.readParcelable(type_name.content[1].content, parent)
        else:
            parsing_log.info("Dynamic Parcelable type name not found")
            # TODO: Ensure this is definitely not a case for an exception
            # raise ParseError("Dynamic Parcelable type name not found")

    def _read_parcelable(self, struct, parent: Field) -> None:
        """
        Read and parses a parcelable object from a parcel.

        Args:
            struct: The structure object of the parcelable object to read
            parcel: The parcel to read from.
        """
        if struct["type"] != "Parcelable":
            raise ParseError(f"{struct['name']} is not a Parcelable")

        if struct["full_name"] == "android.content.pm.ApplicationInfo":
            # TODO: Comment below says its off by a byte but then adds 4.
            self.add(4)  # I have zero clue why, but ApplicationInfo s are offset by a byte. Why?

        # TODO: This is a hack. Sort out the dependencies
        from binder_trace.parsing import parse

        for var in struct["components"]:
            parse(var, self, parent)

    def readParcelable(self, parcelableName, parent: Field) -> None:
        """Read and parses a normal parcelable.

        Most of the parcel parsing logic is in structure.read_parcelable.
        This only exists to open the structure file if it's needed and handle dynamic parcelables.

        Args:
            parcelableName: The type of the parcelable to read, or "__dynamic" if the parcelable is dynamic.
        """
        if parcelableName == "__dynamic":
            # This will in turn pass back to this function with the correct name
            self.readDynamicParcelable(parent)

        import binder_trace.overrides

        if binder_trace.overrides.parcelableHasOverride(parcelableName):
            binder_trace.overrides.parcelableOverride(self, parcelableName, "", parent)

        # TODO: Why is read_parcelable in structure rathr than in parcel?
        struct_definition = self.struct_store.get_struct(parcelableName)
        self._read_parcelable(struct_definition, parent)

    def readParcelableVector(self, parcelableName, parent: Field) -> None:
        """
        Read and parse a vector of parcelables.

        These are each individually null-checked, and the vector itself is prepended by a length field.
        Args:
            parcelableName: The type of the parcelable to read (__dynamic vectors are not supported)
            nullcheck: True if there's a null-check on each element of the vector, False otherwise
                        (generated struct files won't use nullcheck=False, only manual overrides will)
        """
        size_field = self.parse_field("length", "int32", self.readInt32, parent)

        if not isinstance(size_field.content, int):
            raise ParseError("Expected integer length field")

        for i in range(size_field.content):
            # fields.append(self.parse_field(str(i), type_name, reader))
            null_check_field = self.parse_field("nullcheck", "uint32", self.readUint32, parent)
            if not null_check_field.content:
                # TODO: Do we need to output a field here as a placeholder?
                continue

            self.parse_field(
                str(i),
                "",
                functools.partial(self.readParcelable, parcelableName),
                parent,
            )

    def readParcelableVectorWithoutNullChecks(self, parcelableName, parent) -> None:
        """Read a vector of parcelables.

        :param parcelableName: The name of the parcelable
        :param parent: parent field
        """
        self._read_vector("Parcelable", functools.partial(self.readParcelable, parcelableName), parent)

    def readBoolVector(self, parent: Field) -> None:
        """Read a vector of bools.

        :param parent: parent field
        """
        self._read_vector("bool", self.readBool, parent)

    def readByteVector(self, parent: Field) -> None:
        """Read a vector of bytes.

        :param parent: parent field
        """
        self._read_vector("byte", self.readByteUnaligned, parent)
        self.align4()

    def readString16Vector(self, parent: Field) -> None:
        """Read a vector of utf16 strings.

        :param parent: parent field
        """
        self._read_vector("string", self.readString16, parent)

    def readString8Vector(self, parent: Field) -> None:
        """Read a vector of utf8 strings.

        :param parent: parent field
        """
        self._read_vector("string", self.readString8, parent)

    def readInt32Vector(self, parent: Field) -> None:
        """Read a vector of int32s.

        :param parent: parent field
        """
        self._read_vector("int32", self.readInt32, parent)

    def readInt64Vector(self, parent: Field) -> None:
        """Read a vector of int64s.

        :param parent: parent field
        """
        self._read_vector("int64", self.readInt64, parent)

    def readCharVector(self, parent: Field) -> None:
        """Read a vector of chars.

        :param parent: parent field
        """
        self._read_vector("char", self.readChar, parent)

    def readFloatVector(self, parent: Field) -> None:
        """Read a vector of floats.

        :param parent: parent field
        """
        self._read_vector("float", self.readFloat, parent)

    def readDoubleVector(self, parent: Field) -> None:
        """Read a vector of doubles.

        :param parent: parent field
        """
        self._read_vector("double", self.readDouble, parent)

    def _read_vector(self, type_name, reader, parent: Field) -> None:
        size_field = self.parse_field("length", "int32", self.readInt32, parent)

        if not isinstance(size_field.content, int):
            raise ParseError("Expected integer length field")

        for i in range(size_field.content):
            self.parse_field(str(i), type_name, reader, parent)

    def readStrongBinder(self, parent: Field) -> None:
        """Read a strong binder message.

        :param parent: parent field
        """
        self.parse_field("type", "uint32", self.readUint32, parent)
        self.parse_field("flags", "uint32", self.readUint32, parent)
        self.parse_field("handle/ptr", "uint64", self.readUint64, parent)
        self.parse_field("cookie", "uint64", self.readUint64, parent)

        if self.android_version > 9:
            self.parse_field("status", "uint32", self.readUint32, parent)

    def readValue(self, parent: Field) -> None:
        """Read a value from a field.

        :param parent: parent field
        """
        # TODO: Work out how these fields should be represented
        type_field = self.parse_field("value-type", "int32", self.readInt32, parent)
        read_func = self._get_value_function(type_field.content)
        self.parse_field("", type_field, read_func, parent)

    def _get_value_function(self, value_type) -> Callable[[Field], None]:
        """
        Read a generic value of some type. The type is indicated by an uint32 code before the value itself.

        Returns: The read value.
        """
        read_function_lookup = {
            constants.VAL_NULL: lambda f: (Field.empty(), None),
            constants.VAL_STRING: self.readString16,
            constants.VAL_INTEGER: self.readInt32,
            constants.VAL_MAP: self.readArrayMap,
            constants.VAL_PARCELABLE: self.readDynamicParcelable,
            constants.VAL_SHORT: self.readInt32,
            constants.VAL_LONG: self.readInt64,
            constants.VAL_FLOAT: self.readFloat,
            constants.VAL_DOUBLE: self.readDouble,
            constants.VAL_BOOLEAN: self.readBool,
            constants.VAL_CHARSEQUENCE: self.readCharSequence,
            constants.VAL_LIST: self.readList,
            constants.VAL_BOOLEANARRAY: self.readBoolVector,
            constants.VAL_BYTEARRAY: self.readByteVector,
            constants.VAL_STRINGARRAY: self.readString16Vector,
            constants.VAL_IBINDER: self.readStrongBinder,
            constants.VAL_INTARRAY: self.readInt32Vector,
            constants.VAL_LONGARRAY: self.readInt64Vector,
            constants.VAL_BYTE: self.readByte,
            # TODO: Is VAL_PARCELABLEARRAY just not supported yet?
            constants.VAL_PARCELABLEARRAY: lambda f: (Field.empty(), None),
            constants.VAL_SPARSEARRAY: self.readSparseArray,
            constants.VAL_BUNDLE: self.readBundle,
            constants.VAL_PERSISTABLEBUNDLE: self.readBundle,
            constants.VAL_SIZE: self.readSize,
            constants.VAL_SIZEF: self.readFloatSize,
            constants.VAL_DOUBLEARRAY: self.readDoubleVector,
            constants.VAL_CHAR: self.readChar,
            constants.VAL_SHORTARRAY: self.readInt32Vector,
            constants.VAL_CHARARRAY: self.readCharVector,
            constants.VAL_FLOATARRAY: self.readFloatVector,
        }

        if value_type not in read_function_lookup:
            parsing_log.warning(f"Unsupported value type '{value_type:#x}'")

        return read_function_lookup.get(value_type, lambda f: (Field.empty(), None))

    def readSize(self, parent: Field) -> None:
        """Read a size from a message.

        :param parent: parent field
        """
        self.parse_field("width", "int32", self.readInt32, parent)
        self.parse_field("height", "int32", self.readInt32, parent)

    def readFloatSize(self, parent: Field) -> None:
        """Read a float size from a message.

        :param parent: parent field
        """
        self.parse_field("width", "float", self.readFloat, parent)
        self.parse_field("height", "float", self.readFloat, parent)

    def readList(self, parent: Field) -> None:
        """Read a list from a message.

        :param parent: parent field
        """
        size_field = self.parse_field("size", "int32", self.readInt32, parent)

        if not isinstance(size_field.content, int):
            raise ParseError("Expected integer size field")

        for i in range(0, size_field.content):
            self.parse_field(str(i), "", self.readValue, parent)

    def readMap(self, parent: Field) -> None:
        """Read a map from a message.

        :param parent: parent field
        """
        self._read_array_map(parent)

    def readBundle(self, parent: Field) -> None:
        """Read a bundle from a message.

        :param parent: parent field
        """
        size_field = self.parse_field("length", "int32", self.readInt32, parent)

        if not isinstance(size_field.content, int):
            raise ParseError("Expected integer size field")

        if size_field.content > 0:
            magic_field = self.parse_field("magic", "int32", self.readInt32, parent)

            if magic_field.content not in [
                constants.BUNDLE_MAGIC,
                constants.BUNDLE_MAGIC_NATIVE,
            ]:
                raise ParseError(f"Error: bad magic number for bundle: {magic_field.content:#x}")

            bundle_type = "Native Bundle" if magic_field.content == constants.BUNDLE_MAGIC_NATIVE else "Java Bundle"
            self.parse_field(bundle_type, "ArrayMap", self.readArrayMap, parent)

    def readArraySet(self, parent: Field) -> None:
        """Read an array set from a message.

        :param parent: parent field
        """
        size_field = self.parse_field("length", "int32", self.readInt32, parent)

        if not isinstance(size_field.content, int):
            raise ParseError("Expected integer size field")

        for i in range(0, size_field.content):
            self.parse_field("value", "", self.readValue, parent)

    def readArrayMap(self, parent) -> None:
        """Read an array map from a message.

        :param parent: parent field
        """
        self._read_array_map(parent)

    def _read_array_map(self, parent: Field) -> None:
        size_field = self.parse_field("size", "int32", self.readInt32, parent)

        if not isinstance(size_field.content, int):
            raise ParseError("Expected integer length field")

        for i in range(0, size_field.content):
            self.parse_field("key", "string", self.readString16, parent)
            self.parse_field("value", "", self.readValue, parent)

    def readSparseArray(self, parent: Field) -> None:
        """Read a sparse array from a message.

        :param parent: parent field
        """
        size_field = self.parse_field("size", "int32", self.readInt32, parent)

        if not isinstance(size_field.content, int):
            raise ParseError("Expected integer size field")

        for _ in range(0, size_field.content):
            self.parse_field("index", "int32", self.readInt32, parent)
            self.parse_field("value", "", self.readValue, parent)

    def readFileDescriptor(self, parent: Field) -> None:
        """Read a file descriptor from a message.

        :param parent: parent field
        """
        # This is ignoring the use case of binder across a network
        return self._read_object(parent)

    def readObject(self, parent: Field) -> None:
        """Read an object from a message.

        :param parent: parent field
        """
        self._read_object(parent)

    def _read_object(self, parent: Field) -> None:
        self.parse_field("type", "int32", self.readInt32, parent)
        self.parse_field("flags", "int32", self.readInt32, parent)
        self.parse_field("binder / handle", "int64", self.readInt64, parent)
        self.parse_field("cookie", "int64", self.readInt64, parent)

    def readCharSequence(self, parent: Field) -> None:
        """Read a char sequence from a message.

        :param parent: parent field
        """
        self.readParcelable("android.content.pm.TextUtils", parent)


class InterfaceToken:
    """Interface Token."""

    def __init__(self):
        """Initialise interface token."""
        self.strict_mode_policy = None
        self.work_source_uid = None
        self.version_header = None
        self.descriptor = None

    def __str__(self):
        """Return string representation."""
        return self.descriptor
