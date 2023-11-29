"""Encapsulation of a Table."""

from typing import Callable, List, Optional, Type, Union

from prompt_toolkit.cache import SimpleCache
from prompt_toolkit.key_binding.key_bindings import KeyBindingsBase

# from prompt_toolkit.widgets.base import Border
from prompt_toolkit.layout.containers import HorizontalAlign, HSplit, VerticalAlign, VSplit, Window
from prompt_toolkit.layout.dimension import AnyDimension
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.dimension import max_layout_dimensions, sum_layout_dimensions, to_dimension
from prompt_toolkit.utils import take_using_weights


class EmptyBorder:
    """Empty Border."""

    HORIZONTAL = ""
    VERTICAL = ""

    TOP_LEFT = ""
    TOP_RIGHT = ""
    BOTTOM_LEFT = ""
    BOTTOM_RIGHT = ""

    LEFT_T = ""
    RIGHT_T = ""
    TOP_T = ""
    BOTTOM_T = ""

    INTERSECT = ""


class SpaceBorder:
    """Box drawing characters (Spaces)."""

    HORIZONTAL = " "
    VERTICAL = " "

    TOP_LEFT = " "
    TOP_RIGHT = " "
    BOTTOM_LEFT = " "
    BOTTOM_RIGHT = " "

    LEFT_T = " "
    RIGHT_T = " "
    TOP_T = " "
    BOTTOM_T = " "

    INTERSECT = " "


class AsciiBorder:
    """Box drawing characters (ASCII)."""

    HORIZONTAL = "-"
    VERTICAL = "|"

    TOP_LEFT = "+"
    TOP_RIGHT = "+"
    BOTTOM_LEFT = "+"
    BOTTOM_RIGHT = "+"

    LEFT_T = "+"
    RIGHT_T = "+"
    TOP_T = "+"
    BOTTOM_T = "+"

    INTERSECT = "+"


class ThinBorder:
    """Box drawing characters (Thin)."""

    HORIZONTAL = "\u2500"
    VERTICAL = "\u2502"

    TOP_LEFT = "\u250c"
    TOP_RIGHT = "\u2510"
    BOTTOM_LEFT = "\u2514"
    BOTTOM_RIGHT = "\u2518"

    LEFT_T = "\u251c"
    RIGHT_T = "\u2524"
    TOP_T = "\u252c"
    BOTTOM_T = "\u2534"

    INTERSECT = "\u253c"


class RoundedBorder(ThinBorder):
    """Box drawing characters (Rounded)."""

    TOP_LEFT = "\u256d"
    TOP_RIGHT = "\u256e"
    BOTTOM_LEFT = "\u2570"
    BOTTOM_RIGHT = "\u256f"


class ThickBorder:
    """Box drawing characters (Thick)."""

    HORIZONTAL = "\u2501"
    VERTICAL = "\u2503"

    TOP_LEFT = "\u250f"
    TOP_RIGHT = "\u2513"
    BOTTOM_LEFT = "\u2517"
    BOTTOM_RIGHT = "\u251b"

    LEFT_T = "\u2523"
    RIGHT_T = "\u252b"
    TOP_T = "\u2533"
    BOTTOM_T = "\u253b"

    INTERSECT = "\u254b"


class DoubleBorder:
    """Box drawing characters (Thin)."""

    HORIZONTAL = "\u2550"
    VERTICAL = "\u2551"

    TOP_LEFT = "\u2554"
    TOP_RIGHT = "\u2557"
    BOTTOM_LEFT = "\u255a"
    BOTTOM_RIGHT = "\u255d"

    LEFT_T = "\u2560"
    RIGHT_T = "\u2563"
    TOP_T = "\u2566"
    BOTTOM_T = "\u2569"

    INTERSECT = "\u256c"


AnyBorderStyle = Union[
    Type[EmptyBorder],
    Type[SpaceBorder],
    Type[AsciiBorder],
    Type[ThinBorder],
    Type[RoundedBorder],
    Type[ThickBorder],
    Type[DoubleBorder],
]


class Merge:
    """Merge cells."""

    def __init__(self, cell, merge=1):
        """Initialise Merge class.

        :param cell: Cell
        :param merge: Cells to merge, defaults to 1
        """
        self.cell = cell
        self.merge = merge

    def __iter__(self):
        """Merge iterator."""
        yield self.cell
        yield self.merge


