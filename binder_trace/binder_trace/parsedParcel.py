from __future__ import annotations

from asyncore import read
from dataclasses import dataclass
from enum import Enum
from http.client import INSUFFICIENT_STORAGE
from typing import Any, Callable, List, Optional

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


def parse_field(name: str, type, method, parent: Optional[Field] = None) -> Field:
    field = Field(name, [], type, None, parent)
    if parent:
        parent.content.append(field)
    _, position = method(field)
    field.position = position
    return field


@dataclass(eq=True, frozen=True)
class FieldData:
    start: int
    end: int

    def __str__(self) -> str:
        return f"Pos(start={self.start}, end={self.end})"


@dataclass
class Field:
    name: str
    content: list[Field]
    typename: Optional[str] = None
    position: Optional[FieldData] = None
    parent: Optional[Field] = None

    @classmethod
    def empty(cls):
        return cls("", None)

    @classmethod
    def error(cls, err):
        return cls("<failed>", err)

    def walk_back_to(self, name) -> Field | None:
        found_field = next((field for field in reversed(self.content) if field.name == name), None)
        if not found_field and self.parent:
            found_field = self.parent.walk_back_to(name)
        return found_field

    def __str__(self) -> str:
        return self._pretty_str(indent_level=0)

    def _pretty_str(self, indent_level=0):
        indent = indent_level * "  "
        if isinstance(self.content, list):
            content = "".join(["\n" + f._pretty_str(indent_level + 1) for f in self.content])
            content = f"[{content}]"
        else:
            content = str(self.content)
        return f"{indent}Field(name={self.name}, type={self.typename}, position={self.position}, content={content})"


class Direction(Enum):
    IN = 1
    OUT = 2


@dataclass
class Block:
    raw_data: bytes
    interface_name: str
    call_name: str
    code: int
    oneway: bool
    direction: Direction
    root_field: Field
    unsupported_call: bool = False
    errors: Optional[Exception] = None

    def __str__(self):
        return f"Block(interface_name={self.interface_name},callName={self.call_name},fields=\n\t{self.root_field})"

    def __repr__(self) -> str:
        return f"Block(interface_name={self.interface_name},callName={self.call_name},fields=\n{self.root_field})"
