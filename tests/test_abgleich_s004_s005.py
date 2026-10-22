"""Abgleich der Vorschläge S-004/S-005 gegen den Code auf main (7a0b83e).

Belegt, welche Testkriterien (T1, T2, T4) der übernommene Code aus PR #10
bereits erfüllt. T3 (Mock-Adapter mit TEST-Daten) ist auf main nicht umgesetzt
und wird deshalb hier nicht als erfüllt behauptet.
"""
import os
import pathlib
import socket
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app"))
from schnapper.adapter import EbayAdapter, QuelleGesperrt
from schnapper.quellen import QuellenFehler, Register


class TestAbgleichS004(unittest.TestCase):
    def test_t1_kleinanzeigen_wird_abgewiesen(self):
        grund = Register().pruefe("kleinanzeigen")
        self.assertIsNotNone(grund)
        self.assertIn("ausgeschlossen", grund)

    def test_t1_kleinanzeigen_nicht_per_datei_freischaltbar(self):
        with self.assertRaises(QuellenFehler):
            Register().erlaube("kleinanzeigen", "Kleinanzeigen", "Versuch")

    def test_t2_unbekannte_quelle_wird_abgewiesen(self):
        grund = Register().pruefe("unbekannt-xyz")
        self.assertIsNotNone(grund)
        self.assertIn("nicht freigegeben", grund)

    def test_nur_mock_und_eigene_standardmaessig_erlaubt(self):
        erlaubt = sorted(q.kennung for q in Register() if q.freigegeben)
        self.assertEqual(erlaubt, ["eigene", "mock"])


class TestAbgleichS005(unittest.TestCase):
    def test_t4_ebay_ohne_freigabe_gesperrt_ohne_netzaufruf(self):
        def kein_netz(*a, **k):
            raise AssertionError("Netzwerkaufruf trotz Sperre")

        umgebung = {k: v for k, v in os.environ.items() if k != EbayAdapter.FREIGABE_VARIABLE}
        with mock.patch.dict(os.environ, umgebung, clear=True), \
                mock.patch.object(socket, "create_connection", kein_netz), \
                mock.patch.object(socket.socket, "connect", kein_netz):
            with self.assertRaises(QuelleGesperrt):
                EbayAdapter().lade()

    def test_t4_ebay_bleibt_gesperrt_auch_mit_schalter(self):
        with mock.patch.dict(os.environ, {EbayAdapter.FREIGABE_VARIABLE: "ja"}):
            with self.assertRaises(QuelleGesperrt):
                EbayAdapter().lade()


if __name__ == "__main__":
    unittest.main()
