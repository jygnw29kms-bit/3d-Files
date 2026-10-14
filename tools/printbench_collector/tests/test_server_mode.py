import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ServerModeTests(unittest.TestCase):
    def test_windows_telemetry_does_not_load_camera(self):
        import daemon
        with patch.object(daemon.os, 'name', 'nt'), patch.object(daemon.threading, 'Thread') as thread:
            self.assertIsNone(daemon.start_media_worker())
            thread.assert_not_called()
            with self.assertRaises(RuntimeError): daemon.start_media_worker(True)
            thread.assert_not_called()

    def test_linux_camera_requires_explicit_mode(self):
        import daemon
        with patch.object(daemon.os, 'name', 'posix'), patch.object(daemon.threading, 'Thread') as thread:
            self.assertIsNone(daemon.start_media_worker())
            thread.assert_not_called()
            daemon.start_media_worker(True)
            thread.return_value.start.assert_called_once()

    def test_server_credentials_file_and_missing_configuration(self):
        import collector
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'credentials.json'
            path.write_text(json.dumps({'serial':'test-serial','access_code':'test-only'}))
            with patch.dict(collector.os.environ, {'PRINTBENCH_PRINTER_CREDENTIALS_FILE':str(path)}):
                self.assertEqual(collector.load_local_bambu_identity(), ('test-serial','test-only'))
                path.write_text('{}')
                with self.assertRaises(RuntimeError): collector.load_local_bambu_identity()
        with patch.dict(collector.os.environ, {}, clear=True), patch.object(collector.os, 'name', 'posix'):
            with self.assertRaises(RuntimeError): collector.load_local_bambu_identity()
