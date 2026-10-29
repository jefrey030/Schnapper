"""Real local OS processes, no model inference or external services."""
import concurrent.futures
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
import local_ollama
import local_service
from ki import KINichtVerfuegbar


def reserve(path):
    # Constructor consent and inference are separately tested; exercise real flock.
    instance = object.__new__(local_ollama.KI)
    instance.zaehler = pathlib.Path(path)
    try:
        return instance._zaehle()
    except KINichtVerfuegbar:
        return None


class Integration(unittest.TestCase):
    def test_counter_real_parallel_processes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'counter'
            with concurrent.futures.ProcessPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(reserve, [str(path)] * 24))
            self.assertEqual(sorted(x for x in results if x is not None),
                             list(range(1, local_ollama.MAX_AUFRUFE + 1)))
            self.assertEqual(int(path.read_text()), local_ollama.MAX_AUFRUFE)

    def test_stop_terminates_real_child_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            team = pathlib.Path(tmp)
            (team / 'work').mkdir()
            ready = team / 'ready'
            done = team / 'done'
            stop = team / 'work' / 'STOP'
            code = ('import pathlib,time; '
                    f'pathlib.Path({str(ready)!r}).touch(); '
                    'time.sleep(20); '
                    f'pathlib.Path({str(done)!r}).touch()')
            def trigger():
                deadline = time.monotonic() + 5
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(.01)
                stop.touch()
            thread = threading.Thread(target=trigger)
            thread.start()
            try:
                with mock.patch.object(local_service, 'TEAM', team):
                    result = local_service.rolle_starten(
                        [sys.executable, '-c', code], cwd=tmp,
                        env=os.environ.copy(), timeout=8)
            finally:
                thread.join(timeout=6)
            self.assertTrue(ready.exists())
            self.assertEqual(result.returncode, -4)
            self.assertFalse(done.exists())

    def test_approval_revoked_during_discovery_blocks_inference(self):
        instance = object.__new__(local_ollama.KI)
        instance.modell = 'offline-fixture'
        with mock.patch.object(local_ollama, 'pruefe_freigabe',
                               side_effect=['S-014', KINichtVerfuegbar('revoked')]), \
             mock.patch.object(instance, '_pruefe_modell'), \
             mock.patch.object(instance, '_zaehle', return_value=1), \
             mock.patch.object(local_ollama, '_request') as request:
            with self.assertRaises(KINichtVerfuegbar):
                instance.frage('system', 'user')
            request.assert_not_called()
