"""MASTER 122: approval/task FIFO must fail closed without blocking a worker.

No external model, network or real operator approval is required.
"""
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'team'))
import operator_approval as approval


@unittest.skipUnless(hasattr(os, 'mkfifo') and hasattr(os, 'O_NONBLOCK'), 'POSIX FIFO needed')
class TestApprovalNonblocking(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.team = pathlib.Path(self.temp.name) / 'team'
        self.work = self.team / 'work'
        self.work.mkdir(parents=True)
        self.approval_file = self.work / 'operator_approval.json'
        self.tasks_file = self.team / 'tasks.json'
        self.now = dt.datetime.now(dt.timezone.utc)
        self.tasks_file.write_text(json.dumps({'tasks': [{'id': 'S-014', 'status': 'open'}]}), encoding='utf-8')
        self.approval_file.write_text(json.dumps({
            'approved': True,
            'scope': 'LOCAL_OLLAMA_ONLY',
            'task_id': 'S-014',
            'expires_at_utc': (self.now + dt.timedelta(minutes=15)).isoformat(),
        }), encoding='utf-8')
        self.approval_file.chmod(0o600)
        for attr, value in [('TEAM', self.team), ('WORK', self.work),
                            ('STOP', self.work / 'STOP'), ('TASKS', self.tasks_file),
                            ('APPROVAL', self.approval_file)]:
            patcher = mock.patch.object(approval, attr, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _run_separate_process(self):
        """Timeout proves a FIFO regression does not hang the test suite itself."""
        code = (
            'import pathlib,sys; sys.path.insert(0,sys.argv[1]); '
            'import operator_approval as a; '
            'a.TEAM=pathlib.Path(sys.argv[2]); a.WORK=a.TEAM/"work"; '
            'a.APPROVAL=a.WORK/"operator_approval.json"; a.TASKS=a.TEAM/"tasks.json"; '
            'a.STOP=a.WORK/"STOP"; '
            'from ki import KINichtVerfuegbar; '
            'exec("try:\\n a.pruefe_freigabe()\\nexcept KINichtVerfuegbar:\\n sys.exit(7)\\nsys.exit(1)")'
        )
        result = subprocess.run([sys.executable, '-c', code,
                                 str(pathlib.Path(__file__).resolve().parents[1] / 'team'),
                                 str(self.team)], timeout=3, capture_output=True, text=True)
        self.assertEqual(result.returncode, 7, result.stderr)

    def test_regular_file_remains_valid(self):
        self.assertEqual(approval.pruefe_freigabe(self.now), 'S-014')

    def test_approval_fifo_refused_without_blocking(self):
        self.approval_file.unlink()
        os.mkfifo(self.approval_file, mode=0o600)
        self._run_separate_process()

    def test_task_fifo_refused_without_blocking(self):
        self.tasks_file.unlink()
        os.mkfifo(self.tasks_file, mode=0o600)
        self._run_separate_process()

    def test_both_reads_require_nonblocking_and_no_follow(self):
        original = approval.os.open
        with mock.patch.object(approval.os, 'open', wraps=original) as tracked:
            self.assertEqual(approval.pruefe_freigabe(self.now), 'S-014')
        visited = {
            (str(call.args[0]), call.kwargs.get("dir_fd")): call.args[1]
            for call in tracked.call_args_list
        }
        for filename in (self.approval_file, self.tasks_file):
            flags = next(flags for (name, dir_fd), flags in visited.items()
                         if name == filename.name and dir_fd is not None)
            self.assertTrue(flags & os.O_NOFOLLOW)
            self.assertTrue(flags & os.O_NONBLOCK)


if __name__ == '__main__':
    unittest.main()
