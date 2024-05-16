import unittest

from binder_trace.__main__ import setupArgParser


class ArgParseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.argparser = setupArgParser()

    def test_valid_args(self):
        parsed_args = self.argparser.parse_args(
            ["-n", "com.android.settings", "-a", "12", "-d", "emulator-5554", "--spawn"]
        )

        self.assertEqual(parsed_args.android_version, "12")
        self.assertEqual(parsed_args.name, "com.android.settings")
        self.assertEqual(parsed_args.device, "emulator-5554")
        self.assertTrue(parsed_args.spawn)

    def test_invalid_values(self):
        def str_pid():
            self.argparser.parse_args(["pid", "hello", "-a", "12"])

        def invalid_android_version():
            self.argparser.parse_args(["pid", "4", "-a", "18"])

        def no_android_version():
            self.argparser.parse_args(["pid", "4", "-a"])

        self.assertRaises(SystemExit, str_pid)
        self.assertRaises(SystemExit, invalid_android_version)
        self.assertRaises(SystemExit, no_android_version)

    def test_default_spawn(self):
        parsed_args = self.argparser.parse_args(["-p", "12", "-a", "11"])

        self.assertFalse(parsed_args.spawn)

    def test_mutually_exclusive(self):
        def pid_and_name():
            self.argparser.parse_args(["--pid", "12", "--name", "helloworld", "-a", "13"])

        self.assertRaises(SystemExit, pid_and_name)

    def test_missing_key_args(self):
        def pid_and_name():
            self.argparser.parse_args(["-a", "13"])

        def android_version_and_struct_path():
            self.argparser.parse_args(["-p", "13"])

        self.assertRaises(SystemExit, pid_and_name)
        self.assertRaises(SystemExit, android_version_and_struct_path)
