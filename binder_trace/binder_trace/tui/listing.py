import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from prompt_toolkit.formatted_text import HTML, FormattedText
from ranges import Range, RangeDict

from binder_trace import loggers
from binder_trace.parsedParcel import Field, FieldData

log = logging.getLogger(loggers.LOG)


@dataclass
class IndentedField:
    level: int
    field: Field


class DisplayField:
    def __init__(self, field) -> None:
        self.field = field

    # Returns display string format
    def display(self, selected=False, indent=0) -> str:
        value = (
            self.field.content
            if not isinstance(self.field.content, list)
            else self.field.typename
        )

        return f"{indent*' '}{self.field.name}: {value}"

    # Returns hexdump positions
    def position(self):
        return [(self.field.position, "class:hexdump.selected")]

    # Says which children to be shown on new lines
    def children(self):
        return self.field.content if isinstance(self.field.content, list) else []


class ErrorDisplayField(DisplayField):
    def __init__(self, field) -> None:
        super().__init__(field)


class StringDisplayField(DisplayField):
    def __init__(self, field) -> None:
        super().__init__(field)
        self.is_list = isinstance(self.field.content, list) and len(self.field.content) == 2

    # Returns display string format
    def display(self, selected=False, indent=0) -> str:
        if self.is_list:
            if selected:
                return HTML(
                    f"{indent*' '}{self.field.name}: String<hexdump.string_length> ({self.field.content[0].content})</hexdump.string_length><hexdump.string_value> {self.field.content[1].content}</hexdump.string_value>"
                )
            else:
                log.debug(self.field)
                return f"{indent*' '}{self.field.name}: String ({self.field.content[0].content}) {self.field.content[1].content}"
        return f"{indent*' '}{self.field.name}: String ({self.field.content})"

    # Returns hexdump positions
    def position(self):
        if self.is_list:
            return [
                (self.field.content[0].position, "class:hexdump.string_length"),
                (self.field.content[1].position, "class:hexdump.string_value"),
            ]
        return [(self.field.position, "class:hexdump.default")]

    # Says which children to be shown on new lines
    def children(self):
        return []


"""
Converts the Field class into a DisplayField type class to return values such as string format to display, 
positions for hexdump and a choice of what children to show
"""


class FieldFactory:
    DisplayClass = [
        (lambda f: f.typename == "error", ErrorDisplayField),
        (lambda f: f.typename == "string", StringDisplayField),
        (lambda f: True, DisplayField),
    ]

    # Checks which type of DisplayField class is to be used
    def get_display_class(self, field: Field):
        for check, display_class in self.DisplayClass:
            if check(field):
                return display_class(field)
        return DisplayField(field)

    # Finds all the children (content) of a field
    def traverse(self, field: Field, level=0) -> list[DisplayField]:
        display_field = self.get_display_class(field)
        ret = [IndentedField(level, display_field)]

        for child in display_field.children():
            ret += self.traverse(child, level=level + 1)
        return ret


@dataclass
class StyleRun:
    style: str
    hex_fragments: list[str] = field(default_factory=list)
    asci_fragments: list[str] = field(default_factory=list)

    def hex(self):
        return (self.style, "".join(self.hex_fragments))

    def asci(self):
        return (self.style, "".join(self.asci_fragments))


def to_hexdump(
    buf: bytes, default_style: str, selections: List[Tuple[FieldData, str]], offset=0
) -> FormattedText:
    # Map each byte to its class, then collapse consecutive strings of same type
    selection_style_map = RangeDict(
        {Range(s.start, s.end): style for s, style in selections}
    )

    current: Optional[StyleRun] = None
    line_numbers: list[tuple[str, str]] = []
    lines: list[list[StyleRun]] = []
    line: list[StyleRun] = []

    for i, val in enumerate(buf[offset:], offset):
        if i % 16 == 0:
            line_numbers.append((default_style, "{:04x}  ".format(i)))
            if line:
                lines.append(line)
                line = []
            current = None

        style = selection_style_map.get(i, default=default_style)

        spacing = "  " if i % 8 == 0 and i % 16 != 0 else " "

        if not current:
            line.append(StyleRun(default_style, [spacing]))
            current = StyleRun(style)
            line.append(current)
        elif current.style != style:
            line.append(StyleRun(default_style, [spacing]))

            # The style has changed, so save what we've got and start a new run
            current = StyleRun(style)
            line.append(current)
        else:
            current.hex_fragments.append(spacing)

        current.hex_fragments.append(f"{val:02x}")
        current.asci_fragments.append(chr(val) if 32 <= val < 127 else ".")

    if line:
        lines.append(line)

    formatted_dump = FormattedText()
    for line_number, line in zip(line_numbers, lines):
        formatted_dump.append(line_number)

        for fragment in line:
            formatted_dump.append(fragment.hex())

        # We might need to pad the last line of hex
        hex_length = sum([len(fragment.hex()[1]) for fragment in line])
        formatted_dump.append((default_style, " " * (49 - hex_length)))

        formatted_dump.append((default_style, "  "))
        for fragment in line:
            formatted_dump.append(fragment.asci())

        formatted_dump.append((default_style, "\n"))
    return formatted_dump
