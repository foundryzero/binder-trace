"""Android Binder Parcel type structure classes."""

import functools
import json
import os
from typing import Any

import binder_trace.override_IBulkCursor
import binder_trace.override_IContentProvider
import binder_trace.overrides


class StructureStore:
    """A class to encapsulate the structure store."""

    def __init__(self, path: str):
        """Initialise the structure store."""
        self.struct_path_root = path

    @functools.cache
    def get_interface(self, package_name: str) -> Any:
        """
        Get a structure file for an interface.

        Attempts to find the structure file for a specific interface. Functionally the same as get_struct, but includes
        a check that the found file is actually an interface, since interface files and parcelable files have different
        structures.
        Args:
            package_name: The fully qualified name of the interface to load, as a string

        Throws:
            Exception if the loaded structure file is valid, but not an interface.
            FileNotFoundError if the structure file does not exist.
            JSONDecodeError if the loaded structure file is not valid.

        Returns: The structure file as a JSON object

        """
        # Two special cases, since they're not in AIDL. TODO this is a really bad way of doing it but i don't really
        # have time for anything better. A better solution would be looking for classes that implement IInterface and
        # parsing their onTransact and transact methods, but this is going to have similar if not more complexity to the
        # Parcelable parser :(.
        if package_name == "android.content.IContentProvider":
            return binder_trace.override_IContentProvider.getIContentProviderInterface()
        if package_name == "android.content.IBulkCursor":
            return binder_trace.override_IBulkCursor.getIBulkCursorInterface()

        # Attempt to open the struct file for the package name
        with open(
            os.path.normpath(os.path.join(self.struct_path_root, (package_name.replace(".", "/") + ".struct")))
        ) as f:
            struct = json.load(f)
            # Refuse to read the struct if it's not an interface
            if struct["type"] != "Interface":
                raise Exception("Expected interface for " + package_name + ", recieved " + struct["type"])

            return struct

    @functools.cache
    def get_struct(self, struct_name: str) -> Any:
        """Get a struct for a parcelable.

        Attempts to find the structure file for a specific parcelable. Functionally the same as getInterface, but
        includes a check that the found file is actually a parcelable, since interface files and parcelable files have
        different structures.

        Args:
            struct_name: The fully qualified name of the parcelable to load, as a string

        Throws:
            Exception if the loaded structure file is valid, but not a parcelable.
            FileNotFoundError if the structure file does not exist.
            JSONDecodeError if the loaded structure file is not valid.

        Returns: The structure file as a JSON object
        """
        struct_path = os.path.normpath(os.path.join(self.struct_path_root, struct_name.replace(".", "/") + ".struct"))

        if not os.path.exists(struct_path):
            # TODO: Check if this is actually working. It feels like we should be able to sort this upfront.
            struct_path = os.path.join(self.struct_path_root, "$".join(struct_name.rsplit(".", 1)) + ".struct")
            struct_path = os.path.normpath(struct_path)

        # TODO: remove duplication with function above.
        with open(struct_path) as f:
            struct = json.load(f)
            # Refuse to read the struct if it's not an interface
            if struct["type"] != "Parcelable":
                raise Exception("Expected parcelable for " + struct_name + ", recieved " + struct["type"])

            return struct
