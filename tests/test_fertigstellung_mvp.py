"""SCHNAPPER-Fertigstellung: reale Offline-CLI-/HTTP-Abnahme ohne externe Dienste."""
import io
import json
import os
import pathlib
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.__main__ import main as cli_main  # noqa: E402
from schnapper.verlauf import Verlauf  # noqa: E402
from schnapper.web import erstelle_server  # noqa: E402
from schnapper import openprices  # noqa: E402


CSV_HEADER = "id;titel;preis;versand;referenzpreis;zustand;quelle;kategorie;url;erfasst_am"
GUTES_ANGEBOT = (
    "gut;Kopfhörer Berlin;45,00;5;100;gebraucht;eigene;Audio;"
    "https://shop.example/test-angebot;2026-10-21T12:00:00Z"
)
GESPERRTES_ANGEBOT = (
    "fremd;Kopfhörer unzulässige Quelle;10;0;100;gebraucht;kleinanzeigen;Audio;"
    "https://shop.example/nicht-freigegeben;2026-10-21T12:00:00Z"
)


class CliFertigstellung(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pfad = pathlib.Path(self.tmp.name) / "meine.csv"
        self.pfad.write_text(CSV_HEADER + "\n" + GUTES_ANGEBOT + "\n", encoding="utf-8")
        self.verlauf = pathlib.Path(self.tmp.name) / "preise.json"

    def ausfuehren(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli_main([str(self.pfad), *args])
        return code, out.getvalue(), err.getvalue()

    def test_gueltige_eigene_csv_liefert_treffer_ohne_livequelle(self):
        code, ausgabe, fehler = self.ausfuehren(
            "--suche", "kopfhoerer", "--max-preis", "50",
            "--min-rabatt", "40,0", "--json")
        self.assertEqual((code, fehler), (0, ""))
        treffer = json.loads(ausgabe)["treffer"]
        self.assertEqual(len(treffer), 1)
        self.assertEqual(treffer[0]["gesamtpreis"], "50.00")
        self.assertEqual(treffer[0]["quelle"], "eigene")
        self.assertEqual(treffer[0]["rabatt_prozent"], "50.0")

    def test_ungueltige_filter_sind_kontrolliert_und_schreiben_nicht(self):
        faelle = (
            ("--min-rabatt", "abc"), ("--min-rabatt", "NaN"),
            ("--min-rabatt", "Infinity"), ("--min-rabatt", "-1"),
            ("--min-rabatt", "101"), ("--max-preis", "0"),
            ("--max-preis", "-9"), ("--max-preis", "abc"),
            ("--zustand", "unbekanntes-format"),
        )
        for option, wert in faelle:
            with self.subTest(option=option, wert=wert):
                code, ausgabe, fehler = self.ausfuehren(
                    option, wert, "--verlauf", str(self.verlauf))
                self.assertEqual(code, 2)
                self.assertEqual(ausgabe, "")
                self.assertIn("Ungültiger Suchfilter", fehler)
                self.assertFalse(self.verlauf.exists())

    def test_fehlende_angebote_fehlschlag_ohne_traceback(self):
        self.pfad.unlink()
        code, ausgabe, fehler = self.ausfuehren("--json")
        self.assertEqual(code, 1)
        self.assertFalse(ausgabe)
        self.assertIn("Angebotsdatei konnte nicht gelesen werden", fehler)
        self.assertNotIn("Traceback", fehler)

    def test_verlauf_nach_erfolgreichem_import_idempotent(self):
        code, _, fehler = self.ausfuehren("--verlauf", str(self.verlauf), "--json")
        self.assertEqual((code, fehler), (0, ""))
        raw = json.loads(self.verlauf.read_text(encoding="utf-8"))
        self.assertEqual(sum(len(x) for x in raw["angebote"].values()), 1)
        code, _, fehler = self.ausfuehren("--verlauf", str(self.verlauf), "--json")
        self.assertEqual((code, fehler), (0, ""))
        raw = json.loads(self.verlauf.read_text(encoding="utf-8"))
        self.assertEqual(sum(len(x) for x in raw["angebote"].values()), 1)

    def test_speicherfehler_stoppt_ausgabe(self):
        with mock.patch.object(Verlauf, "importiere", side_effect=OSError("simulierter Defekt")):
            code, ausgabe, fehler = self.ausfuehren(
                "--verlauf", str(self.verlauf), "--json")
        self.assertEqual(code, 1)
        self.assertEqual(ausgabe, "")
        self.assertIn("nicht sicher gespeichert", fehler)
        self.assertNotIn("simulierter Defekt", fehler)


class WebFertigstellung(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        self.pfad = root / "eigene.csv"
        self.pfad.write_text(CSV_HEADER + "\n" + GUTES_ANGEBOT + "\n", encoding="utf-8")
        self.verlauf = root / "verlauf.json"
        self.server = erstelle_server(self.pfad, port=0, verlauf=self.verlauf)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._server_schliessen)
        self.url = "http://127.0.0.1:" + str(self.server.server_address[1])
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _server_schliessen(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def req(self, path, data=None, headers=None):
        req = urllib.request.Request(
            self.url + path, data=data,
            headers=headers or {},
            method="POST" if data is not None else "GET")
        try:
            with self.opener.open(req, timeout=5) as response:
                return response.status, response.headers, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, json.loads(exc.read())

    def test_eigene_liste_suche_mit_preis_und_verlauf(self):
        code, headers, body = self.req(
            "/api/suche?text=kopfhoerer&max_preis=50&sortierung=preis")
        self.assertEqual(code, 200)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertTrue(body["verlauf_aktiv"])
        self.assertFalse(body["beispieldaten"])
        self.assertEqual([(t["id"], t["gesamtpreis"]) for t in body["treffer"]],
                         [("gut", "50.00")])
        self.assertTrue(self.verlauf.exists())

    def test_upload_lehnt_fremdquelle_ab_und_uebernimmt_eigene(self):
        csv = (CSV_HEADER + "\n" + GUTES_ANGEBOT.replace("gut;", "neu;") +
               "\n" + GESPERRTES_ANGEBOT + "\n").encode("utf-8")
        code, _, _ = self.req(
            "/api/import", csv, {"X-Dateiname": "eigene.csv"})
        self.assertEqual(code, 403)
        code, _, body = self.req("/api/import", csv, {
            "X-Dateiname": "eigene.csv", "X-Schnapper": "1"})
        self.assertEqual(code, 200)
        self.assertEqual(body["eingelesen"], 1)
        self.assertTrue(any("ausgeschlossen" in w for w in body["ungueltig"]))
        code, _, body = self.req("/api/suche?sortierung=preis")
        self.assertEqual(code, 200)
        self.assertEqual([x["id"] for x in body["treffer"]], ["neu"])

    def test_barcode_ohne_betreiberfreigabe_kein_internet(self):
        payload = json.dumps({"ean": "4008400402222"}).encode("utf-8")
        with mock.patch.dict(os.environ, {openprices.FREIGABE_VARIABLE: ""}), \
             mock.patch.object(openprices, "_abruf") as abruf:
            code, _, body = self.req(
                "/api/openprices", payload,
                {"X-Schnapper": "1", "Content-Type": "application/json"})
        self.assertEqual(code, 403)
        self.assertIn("FREIGABE", body["fehler"])
        abruf.assert_not_called()


if __name__ == "__main__":
    unittest.main()
