"""Parsing functionality."""

import functools
import logging
import traceback
from typing import Any, Dict, Optional

import binder_trace.overrides
from binder_trace import loggers
from binder_trace.parcel import ParcelParser
from binder_trace.parsedParcel import Block, Direction, Field, FieldData
from binder_trace.parseerror import ParseError
from binder_trace.structure import StructureStore

log = logging.getLogger(loggers.LOG)
parsing_log = logging.getLogger(loggers.PARSING_LOG)


"""
Stores the current parcel number that has been recieved. Must be global, since on_message is called by frida directly
and cannot store state.
"""
frameNumber = -1


def on_message(struct_store: StructureStore, message: Any, data: Any, android_version: int) -> Optional[Block]:
    """
    Decode and parses a binder parcel, and writes it to the block_queue, archiver, and logger if present.

    Args:
        message: A dict containing a 'payload' key, which is a string of the form:
            TRANSACT <code> or
            REPLY <code> <interface_descriptor>

            eg: TRANSACT 47
            eg: REPLY 47 android.os.storage.IStorageManager

        data: A bytes[] object containing the data of the intercepted parcel
    """
    if data is None:
        # TODO: Work out why data is sometimes None here.
        return None

    # TODO: make the parser a class so it can keep this in state
    global frameNumber
    frameNumber += 1

    block_metadata = message["payload"]

    parcel = ParcelParser(struct_store, data, android_version)

    block = None
    parsing_log.debug(str(message))

    if block_metadata["type"] == "TRANSACT":
        # If the message is a transaction it will have an interfaceToken header before the data
        block = on_message_in(struct_store, parcel, block_metadata["code"])

    elif block_metadata["type"] == "REPLY":  # in this case the message will be of the form "REPLY <code> <descriptor>"
        block = on_message_out(struct_store, parcel, block_metadata["code"], block_metadata["descriptor"])

    else:
        log.warn(f"Unknown message block type: {block_metadata['type']}")

    return block


def on_message_out(struct_store: StructureStore, parcel: ParcelParser, code: Any, descriptor: Any) -> Optional[Block]:
    """Attempt to parse a reply parcel with the specified code and interface.

    Args:
        p: The parcel to read the data from
        code: The method code in the interface that this parcel is a return from
        descriptor: The interface, as a string, that this parcel was returned from
    """
    try:
        interface = struct_store.get_interface(descriptor)
        call = get_call(interface, code)
        root_field = Field("", [])
        block = Block(
            parcel.data,
            interface["full_name"],
            call["name"],
            code,
            oneway=False,
            direction=Direction.OUT,
            root_field=root_field,
        )

        try:
            read_interface_output(call, parcel, root_field)
        except FileNotFoundError as e:
            block.errors = e
            block.unsupported_call = True
        except Exception as e:
            block.errors = e
            parsing_log.error(e)
            parsing_log.error(traceback.format_exc())

    # TODO: change this for a better exception
    except FileNotFoundError as e:  # Thrown if we try to read an interface that doesn't have an associated struct file
        # TODO: Work out what to do with unhandled blocks
        block = None
        parsing_log.debug(e)
        parsing_log.debug(traceback.format_exc())

        # block = Block(descriptor, str(code), p, frameNumber, code=code, noAidl=True)

    return block


def on_message_in(struct_store: StructureStore, parcel: ParcelParser, code: Any) -> Optional[Block]:
    """Attempt to parse a call parcel with the specified code.

    Args:
        parcel: The parcel to read the data from
        code: The method code in the interface that this parcel is a return from
    """
    # TODO: Work out what these short parcels are
    if len(parcel.data) <= 4:
        log.debug("Unexpectedly short parcel detected")
        return None

    try:
        token = parcel.parse_field("interface-token", "", parcel.read_interface_token)
        descriptor = next(field.content[1].content for field in token.content if field.name == "Token Descriptor")
        interface = struct_store.get_interface(descriptor)

        call = get_call(interface, code)
        root_field = Field("", [token])
        block = Block(
            parcel.data,
            interface["full_name"],
            call["name"],
            code,
            call["oneWay"],
            direction=Direction.IN,
            root_field=root_field,
        )

        try:
            read_interface_input(call, parcel, root_field)
        except FileNotFoundError as e:
            block.errors = e
            block.unsupported_call = True
        except Exception as e:
            block.errors = e
            parsing_log.error(e)
            parsing_log.error(traceback.format_exc())

    except FileNotFoundError as e:
        # TODO: This probably means the type isn't supported. Create a block with "unsupported_call" set
        block = None
        parsing_log.debug(e)
        parsing_log.debug(traceback.format_exc())
    return block


def parse_parcel_type(definition: Dict[Any, Any], parcel: ParcelParser, parent: Field) -> Optional[Field]:
    """Parse the type of a given parcel.

    :param definition: Definition of the parcel
    :param parcel: The parcel
    :param parent: The parcel's parent
    :return: The pracel type
    """
    parcelType = definition["__parcelType"]

    # TODO: Update structure so this is a named field we don't have to search for.
    name = next(n for n in definition.keys() if n == "__return" or not n.startswith("__"))

    if definition[name] == "readParcelable":
        if binder_trace.overrides.parcelableHasOverride(parcelType):
            binder_trace.overrides.parcelableOverride(parcel, parcelType, name, parent)
            return None
        retval = parcel.parse_field(name, "", functools.partial(parcel.readParcelable, parcelType), parent)
    else:
        retval = parcel.parse_field(name, "", functools.partial(parcel.readParcelableVector, parcelType), parent)
    return retval


