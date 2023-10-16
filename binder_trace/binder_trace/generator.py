import logging
import os
import queue
import threading
import traceback

import frida

from binder_trace import loggers, parsing
from binder_trace.structure import StructureStore

log = logging.getLogger(loggers.LOG)
parsing_log = logging.getLogger(loggers.PARSING_LOG)


class FridaInjector:
    SCRIPT_FILE = os.path.join(os.path.dirname(__file__), "js/interceptbinder.js")

    def __init__(self, process_identifier, struct_path, android_version, device_name):
        self.process_identifier = process_identifier
        self.android_version = android_version
        self._stop_event = threading.Event()
        self._handler_process = None

        self.message_queue = queue.Queue()
        self.block_queue = queue.Queue()

        self.struct_store = StructureStore(struct_path)

        self.recording = True

        with open(os.path.normpath(self.SCRIPT_FILE)) as f:
            self.script_content = f.read()

        if device_name:
            self.device = frida.get_device(device_name)
        else:
            self.device = frida.get_usb_device()

    def start(self):
        self.session = self.device.attach(self.process_identifier)
        self.script = self.session.create_script(self.script_content)
        self.script.on("message", self._message_handler)

        log.info("Starting injector")
        self._handler_process = threading.Thread(target=self._start)
        self._handler_process.start()
        log.info("Injector started")

    def stop(self):
        log.info("Stopping injector")

        self._stop_event.set()
        if self._handler_process:
            self._handler_process.join()

        log.info("Injector stopped")

    def pause_unpause(self):
        self.recording = not self.recording
        return self.recording

    def _message_handler(self, message, data):
        try:
            if self.recording:
                block = parsing.on_message(self.struct_store, message, data, self.android_version)
                if block:
                    self.block_queue.put(block)
        except Exception as e:
            parsing_log.error(e)
            parsing_log.error(traceback.format_exc())

    def _start(self):
        self.script.load()

        self.script.exports.init(None, {"connected": "true", "version": self.android_version})
        self.message_queue.put("Connected")

        log.info("Injector waiting for stop event")
        self._stop_event.wait()
        log.info("Stop event received")

        # script.unload()
        self.session.detach()
        log.info("Script unloaded")
