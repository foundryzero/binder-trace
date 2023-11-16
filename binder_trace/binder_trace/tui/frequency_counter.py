import logging
from bisect import insort_left
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from operator import itemgetter

from binder_trace import loggers
from binder_trace.tui.interface import DisplayTransaction, Filter
from binder_trace.tui.selection import SelectionViewList

# Defining variable to be able to log events
log = logging.getLogger(loggers.LOG)


class FilterType(Enum):
    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"

@dataclass
class FrequencyRecord:
    interface: str
    method: str
    frequency: int
    filter: str
    interface_total: list[int]

    def __hash__(self):
        return hash((self.interface, self.method, self.frequency, self.filter, self.interface_total[0]))    

class FrequencyCounter:
    def __init__(self):
        self.svl = SelectionViewList([], max_view_size=1)
        self.sort_key = self.freq_asc_key

        def empty_total():
            return [0]

        self.interface_totals = defaultdict(empty_total)

    def frequency_record_to_filter(self, record: DisplayTransaction) -> Filter:
        return Filter(
            interface=record.interface,
            method=record.method,
            types="",
            include=False,
        )

    def check_frequency_filters(self, record: DisplayTransaction):
        filters = [
            self.frequency_record_to_filter(record) for record in self.svl if record.filter == FilterType.EXCLUDE
        ]

        return all(filter.passes(record) for filter in filters)

    def toggle_filter(self):
        selection = self.svl.selected()
        new_filter = FilterType.EXCLUDE if selection.filter == FilterType.INCLUDE else FilterType.INCLUDE
        selection.filter = new_filter
        for record in self.svl:
            # If selection is an interface
            if not selection.method:
                if record.interface == selection.interface:
                    record.filter = new_filter
            # If selection is a method
            else:
                if record.interface == selection.interface and record.method == "":
                    record.filter = FilterType.INCLUDE

    def filter_all_out(self, option: bool):
        with self.svl.on_update_event.suspended():
            for filter in self.svl:
                filter.filter = FilterType.EXCLUDE if option else FilterType.INCLUDE

    # Toggles the selction view list to either show asc or desc order based on the frequency
    def toggle_sort(self):
        with self.svl.on_update_event.suspended():
            self.sort_key = self.freq_inv_key if self.sort_key == self.freq_asc_key else self.freq_asc_key
            self.svl.sort(key=self.sort_key)

    def find_index(self, record: tuple) -> int:
        return next(
            filter(
                itemgetter(1),
                enumerate(map(lambda row: (row.interface, row.method) == record, self.svl)),
            ),
            (-1,),
        )[0]

    # Checking if a record needs to be added or updated
    def add(self, record: tuple):
        idx = self.find_index(record)

        if idx != -1:
            self.svl[idx].frequency += 1
        else:
            self.svl.append(
                FrequencyRecord(
                    interface=record[0],
                    method=record[1],
                    frequency=1,
                    filter=FilterType.INCLUDE,
                    interface_total=self.interface_totals[record[0]],
                )
            )
            self.svl.sort(key=self.sort_key)


    # Adding records to the selection view list in sorted order
    def add_record(self, record: tuple):
        with self.svl.on_update_event.suspended():
            with self.svl.on_selection_change.suspended():
                interface_record = (record[0], "")
                self.add(interface_record)
                self.add(record)
                self.interface_totals[record[0]][0] += 1
                self.svl.sort(key=self.sort_key)

    # Key to define how to sort the list in ascending order of the frequency
    def freq_asc_key(self, row: FrequencyRecord):
        return (
            row.interface_total[0] * -1,
            row.interface,
            row.frequency * -1,
            row.method,
        )

    # Key to define how to sort the list in descending order of the frequency
    def freq_inv_key(self, row: FrequencyRecord):
        return (
            row.interface_total[0],
            row.interface,
            0 if not row.method else row.frequency,
            row.method,
        )
