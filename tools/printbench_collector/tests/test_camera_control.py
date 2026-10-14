import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import camera_control
import quiet_process


class CameraTests(unittest.TestCase):
    def test_expiry_off_and_bad_requests(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(camera_control, 'LEASE', Path(directory)/'lease'), patch.object(camera_control.time, 'time', return_value=1000):
            self.assertFalse(camera_control.enabled())
            camera_control.request(30)
            self.assertTrue(camera_control.enabled())
            self.assertFalse(camera_control.enabled(2800))
            camera_control.disable()
            self.assertFalse(camera_control.enabled())
            for duration in (0, 481):
                with self.assertRaises(ValueError): camera_control.request(duration)
            camera_control.LEASE.write_text('{broken')
            self.assertFalse(camera_control.enabled())
            camera_control.LEASE.write_text(json.dumps({'expires': 999999}))
            self.assertFalse(camera_control.enabled())

    def test_windows_hidden(self):
        with patch.object(quiet_process.os, 'name', 'nt'), patch.object(quiet_process.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True):
            self.assertEqual(quiet_process.options(), {'creationflags': 0x08000000})

    def test_media_disabled_then_enabled_then_disabled(self):
        # Isolate external printer/network modules; exercise the actual worker loop.
        names = ('requests', 'collector', 'native_media', 'session_tracker')
        with patch.dict(sys.modules, {name: types.ModuleType(name) for name in names}):
            worker = importlib.import_module('media_worker')
        event = Mock()
        event.wait.side_effect = [False, False, False, True]
        proc = Mock()
        proc.poll.return_value = None
        with tempfile.TemporaryDirectory() as directory, patch.object(worker, 'MEDIA', Path(directory)), patch.object(worker.camera_control, 'enabled', side_effect=[False, True, True, False]), patch.object(worker, 'start_ffmpeg', return_value=proc) as start, patch.object(worker, 'latest_state', return_value={}), patch.object(worker.native_media, 'sync_native', return_value={}, create=True):
            worker.run_forever(event)
        start.assert_called_once()
        proc.terminate.assert_called_once()
        proc.wait.assert_called_once_with(timeout=5)

    def test_idle_never_starts_ffmpeg(self):
        names = ('requests', 'collector', 'native_media', 'session_tracker')
        with patch.dict(sys.modules, {name: types.ModuleType(name) for name in names}):
            worker = importlib.import_module('media_worker')
        event = Mock()
        event.wait.side_effect = [False, False, True]
        with patch.object(worker.camera_control, 'enabled', return_value=False), patch.object(worker, 'start_ffmpeg') as start, patch.object(worker, 'clear_session_marker'):
            worker.run_forever(event)
        start.assert_not_called()


if __name__ == '__main__': unittest.main()
