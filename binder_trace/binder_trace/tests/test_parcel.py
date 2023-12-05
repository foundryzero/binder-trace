# noqa

import struct
import unittest
from unittest.mock import create_autospec

from binder_trace.parcel import ParcelParser
from binder_trace.parsedParcel import Field, FieldData
from binder_trace.parseerror import ParseError
from binder_trace.structure import StructureStore

DEFAULT_TEST_ANDROID_VERSION = 11


class TestParseError(unittest.TestCase):
    """Parcel tests."""

    def test_simple(self) -> None:
        """A simple test of ParseError's initialisation."""
        token = ParseError("err")
        self.assertEqual(token.message, "err")


class ParcelParserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_store = create_autospec(StructureStore)
        self.parent = Field("", [])
        self.maxDiff = None
        if "unittest.util" in __import__("sys").modules:
            # Show full diff in self.assertEqual.
            __import__("sys").modules["unittest.util"]._MAX_LENGTH = 999999999

    def test_read_byte(self):
        parser = ParcelParser(self.mock_store, b"\x41\x00\x00\x00", DEFAULT_TEST_ANDROID_VERSION)

        parser.readByte(self.parent)

        self.assertEqual(0x41, self.parent.content)
        self.assertEqual(4, parser.pos)

    def test_read_int32(self):
        parser = ParcelParser(self.mock_store, b"\x44\x33\x22\x11", DEFAULT_TEST_ANDROID_VERSION)

        parser.readInt32(self.parent)

        self.assertEqual(0x11223344, self.parent.content)
        self.assertEqual(4, parser.pos)

    def test_read_uint32(self):
        parser = ParcelParser(self.mock_store, b"\x44\x33\x22\x11", DEFAULT_TEST_ANDROID_VERSION)

        parser.readUint32(self.parent)

        self.assertEqual(0x11223344, self.parent.content)
        self.assertEqual(4, parser.pos)

    def test_read_int64(self):
        data = struct.pack("<q", 0x1122334455667788)
        parser = ParcelParser(self.mock_store, data, DEFAULT_TEST_ANDROID_VERSION)

        parser.readInt64(self.parent)

        self.assertEqual(0x1122334455667788, self.parent.content)
        self.assertEqual(8, parser.pos)

    def test_read_uint64(self):
        data = struct.pack("<Q", 0x1122334455667788)
        parser = ParcelParser(self.mock_store, data, DEFAULT_TEST_ANDROID_VERSION)

        parser.readUint64(self.parent)

        self.assertEqual(0x1122334455667788, self.parent.content)
        self.assertEqual(8, parser.pos)

    def test_read_int32_vector(self):
        data = struct.pack("<iiiii", 0x4, 0x11111111, 0x22222222, 0x33333333, 0x44444444)
        parser = ParcelParser(self.mock_store, data, DEFAULT_TEST_ANDROID_VERSION)

        parser.readInt32Vector(self.parent)

        subfields = [
            Field(name="length", content=0x4, typename="int32", position=FieldData(start=0, end=4), parent=self.parent),
            Field(
                name="0",
                content=0x11111111,
                typename="int32",
                position=FieldData(start=4, end=8),
                parent=self.parent,
            ),
            Field(
                name="1",
                content=0x22222222,
                typename="int32",
                position=FieldData(start=8, end=12),
                parent=self.parent,
            ),
            Field(
                name="2",
                content=0x33333333,
                typename="int32",
                position=FieldData(start=12, end=16),
                parent=self.parent,
            ),
            Field(
                name="3",
                content=0x44444444,
                typename="int32",
                position=FieldData(start=16, end=20),
                parent=self.parent,
            ),
        ]
        expected = Field("test", subfields, "some-object", FieldData(0, 20), self.parent)
        self.assertEqual(expected.content, self.parent.content)
        self.assertEqual(20, parser.pos)

    def test_read_int64_vector(self):
        data = struct.pack(
            "<iqqqq", 0x4, 0x1111111111111111, 0x2222222222222222, 0x3333333333333333, 0x4444444444444444
        )
        parser = ParcelParser(self.mock_store, data, DEFAULT_TEST_ANDROID_VERSION)

        parser.readInt64Vector(self.parent)

        subfields = [
            Field(name="length", content=0x4, typename="int32", position=FieldData(start=0, end=4), parent=self.parent),
            Field(
                name="0",
                content=0x1111111111111111,
                typename="int64",
                position=FieldData(start=4, end=12),
                parent=self.parent,
            ),
            Field(
                name="1",
                content=0x2222222222222222,
                typename="int64",
                position=FieldData(start=12, end=20),
                parent=self.parent,
            ),
            Field(
                name="2",
                content=0x3333333333333333,
                typename="int64",
                position=FieldData(start=20, end=28),
                parent=self.parent,
            ),
            Field(
                name="3",
                content=0x4444444444444444,
                typename="int64",
                position=FieldData(start=28, end=36),
                parent=self.parent,
            ),
        ]
        expected = Field("test", subfields, "some-object", FieldData(0, 36), self.parent)
        self.assertEqual(expected.content, self.parent.content)
        self.assertEqual(36, parser.pos)

    def test_read_string8_ascii_bound(self):
        data = struct.pack("<i10s", 0xA, b"helloworld")
        parser = ParcelParser(self.mock_store, data, DEFAULT_TEST_ANDROID_VERSION)

        parser.readString8(self.parent)

        expected_content = [
            Field("Length", 10, "uint32", FieldData(0, 4), self.parent),
            Field("Value", "helloworld", "utf-8", FieldData(4, 15), self.parent),
        ]
        length_length, string_length, aligned_null_terminator_length = 4, 10, 2
        expected_position = length_length + string_length + aligned_null_terminator_length
        self.assertEqual(expected_content, self.parent.content)
        self.assertEqual(expected_position, parser.pos)

    def test_read_string8_unbound(self):
        data = struct.pack("<i12s", 0xC, b"\xc2\xb5\xc2\xa5\xc2\xaa\xe0\xaa\xaa\xe0\xaa\xac")
        parser = ParcelParser(self.mock_store, data, DEFAULT_TEST_ANDROID_VERSION)

        parser.readString8(self.parent)

        expected_content = [
            Field("Length", 12, "uint32", FieldData(0, 4), self.parent),
            Field("Value", "µ¥ªપબ", "utf-8", FieldData(4, 17), self.parent),
        ]
        length_length, string_length, aligned_null_terminator_length = 4, 12, 4
        expected_position = length_length + string_length + aligned_null_terminator_length
        print(self.parent.content)
        print(expected_content)
        self.assertEqual(expected_content, self.parent.content)
        self.assertEqual(expected_position, parser.pos)

    def test_read_string16(self):
        data = struct.pack("<i10s", 0x5, b"\xb5\x00\xa5\x00\xaa\x00\xaa\n\xac\n")
        parser = ParcelParser(self.mock_store, data, DEFAULT_TEST_ANDROID_VERSION)

        parser.readString16(self.parent)

        expected_content = [
            Field("Length", 5, "uint32", FieldData(0, 4), self.parent),
            Field("Value", "µ¥ªપબ", "utf_16_le", FieldData(4, 16), self.parent),
        ]
        length_length, string_length, aligned_null_terminator_length = 4, 10, 2
        expected_position = length_length + string_length + aligned_null_terminator_length

        self.assertEqual(expected_content, self.parent.content)
        self.assertEqual(expected_position, parser.pos)

    def test_read_string8_vector(self):
        self.maxDiff = None
        if "unittest.util" in __import__("sys").modules:
            # Show full diff in self.assertEqual.
            __import__("sys").modules["unittest.util"]._MAX_LENGTH = 999999999

        data = struct.pack(
            "<ii4si4si4si4si4s",
            0x5,
            0x2,
            b"he\x00\x00",
            0x2,
            b"ll\x00\x00",
            0x2,
            b"ow\x00\x00",
            0x2,
            b"or\x00\x00",
            0x2,
            b"ld\x00\x00",
        )
        parser = ParcelParser(self.mock_store, data, DEFAULT_TEST_ANDROID_VERSION)

        parser.readString8Vector(self.parent)

        length_field = Field("length", 5, "int32", FieldData(0, 4), self.parent)
        array_field0 = Field("0", [], "string", FieldData(4, 12), self.parent)
        array_field1 = Field("1", [], "string", FieldData(12, 20), self.parent)
        array_field2 = Field("2", [], "string", FieldData(20, 28), self.parent)
        array_field3 = Field("3", [], "string", FieldData(28, 36), self.parent)
        array_field4 = Field("4", [], "string", FieldData(36, 44), self.parent)
        array_field0.content.append(Field("Length", 2, "uint32", FieldData(4, 8), array_field0))
        array_field0.content.append(Field("Value", "he", "utf-8", FieldData(8, 11), array_field0))
        array_field1.content.append(Field("Length", 2, "uint32", FieldData(12, 16), array_field1))
        array_field1.content.append(Field("Value", "ll", "utf-8", FieldData(16, 19), array_field1))
        array_field2.content.append(Field("Length", 2, "uint32", FieldData(20, 24), array_field2))
        array_field2.content.append(Field("Value", "ow", "utf-8", FieldData(24, 27), array_field2))
        array_field3.content.append(Field("Length", 2, "uint32", FieldData(28, 32), array_field3))
        array_field3.content.append(Field("Value", "or", "utf-8", FieldData(32, 35), array_field3))
        array_field4.content.append(Field("Length", 2, "uint32", FieldData(36, 40), array_field4))
        array_field4.content.append(Field("Value", "ld", "utf-8", FieldData(40, 43), array_field4))
        mock_parent = Field("", [length_field, array_field0, array_field1, array_field2, array_field3, array_field4])
        expected_position = 44

        print(self.parent.content[1].content[1].parent == self.parent.content[1])
        print(mock_parent.content[1].content[1].parent == mock_parent.content[1])

        self.assertEqual(mock_parent.content, self.parent.content)
        self.assertEqual(expected_position, parser.pos)

    def test_read_object(self):
        data = struct.pack("iiqq", 0x11223344, 0x22446688, 0x3333333333333333, 0x4444444444444444)
        parser = ParcelParser(self.mock_store, data, DEFAULT_TEST_ANDROID_VERSION)

        parser.readObject(self.parent)

        expected = [
            Field("type", 0x11223344, "int32", FieldData(0, 4), self.parent),
            Field("flags", 0x22446688, "int32", FieldData(4, 8), self.parent),
            Field(
                "binder / handle",
                0x3333333333333333,
                "int64",
                FieldData(8, 16),
                self.parent,
            ),
            Field("cookie", 0x4444444444444444, "int64", FieldData(16, 24), self.parent),
        ]
        self.assertEqual(expected, self.parent.content)
        self.assertEqual(24, parser.pos)

    def test_parse_field_byte(self):
        parser = ParcelParser(self.mock_store, b"\x41\x00\x00\x00", DEFAULT_TEST_ANDROID_VERSION)

        field = parser.parse_field("test", "byte", parser.readByte, self.parent)

        expected = Field("test", 0x41, "byte", FieldData(0, 4), self.parent)
        self.assertEqual(expected, field)

    def test_parse_field_object(self):
        data = struct.pack("iiqq", 0x11223344, 0x22446688, 0x3333333333333333, 0x4444444444444444)
        parser = ParcelParser(self.mock_store, data, DEFAULT_TEST_ANDROID_VERSION)

        field = parser.parse_field("test", "some-object", parser.readObject, self.parent)

        subfields = [
            Field("type", 0x11223344, "int32", FieldData(0, 4), field),
            Field("flags", 0x22446688, "int32", FieldData(4, 8), field),
            Field("binder / handle", 0x3333333333333333, "int64", FieldData(8, 16), field),
            Field("cookie", 0x4444444444444444, "int64", FieldData(16, 24), field),
        ]
        expected = Field("test", subfields, "some-object", FieldData(0, 24), self.parent)
        self.assertEqual(expected, field)