class Table(HSplit):
    """Table view."""

    def __init__(
        self,
        table,
        borders: AnyBorderStyle = ThinBorder,
        column_width=None,
        column_widths=[],
        window_too_small=None,
        align=VerticalAlign.JUSTIFY,
        padding=0,
        padding_char=None,
        padding_style="",
        width=None,
        height=None,
        z_index=None,
        modal=False,
        key_bindings=None,
        style="",
        selected_style="",
    ):
        """Initialise Table.

        :param table: The table backing the table frame.
        :param borders: Border type, defaults to ThinBorder
        :param column_width: Column width, defaults to None
        :param column_widths: Widths of each column, defaults to []
        :param window_too_small: Flag indicating if the display window is to small for an elements minimum size.
        :param align: How to align the table, defaults to VerticalAlign.JUSTIFY
        :param padding: Padding for the frame, defaults to 0
        :param padding_char: Character to use in padding, defaults to None
        :param padding_style: Style of padding, defaults to ""
        :param width: Table frame width, defaults to None
        :param height: Table frame height, defaults to None
        :param z_index: Z index, defaults to None
        :param modal: Modal, defaults to False
        :param key_bindings: Key bindings for this frame, defaults to None
        :param style: Frame style to use, defaults to ""
        :param selected_style: Current style, defaults to ""
        """
        self.borders = borders
        self.column_width = column_width
        self.column_widths = column_widths
        self.selected_style = selected_style

        # ensure the table is iterable (has rows)
        if not isinstance(table, list):
            table = [table]

        children = [_Row(row=row, table=self, borders=borders, height=1) for row in table]

        super().__init__(
            children=children,
            window_too_small=window_too_small,
            align=align,
            padding=padding,
            padding_char=padding_char,
            padding_style=padding_style,
            width=width,
            height=height,
            z_index=z_index,
            modal=modal,
            key_bindings=key_bindings,
            style=style,
        )
        self.row_cache = SimpleCache(maxsize=30)

    def add_row(self, row, style, cache_id):
        """Add row to table.

        :param row: The row to add
        :param style: Row style
        :param cache_id: Cache lookup id.
        """
        r = self.row_cache.get(cache_id, lambda: _Row(row=row, table=self, borders=self.borders, height=1, style=style))
        self.children.append(r)

    @property
    def columns(self):
        """Get the maximum number of columns."""
        return max(row.raw_columns for row in self.children)

    @property
    def _all_children(self):
        """List of child objects, including padding & borders."""

        def get():
            result = []

            # Padding top.
            if self.align in (VerticalAlign.CENTER, VerticalAlign.BOTTOM):
                result.append(Window(width=D(preferred=0)))

            # Border top is first inserted in children loop.

            # The children with padding.
            for child in self.children:
                result.append(child)

            # Padding bottom.
            if self.align in (VerticalAlign.CENTER, VerticalAlign.TOP):
                result.append(Window(width=D(preferred=0)))

            return result

        return self._children_cache.get(tuple(self.children), get)

    def preferred_dimensions(self, width):
        """Preferred dimensions for the table frame.

        :param width: The width of the table
        :yield: Preferred table dimensions.
        """
        dimensions = [[]] * self.columns
        for row in self.children:
            assert isinstance(row, _Row)
            j = 0
            for cell in row.children:
                assert isinstance(cell, _Cell)

                if cell.merge != 1:
                    dimensions[j].append(cell.preferred_width(width))

                j += cell.merge

        for i, c in enumerate(dimensions):
            yield D.exact(1)

            try:
                w = self.column_widths[i]
            except IndexError:
                w = self.column_width
            if w is None:  # fitted
                yield max_layout_dimensions(c)
            else:  # fixed or weighted
                yield to_dimension(w)
        yield D.exact(1)


class _VerticalBorder(Window):
    def __init__(self, borders):
        super().__init__(width=1, char=borders.VERTICAL)


class _BaseRow(VSplit):
    @property
    def columns(self):
        return self.table.columns

    def _divide_widths(self, width):
        """
        Return the widths for all columns.

        Or None when there is not enough space.
        """
        children = self._all_children

        if not children:
            return []

        # Calculate widths.
        dimensions = list(self.table.preferred_dimensions(width))
        preferred_dimensions = [d.preferred for d in dimensions]

        # Sum dimensions
        sum_dimensions = sum_layout_dimensions(dimensions)

        # If there is not enough space for both.
        # Don't do anything.
        if sum_dimensions.min > width:
            return

        # Find optimal sizes. (Start with minimal size, increase until we cover
        # the whole width.)
        sizes = [d.min for d in dimensions]

        child_generator = take_using_weights(items=list(range(len(dimensions))), weights=[d.weight for d in dimensions])

        i = next(child_generator)

        # Increase until we meet at least the 'preferred' size.
        preferred_stop = min(width, sum_dimensions.preferred)

        while sum(sizes) < preferred_stop:
            if sizes[i] < preferred_dimensions[i]:
                sizes[i] += 1
            i = next(child_generator)

        # Increase until we use all the available space.
        max_dimensions = [d.max for d in dimensions]
        max_stop = min(width, sum_dimensions.max)

        while sum(sizes) < max_stop:
            if sizes[i] < max_dimensions[i]:
                sizes[i] += 1
            i = next(child_generator)

        # perform merges if necessary
        if len(children) != len(sizes):
            tmp = []
            i = 0
            for c in children:
                if isinstance(c, _Cell):
                    inc = (c.merge * 2) - 1
                    tmp.append(sum(sizes[i : i + inc]))
                else:
                    inc = 1
                    tmp.append(sizes[i])
                i += inc
            sizes = tmp

        return sizes


