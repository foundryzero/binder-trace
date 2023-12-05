import string
import unittest

from binder_trace.tui.selection import SelectionViewList, View


class TestSelectionViewList(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_init_no_args(self):
        items = SelectionViewList()
        self.assertEqual(0, len(items))
        self.assertEqual(-1, items.selection)

    def test_init_with_initial_list(self):
        items = SelectionViewList(["a", "b", "c"])
        self.assertEqual(3, len(items))
        self.assertEqual(0, items.selection)

    def test_move_selection(self):
        items = SelectionViewList(list(string.ascii_lowercase), max_view_size=10, view_padding=2)

        items.move_selection(1)
        self.assertEqual((1, View(0, 10)), (items.selection, items.view))

        items.move_selection(1)
        self.assertEqual((2, View(0, 10)), (items.selection, items.view))

        items.move_selection(3)
        self.assertEqual((5, View(0, 10)), (items.selection, items.view))

        items.move_selection(3)
        self.assertEqual((8, View(0, 10)), (items.selection, items.view))

        items.move_selection(1)
        self.assertEqual((9, View(1, 11)), (items.selection, items.view))

        items.move_selection(-1)
        self.assertEqual((8, View(1, 11)), (items.selection, items.view))

        items.move_selection(-2)
        self.assertEqual((6, View(1, 11)), (items.selection, items.view))

        items.move_selection(-4)
        self.assertEqual((2, View(0, 10)), (items.selection, items.view))

    def test_move_selection_down_and_back_up(self):
        items = SelectionViewList(list(string.ascii_lowercase), max_view_size=10, view_padding=2)
        for _ in range(len(items)):
            items.move_selection(1)
            print(items.selection, items.view)

        for _ in range(len(items)):
            items.move_selection(-1)
            print(items.selection, items.view)

    # def test_delete_item(self):
    #     items = SelectionViewList(list(string.ascii_lowercase), max_view_size=10, view_padding=2)
    #     items.move_selection(5)
    #     items.move_selection(5)

    #     self.assertEqual((10, View(5, 15)), (items.selection, items.view))

    #     del items[3]
    #     self.assertEqual((9, View(4, 14)), (items.selection, items.view))

    #     del items[6]
    #     self.assertEqual((8, View(4, 14)), (items.selection, items.view))

    #     del items[10]
    #     self.assertEqual((8, View(4, 14)), (items.selection, items.view))

    #     del items[8]
    #     self.assertEqual((8, View(4, 14)), (items.selection, items.view))
    #     items.move_selection(-2)
    #     self.assertEqual((6, View(4, 14)), (items.selection, items.view))
    #     del items[5]
    #     self.assertEqual((6, View(3, 13)), (items.selection, items.view))

    # def test_pop_item(self):
    #     items = SelectionViewList(list(string.ascii_lowercase), max_view_size=10, view_padding=2)
    #     items.move_selection(5)
    #     items.move_selection(5)

    #     self.assertEqual((10, View(5, 15)), (items.selection, items.view))

    #     items.pop(3)
    #     self.assertEqual((9, View(4, 14)), (items.selection, items.view))

    #     items.pop(6)
    #     self.assertEqual((8, View(4, 14)), (items.selection, items.view))

    #     items.pop(10)
    #     self.assertEqual((8, View(4, 14)), (items.selection, items.view))

    # def test_remove_item(self):
    #     items = SelectionViewList(list(string.ascii_lowercase), max_view_size=10, view_padding=2)
    #     items.move_selection(5)
    #     items.move_selection(5)

    #     self.assertEqual((10, View(5, 15)), (items.selection, items.view))

    #     items.remove("c")
    #     self.assertEqual((9, View(4, 15)), (items.selection, items.view))

    def test_append_item(self):
        items = SelectionViewList(list("abc"), max_view_size=10, view_padding=2)
        self.assertEqual((0, View(0, 3)), (items.selection, items.view))
        items.append("d")
        self.assertEqual((0, View(0, 4)), (items.selection, items.view))

    def test_insert_item_into_empty_list(self):
        items = SelectionViewList()
        items.insert(0, "a")
        self.assertEqual((0, View(0, 1)), (items.selection, items.view))

    def test_insert_item_into_small_list(self):
        items = SelectionViewList(list("abcde"), max_view_size=10, view_padding=2)
        items.move_selection(2)
        self.assertEqual((2, View(0, 5)), (items.selection, items.view))
        items.insert(0, "_")
        self.assertEqual((3, View(0, 6)), (items.selection, items.view))
        items.insert(3, "_")
        self.assertEqual((4, View(0, 7)), (items.selection, items.view))
        items.insert(6, "_")
        self.assertEqual((4, View(0, 8)), (items.selection, items.view))

    def test_insert_item_into_list(self):
        items = SelectionViewList(list(string.ascii_lowercase), max_view_size=10, view_padding=2)
        items.move_selection(5)
        items.move_selection(5)
        items.move_selection(5)
        self.assertEqual((15, View(10, 20)), (items.selection, items.view))

        items.insert(1, "_")
        self.assertEqual((16, View(10, 20)), (items.selection, items.view))
        items.insert(16, "_")
        self.assertEqual((17, View(10, 20)), (items.selection, items.view))
        items.insert(19, "_")
        self.assertEqual((17, View(10, 20)), (items.selection, items.view))
