from dataclasses import dataclass, field
import itertools
from select import select
from typing import List, Tuple, Optional
from binder_trace.parsedParcel import Field, FieldData
from ranges import Range, RangeDict
from prompt_toolkit.formatted_text import FormattedText

@dataclass
class IndentedField:
    level: int
    field: Field


def _flatten_into(field: Field, dest: list[IndentedField], level=0):
    dest.append(IndentedField(level, field))

    if isinstance(field.content, list):
        for sub_field in field.content:
            _flatten_into(sub_field, dest, level=level+1)

def _to_indented(indented: IndentedField):
    indent = "  " * indented.level
    value = indented.field.content if not isinstance(indented.field.content, list) else indented.field.typename
    return f"{indent}{indented.field.name}: {value}"

def flatten_fields(field: Field) -> List[Field]:
    flat_fields = []
    _flatten_into(field, flat_fields)
    return flat_fields

def to_hierarchy(field: Field):
    flat_fields = []
    _flatten_into(field, flat_fields)

    return "\n".join(_to_indented(f) for f in flat_fields)


@dataclass
class StyleRun:
    style: str
    hex_fragments: list[str] = field(default_factory=list)
    asci_fragments: list[str] = field(default_factory=list)

    def hex(self):
        return (self.style, "".join(self.hex_fragments))

    def asci(self):
        return (self.style, "".join(self.asci_fragments))

def to_hexdump(buf: bytes, default_style: str, selections: List[Tuple[FieldData, str]], offset=0) -> FormattedText:
    # Map each byte to its class, then collapse consecutive strings of same type
    selection_style_map = RangeDict({Range(s.start, s.end): style for s, style in selections})

    current: Optional[StyleRun] = None
    line_numbers: list[tuple[str,str]] = []
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

        spacing = '  ' if i % 8 == 0 and i % 16 != 0 else ' '

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
