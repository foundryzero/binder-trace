import unittest
from unittest.mock import create_autospec, patch

import frida
from frida import ProcessNotFoundError

from binder_trace.generator import FridaInjector


class FridaInjectorTest(unittest.TestCase):
    def mock_get_device(self, id: str):
        return create_autospec(frida.core.Device)

    @patch("binder_trace.generator.frida")
    def test_spawn_flag(self, mock_frida):
        mock_frida.get_device.side_effect = self.mock_get_device
        injector = FridaInjector("com.android.settings", "../structs/android10", 10, "emulator-5554", True)
        injector.device.attach.side_effect = [ProcessNotFoundError(""), create_autospec(frida.core.Session)]
        injector.start()
        injector.stop()
        try:
            injector.device.spawn.assert_called_with(["com.android.settings"])
        except AssertionError as exc:
            self.fail(exc)

    @patch("binder_trace.generator.frida")
    def test_no_spawn_flag(self, mock_frida):
        mock_frida.get_device.side_effect = self.mock_get_device
        injector = FridaInjector("com.android.settings", "../structs/android10", 10, "emulator-5554", False)
        injector.start()
        injector.stop()
        try:
            injector.device.spawn.assert_not_called()
        except AssertionError as exc:
            self.fail(exc)

    @patch("binder_trace.generator.frida")
    def test_pause_unpause(self, mock_frida):
        mock_frida.get_device.side_effect = self.mock_get_device
        injector = FridaInjector("com.android.settings", "../structs/android10", 10, "emulator-5554", False)
        injector.start()
        self.assertTrue(injector.recording)
        injector.pause_unpause()
        self.assertFalse(injector.recording)
        injector.pause_unpause()
        self.assertTrue(injector.recording)
        injector.stop()