def parse_generic_type(definition: Dict[Any, Any], parcel: ParcelParser, parent: Field):
    """Parse the generic type from a parcel.

    :param definition: _description_
    :param parcel: The parcel
    :param parent: The parcel's parent
    """
    type = definition["__type"]

    # TODO: Update structure so this is a named field we don't have to search for.
    name = next(n for n in definition.keys() if n == "__return" or not n.startswith("__"))
    parcel.parse_field(name, f"List<{type}>", parcel.readList, parent)


def parse_value_from_definition(definition: Dict[Any, Any], parcel: ParcelParser, parent: Field):
    """Parse a value from a parcel.

    :param definition: The definition of the parcel
    :param parcel: The parse to parse it from
    :param parent: The parcel's parent
    :return: The parsed value
    """
    # This is expected to be a simple value definition like:
    #   {"effectType": "readInt32"},
    #   {"volume": "readFloat"}
    assert len(definition) == 1, f"Only one key expected: {definition}"

    name, read_func = next(iter(definition.items()))
    reader = getattr(parcel, read_func)
    return parcel.parse_field(name, "", reader, parent)


def parse_conditional(definition: Dict[Any, Any], parcel: ParcelParser, parent: Field):
    """Parse a conditional out of a parcel.

    :param definition: The parcel definition
    :param parcel: The parcel to parse
    :param parent: The parcel's parent
    :raises ParseError: raised if a backreference cannot be found.
    :return: The conditional
    """
    conditional = definition["__conditional"]
    backreference = definition["__backreference"]

    # Search through the already parsed names backwards for the backreference.
    # If we find it then check its associated value. If its falsey then fields in the
    # condition block won't be present.
    backreference_field = parent.walk_back_to(backreference)

    if not backreference_field:
        raise ParseError("Failed to find back reference")

    if not backreference_field.content:
        return Field.empty()

    # Read the conditional block
    conditional_field = Field(f"Conditional On '{backreference}'", [], "", None, parent)
    parent.content.append(conditional_field)
    startPos = parcel.pos
    for var in conditional:
        parse(var, parcel, conditional_field)

    conditional_field.position = FieldData(startPos, parcel.pos)


def parse_repeated_value(definition: Dict[Any, Any], parcel: ParcelParser, parent_field: Field):
    """Parse out a list of values.

    :param definition: The parcel definition
    :param parcel: The parcel to parse
    :param parent_field: The parcel's parent
    :raises ParseError: raised on parsing error
    """
    repeated = definition["__repeated"]
    backreference = definition["__backreference"]

    backreference_field = parent_field.walk_back_to(backreference)

    if not backreference_field:
        raise ParseError("Failed to find back reference")

    if not backreference_field.content:
        raise ParseError(f"Repeated values count field '{backreference}' not found.")

    if not isinstance(backreference_field.content, (str, int)):
        raise ParseError(f"Unexpected repeated value count type: {type(backreference_field.content)}")

    repeat_count = int(backreference_field.content)

    for _ in range(repeat_count):
        for var in repeated:
            parse(var, parcel, parent_field)


def parse(definition: Dict[Any, Any], parcel: ParcelParser, parent: Field) -> None:
    """
    Parse a single element of a parcel.

    Args:
        definition: A dict containing the definition of the value to parse.
        parcel: The parcel to read data from.
        parsedParcel: The current parsedParcel that we are writing to
        parent: The direct parent of parsedParcel, if it exists

    Returns: (name, retval, err) where name is the name of the parsed value, retval is the parsed data, and err is a
        boolean which is true if an error that renders the rest of the parsing process meaningless has occurred, like
        an unknown parcelable being encountered.

    """
    names = definition.keys()

    if "__parcelType" in names:  # If a parceltype is present, then it's either a Parcelable or a ParcelableVector
        parse_parcel_type(definition, parcel, parent)
    elif "__type" in names:  # If a generic type is present, then the value is as List<__type>
        parse_generic_type(definition, parcel, parent)
    # If a repeated is present, then the definitions inside should be parsed in a loop on the value of backreference.
    elif "__repeated" in names:
        parse_repeated_value(definition, parcel, parent)

    # If a conditional is present, then the definitions contained inside the conditional should only be parsed if
    # the value from the backreference is truthy
    elif "__conditional" in names:
        parse_conditional(definition, parcel, parent)
    else:
        parse_value_from_definition(definition, parcel, parent)


def get_call(struct: Any, code: Any) -> Any:
    """Get the call element of a parcelable."""
    call = next((c for c in struct["calls"] if c["code"] == code), None)
    if not call:
        raise Exception(f"Call {code} not found in interface {struct['full_name']}")
    return call


def read_interface_output(call, parcel: ParcelParser, parent: Field) -> None:
    """
    Read and parse the output of an IPC call from a REPLY parcel.

    Args:
        call: The structure object for the call.
        parcel: The read data, in parcel form.

    Throws:
        Exception if the code does not exist in the interface structure.
    """
    for outvar in call["out"]:
        parse(outvar, parcel, parent)

        # TODO: Find a better way to check the exception code.
        if ("readException" in list(outvar.values())) and parent.content[-1].content[0].content:
            # If an exception occurred then no further parsing should occur
            break


def read_interface_input(call, parcel: ParcelParser, parent: Field) -> None:
    """
    Read and parse the input to an IPC call from a TRANSACTION parcel.

    Args:
        call: The structure object for the call.
        parcel: The read data, in parcel form.
    Throws:
        Exception if the code does not exist in the interface structure.
    """
    for invar in call["in"]:
        parse(invar, parcel, parent)
