"""Encapsulate a binder parcel which has been parsed."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, Union

# def parse_field(name: str, read_type: str|Callable, parent: Field|None = None):
#     if isinstance(read_type, str):
#         # Get function for name
#     elif isinstance(read_type, Callable):
#         # Get name for function


#     field = Field(name, [], type, None, parent)
#     if parent:
#         parent.content.append(field)
#     _, position = method(field)
#     field.position = position
#     return field


def parse_field(name: str, type: str, method: Callable[[Field], Any], parent: Optional[Field] = None) -> Field:
    """Parse a field from a parcel.

    :param name: Name of the field
    :param type: Type of the field
    :param method: Method to parse the field
    :param parent: Parent parcel, defaults to None
    :return: The parsed field
    """
    field = Field(name, [], type, None, parent)
    if parent:
        parent.content.append(field)
    _, position = method(field)
    field.position = position
    return field


@dataclass(eq=True, frozen=True)
class FieldData:
    """Field data encaptulation."""

    start: int
    end: int

    def __str__(self) -> str:
        """Generate string representation of field data."""
        return f"Pos(start={self.start}, end={self.end})"


@dataclass
class Field:
    """Field dataclass."""

    name: str
    content: Union[list[Field], str]
    typename: Optional[str] = None
    position: Optional[FieldData] = None
    parent: Optional[Field] = None

    @classmethod
    def empty(cls):
        """Check if field is empty."""
        return cls("", None)

    @classmethod
    def error(cls, err):
        """Error field."""
        return cls("<failed>", err)

    def walk_back_to(self, name: str) -> Field | str | None:
        """Search through the already parsed names backwards for a given field.

        :param name: name to search for
        :return: The field, if found.
        """
        found_field: Optional[Union[Field, str]] = next(
            (field for field in reversed(self.content) if field.name == name), None
        )
        if not found_field and self.parent:
            found_field = self.parent.walk_back_to(name)
        return found_field

    def __str__(self) -> str:
        """Generate string representation of the field."""
        return self._pretty_str(indent_level=0)

    def _pretty_str(self, indent_level: int = 0) -> str:
        indent = indent_level * "  "
        if isinstance(self.content, list):
            content = "".join(["\n" + f._pretty_str(indent_level + 1) for f in self.content])
            content = f"[{content}]"
        else:
            content = str(self.content)
        return f"{indent}Field(name={self.name}, type={self.typename}, position={self.position}, content={content})"

    def __eq__(self, other) -> bool:
        """Equality builtin override.

        :param other: Other object to compare against
        :return: True if objects are equal, False otherwise
        """
        result = False
        if isinstance(other, type(self)):
            if (
                self.name == other.name
                and self.content == other.content
                and self.typename == other.typename
                and self.position == other.position
            ):
                result = True
        return result


class Direction(Enum):
    """Direction enum."""

    IN = 1
    OUT = 2


@dataclass
class Block:
    """Block dataclass."""

    raw_data: bytes
    interface_name: str
    call_name: str
    code: int
    oneway: bool
    direction: Direction
    root_field: Field
    unsupported_call: bool = False
    errors: Optional[Exception] = None

    def __str__(self) -> str:
        """Generate string representation of block."""
        return f"Block(interface_name={self.interface_name},callName={self.call_name},fields=\n\t{self.root_field})"

    def __repr__(self) -> str:
        """Represent block."""
        return f"Block(interface_name={self.interface_name},callName={self.call_name},fields=\n{self.root_field})"
