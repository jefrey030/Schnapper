"""Regression: beschädigte Base64-Journaldaten werden kontrolliert abgewiesen."""
import base64
import hashlib
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app"))
from schnapper.sicherer_speicher import _parse_journal


class RestoreJournalInvalidBase64(unittest.TestCase):
    def test_invalid_base64_fails_closed_as_oserror(self):
        body = {
            "version": 1,
            "previous": {"missionen.json": "%%invalid%%", "blitz.json": None},
            "next": {"missionen.json": None, "blitz.json": None},
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        body["sha256"] = hashlib.sha256(canonical).hexdigest()
        raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        with self.assertRaisesRegex(OSError, "Wiederherstellungsjournal ist beschädigt"):
            _parse_journal(raw)


if __name__ == "__main__":
    unittest.main()