class _Row(_BaseRow):
    def __init__(
        self,
        row,
        table: Table,
        borders: AnyBorderStyle,
        window_too_small: Optional[bool] = None,
        align: HorizontalAlign = HorizontalAlign.JUSTIFY,
        padding: AnyDimension = D.exact(0),
        padding_char: Optional[str] = None,
        padding_style: str = "",
        width: AnyDimension = None,
        height: AnyDimension = None,
        z_index: Optional[int] = None,
        modal: bool = False,
        key_bindings: Optional[KeyBindingsBase] = None,
        style: Union[str, Callable[[], str]] = "",
    ):
        self.table = table
        self.borders = borders

        # ensure the row is iterable (has cells)
        if not isinstance(row, list):
            row = [row]
        children = []
        for c in row:
            m = 1
            if isinstance(c, Merge):
                c, m = c
            elif isinstance(c, dict):
                c, m = Merge(**c)
            children.append(_Cell(cell=c, table=table, row=self, merge=m))

        super().__init__(
            children=children,
            window_too_small=window_too_small,
            align=align,
            padding=padding,
            padding_char=padding_char,
            padding_style=padding_style,
            width=width,
            height=height,
            z_index=z_index,
            modal=modal,
            key_bindings=key_bindings,
            style=style,
        )

    @property
    def raw_columns(self):
        return sum(cell.merge for cell in self.children)

    @property
    def _all_children(self):
        """List of child objects, including padding & borders."""

        def get():
            result = []

            # Padding left.
            if self.align in (HorizontalAlign.CENTER, HorizontalAlign.RIGHT):
                result.append(Window(width=D(preferred=0)))

            # Border left is first inserted in children loop.

            # The children with padding.
            c = 0
            for child in self.children:
                result.append(_VerticalBorder(borders=self.borders))
                result.append(child)
                c += child.merge
            # Fill in any missing columns
            for _ in range(self.columns - c):
                result.append(_VerticalBorder(borders=self.borders))
                result.append(_Cell(cell=None, table=self.table, row=self))

            # Border right.
            result.append(_VerticalBorder(borders=self.borders))

            # Padding right.
            if self.align in (HorizontalAlign.CENTER, HorizontalAlign.LEFT):
                result.append(Window(width=D(preferred=0)))

            return result

        return self._children_cache.get(tuple(self.children), get)


class _Cell(HSplit):
    def __init__(
        self,
        cell,
        table,
        row,
        merge=1,
        padding: AnyDimension = 0,
        char=None,
        padding_left: AnyDimension = None,
        padding_right: AnyDimension = None,
        padding_top: AnyDimension = None,
        padding_bottom: AnyDimension = None,
        window_too_small=None,
        width: AnyDimension = None,
        height: AnyDimension = None,
        z_index: Optional[int] = None,
        modal=False,
        key_bindings: Optional[KeyBindingsBase] = None,
        style="",
    ):
        self.table = table
        self.row = row
        self.merge = merge

        if padding is None:
            padding = D(preferred=0)

        def get(value: AnyDimension) -> Dimension:
            if value is None:
                value = padding
            return to_dimension(value)

        self.padding_left = get(padding_left)
        self.padding_right = get(padding_right)
        self.padding_top = get(padding_top)
        self.padding_bottom = get(padding_bottom)

        children: List[Union[Window, VSplit]] = []
        children.append(Window(width=self.padding_left, char=char))
        if cell:
            children.append(cell)
        children.append(Window(width=self.padding_right, char=char))

        children = [
            Window(height=self.padding_top, char=char),
            VSplit(children),
            Window(height=self.padding_bottom, char=char),
        ]

        super().__init__(
            children=children,
            window_too_small=window_too_small,
            width=width,
            height=height,
            z_index=z_index,
            modal=modal,
            key_bindings=key_bindings,
            style=style,
        )
