"""Real local security regressions, no model or network calls."""
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'team'))
import agent
import local_service as service
from safe_artifacts import read_text, write_text


class P0Security(unittest.TestCase):
    def test_directory_links_and_leaf_reads_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            outside = root / 'outside'
            outside.mkdir()
            link = root / 'link'
            link.symlink_to(outside, target_is_directory=True)
            for role in ('LEAD', 'BRAIN', 'CHECK', 'COMMAND'):
                with self.subTest(role=role), self.assertRaises(OSError):
                    agent.schreibe(link, role, {'status': 'probe'})
                self.assertFalse((outside / (role + '.json')).exists())
            (outside / 'LEAD.json').write_text('{"secret":true}')
            self.assertIsNone(agent.lies(link, 'LEAD'))
            (root / 'LEAD.json').symlink_to(outside / 'LEAD.json')
            self.assertIsNone(agent.lies(root, 'LEAD'))

    def test_atomic_write_replaces_leaf_link_without_touching_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / 'target').write_text('unchanged')
            (root / 'output').symlink_to(root / 'target')
            write_text(root / 'output', 'safe')
            self.assertEqual((root / 'target').read_text(), 'unchanged')
            self.assertEqual(read_text(root / 'output'), 'safe')

    def _process(self, mode, parent_exit=False):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / 'work').mkdir()
            ready, marker = root / 'ready', root / 'marker'
            child = ('import signal,time,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN); '
                     f'pathlib.Path({str(ready)!r}).touch(); time.sleep(2); '
                     f'pathlib.Path({str(marker)!r}).touch()')
            parent = ('import subprocess,sys,time; '
                      f'subprocess.Popen([sys.executable,"-c",{child!r}]); '
                      + ('' if parent_exit else 'time.sleep(20)'))
            def stop():
                deadline = time.monotonic() + 3
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(.01)
                if mode == 'stop':
                    (root / 'work' / 'STOP').touch()
            thread = threading.Thread(target=stop)
            thread.start()
            try:
                with mock.patch.object(service, 'TEAM', root):
                    if mode == 'timeout':
                        with self.assertRaises(subprocess.TimeoutExpired):
                            service.rolle_starten([sys.executable, '-c', parent], cwd=root,
                                                  env=os.environ.copy(), timeout=.7)
                    else:
                        result = service.rolle_starten([sys.executable, '-c', parent], cwd=root,
                                                      env=os.environ.copy(), timeout=5)
                        self.assertEqual(result.returncode, -4)
                self.assertTrue(ready.exists())
                time.sleep(2.1)
                self.assertFalse(marker.exists(), 'descendant survived cancellation')
            finally:
                thread.join(timeout=4)

    def test_stop_kills_term_ignoring_descendant(self):
        self._process('stop')

    def test_stop_after_parent_exit_kills_descendant(self):
        self._process('stop', parent_exit=True)

    def test_timeout_kills_descendant(self):
        self._process('timeout')
