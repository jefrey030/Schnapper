"""Diagnose-Tests: nur synthetische Umgebung, niemals echte Inferenz."""
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import diagnose_local as diagnose


class TestDiagnose(unittest.TestCase):
    def test_altes_mac_wird_ohne_ki_aufruf_blockiert(self):
        with mock.patch.object(diagnose.platform, "system", return_value="Darwin"), \
             mock.patch.object(diagnose.platform, "mac_ver", return_value=("10.15.7", ("", "", ""), "")), \
             mock.patch.object(diagnose.shutil, "which", return_value="/usr/local/bin/ollama"), \
             mock.patch.object(diagnose, "_request") as req:
            r = diagnose.diagnose()
        self.assertFalse(r["startbereit"])
        self.assertFalse(r["modell_angerufen"])
        req.assert_not_called()

    def test_linux_local_installation_wird_erkannt_ohne_inferenz(self):
        with mock.patch.object(diagnose.platform, "system", return_value="Linux"), \
             mock.patch.object(diagnose.shutil, "which", return_value="/usr/bin/test"), \
             mock.patch.object(diagnose, "_request",
                               return_value={"models": [{"name": "qwen2.5:1.5b"}]}) as req, \
             mock.patch.dict(diagnose.os.environ, {"SCHNAPPER_OLLAMA_MODELL": "qwen2.5:1.5b"}):
            r = diagnose.diagnose()
        self.assertTrue(r["startbereit"])
        self.assertFalse(r["modell_angerufen"])
        req.assert_called_once_with("/api/tags", timeout=3)

    def test_cloud_modell_wird_abgelehnt_ohne_anfrage(self):
        with mock.patch.object(diagnose.platform, "system", return_value="Linux"), \
             mock.patch.object(diagnose.shutil, "which", return_value="/usr/bin/test"), \
             mock.patch.object(diagnose, "_request") as req, \
             mock.patch.dict(diagnose.os.environ, {"SCHNAPPER_OLLAMA_MODELL": "gemma4:cloud"}):
            r = diagnose.diagnose()
        self.assertFalse(r["startbereit"])
        req.assert_not_called()


if __name__ == "__main__":
    unittest.main()
