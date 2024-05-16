"""Frida Injector for remote Android process."""

import logging
import os
import queue
import threading
import traceback
from typing import Any

import frida
from frida import ProcessNotFoundError

from binder_trace import loggers, parsing
from binder_trace.parsedParcel import Block
from binder_trace.structure import StructureStore

log = logging.getLogger(loggers.LOG)
parsing_log = logging.getLogger(loggers.PARSING_LOG)


class FridaInjector:
    """FridaInjector class for injecting our hook into binder."""

    SCRIPT_FILE = os.path.join(os.path.dirname(__file__), "js/interceptbinder.js")

    def __init__(
        self, process_identifier: str, struct_path: str, android_version: int, device_name: str, spawn_process: bool
    ):
        """Initialise FridaInjector.

        :param process_identifier: Process identifier
        :param struct_path: Path to struct files
        :param android_version: Version of android
        :param device_name: Device or emulator name
        :param spawn_process: Should process be spawned?
        """
        self.process_identifier = process_identifier
        self.android_version = android_version
        self._stop_event = threading.Event()
        self._handler_process = None
        self.spawn_process = spawn_process

        self.message_queue: queue.Queue[str] = queue.Queue()
        self.block_queue: queue.Queue[Block] = queue.Queue()

        self.struct_store = StructureStore(struct_path)

        self.recording = True

        with open(os.path.normpath(self.SCRIPT_FILE)) as f:
            self.script_content = f.read()

        if device_name:
            self.device = frida.get_device(device_name)
        else:
            self.device = frida.get_usb_device()

    def start(self):
        """Start the injector."""
        # Frida can behave weirdly if you attempt to spawn a package which is already running
        # so first try to attach, and if it fails and spawn option supplied, spawn it.
        try:
            self.session = self.device.attach(self.process_identifier)
        except ProcessNotFoundError:
            if self.spawn_process:
                self.device.spawn([self.process_identifier])
                self.start()
                return
            else:
                raise

        self.script = self.session.create_script(self.script_content)
        self.script.on("message", self._message_handler)

        log.info("Starting injector")
        self._handler_process = threading.Thread(target=self._start)
        self._handler_process.start()
        log.info("Injector started")

    def stop(self):
        """Stop the injector."""
        log.info("Stopping injector")

        self._stop_event.set()
        if self._handler_process:
            self._handler_process.join()

        log.info("Injector stopped")

    def pause_unpause(self):
        """Pause or unpause capture of binder messages from the injector."""
        self.recording = not self.recording
        return self.recording

    def _message_handler(self, message: Any, data: Any) -> None:
        try:
            if self.recording:
                block = parsing.on_message(self.struct_store, message, data, self.android_version)
                if block:
                    self.block_queue.put(block)
        except Exception as e:
            parsing_log.error(e)
            parsing_log.error(traceback.format_exc())

    def _start(self) -> None:
        self.script.load()

        if self.spawn_process:
            self.device.resume(self.process_identifier)

        self.script.exports.init(None, {"connected": "true", "version": self.android_version})
        self.message_queue.put("Connected")

        log.info("Injector waiting for stop event")
        self._stop_event.wait()
        log.info("Stop event received")

        # script.unload()
        self.session.detach()
        log.info("Script unloaded")
