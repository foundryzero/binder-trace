import argparse
import json
import logging
import traceback
from os import path

import binder_trace.constants
import binder_trace.loggers
import binder_trace.structure
import binder_trace.tui.interface
from binder_trace import loggers
from binder_trace.generator import FridaInjector

loggers.configure()

log = logging.getLogger(loggers.LOG)


def main():
    parser = argparse.ArgumentParser(
        description="Connects to a Android device with a "
        "frida server running and extracts and "
        "parses the data passed across the Binder "
        "interface."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-p", "--pid", dest="pid", type=int, help="the process id to attach to")
    group.add_argument("-n", "--name", dest="name", type=str, help="the process name to attach to")

    parser.add_argument(
        "-d",
        "--device",
        dest="device",
        type=str,
        help="the android device to attach to",
    )

    struct_group = parser.add_mutually_exclusive_group(required=True)

    struct_group.add_argument(
        "-a",
        "--android-version",
        const="all",
        nargs="?",
        choices=["9", "10", "11", "12", "13"],
        default="13",
        help="Android version structs to use",
    )

    struct_group.add_argument(
        "-s",
        "--structpath",
        help="provides the path to the root of the struct directory. e.g. ../structs/android11",
    )

    parser.add_argument("-c", "--config", help="Path to a binder-trace configuration file")
    args = parser.parse_args()

    structs_dict = {
        "9": "android9",
        "10": "android10",
        "11": "android11",
        "12": "android-12.1.0_r27",
        "13": "android13.0.0-r_49",
    }

    base_dir = path.dirname(path.abspath(__file__))

    struct_path = args.structpath or path.join(base_dir, "structs", structs_dict[args.android_version])

    if not path.exists(struct_path):
        print(f'Struct path "{struct_path}" not found.')
        exit(-1)

    config = None
    injector = None
    try:
        injector = FridaInjector(
            args.pid or args.name,
            struct_path,
            int(args.android_version),
            args.device,
        )
        injector.start()
        binder_trace.tui.interface.start_ui(injector.block_queue, injector.pause_unpause, config, args.config)
        log.info("UI Stopped")
    except Exception as err:
        print(err)
        log.error(f"Error occurred in UI: {err}")
        log.error(traceback.format_exc())
    except KeyboardInterrupt:
        pass
    finally:
        if injector:
            injector.stop()
        log.info("Injector stopped.")


if __name__ == "__main__":
    main()
