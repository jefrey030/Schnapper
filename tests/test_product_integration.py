"""End-to-end HTTP regressions for the locally integrated five-module app."""
import datetime as dt
import json
import pathlib
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper import web  # noqa: E402
from schnapper.mission import MissionsFehler  # noqa: E402
import schnapper.sicherer_speicher as sicherer_speicher  # noqa: E402

BEISPIEL = ROOT / "app" / "beispiele" / "angebote.csv"


class ProductIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data_dir = pathlib.Path(self.temp.name) / "state"
        self.server = None
        self.thread = None
        self._server_starten()

    def tearDown(self):
        self._server_stoppen()
        self.temp.cleanup()

    def _server_starten(self):
        self.server = web.erstelle_server(BEISPIEL, port=0, datenverzeichnis=self.data_dir)
        self.basis = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def _server_stoppen(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=2)
            self.server = None

    def request(self, method, path, data=None, headers=None, base=None):
        kopf = dict(headers or {})
        if data is not None:
            kopf.setdefault("X-Schnapper", "1")
            kopf.setdefault("Content-Type", "application/json")
        req = urllib.request.Request((base or self.basis) + path, data=data, headers=kopf, method=method)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(req, timeout=5) as response:
                body = response.read()
                try:
                    parsed = json.loads(body or b"{}")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    parsed = body.decode("utf-8", errors="replace")
                return response.status, parsed
        except urllib.error.HTTPError as exc:
            body = exc.read()
            try:
                parsed = json.loads(body or b"{}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                parsed = body.decode("utf-8", errors="replace")
            return exc.code, parsed

    def post(self, path, payload):
        return self.request("POST", path, json.dumps(payload).encode())

    def offer_import(self, **changes):
        offer = {
            "id": "camera-1",
            "titel": "Kamera Lumix",
            "preis": "80",
            "versand": "4",
            "url": "https://angebote.example/kamera-1",
            "quelle": "eigene",
            "erfasst_am": dt.datetime.now(dt.timezone.utc).isoformat(),
            "region": "Berlin",
            "entfernung_km": "12",
            "referenzpreis": "100",
        }
        offer.update(changes)
        status, data = self.request(
            "POST", "/api/import", json.dumps([offer]).encode(),
            {"X-Schnapper": "1", "X-Dateiname": "eigene.json", "Content-Type": "application/json"},
        )
        self.assertEqual(status, 200, data)
        return offer

    def create_mission(self, **changes):
        values = {
            "aktion": "erstellen",
            "name": "Kamera finden",
            "suche": "Kamera Lumix",
            "max_preis": "100",
            "min_rabatt": "",
            "zustaende": [],
            "intervall_minuten": 60,
            "region": "Berlin",
            "entfernung_km": "25",
            "automatisch": False,
        }
        values.update(changes)
        status, data = self.post("/api/missionen", values)
        self.assertEqual(status, 201, data)
        return data["mission"]

    def test_mission_search_to_cart_price_analysis_and_blitz_queue(self):
        self.offer_import()
        created = self.create_mission()

        status, search = self.request(
            "GET", "/api/suche?text=kamera&region=Berlin&entfernung_km=25&sortierung=preis"
        )
        self.assertEqual(status, 200)
        self.assertEqual([x["id"] for x in search["treffer"]], ["camera-1"])
        self.assertEqual(search["treffer"][0]["region"], "Berlin")
        self.assertEqual(search["treffer"][0]["entfernung_km"], "12")
        self.assertEqual(search["treffer"][0]["gesamtpreis"], "84.00")

        status, run = self.post(f"/api/missionen/{created['id']}/lauf", {"automatisch": False})
        self.assertEqual(status, 200, run)
        self.assertEqual([x["id"] for x in run["treffer"]], ["camera-1"])
        self.assertEqual(len(run["meldungen"]), 1)
        self.assertEqual(run["benachrichtigung"], "lokale_queue")
        self.assertEqual(run["meldungen"][0]["gesamtpreis"], "84.00")
        self.assertEqual(run["meldungen"][0]["url"], "https://angebote.example/kamera-1")
        self.assertEqual(run["meldungen"][0]["quelle"], "eigene")

        # A repeat manual check must not create a duplicate BLITZ notice.
        status, second = self.post(f"/api/missionen/{created['id']}/lauf", {"automatisch": False})
        self.assertEqual(status, 200, second)
        self.assertEqual(second["meldungen"], [])

        # Region and radius filters require actual offer metadata; no inferred location.
        self.assertEqual(self.request("GET", "/api/suche?text=kamera&region=Hamburg")[1]["treffer"], [])
        self.assertEqual(self.request("GET", "/api/suche?text=kamera&entfernung_km=5")[1]["treffer"], [])

    def test_missions_persist_after_server_restart(self):
        mission = self.create_mission()
        self._server_stoppen()
        self._server_starten()
        status, data = self.request("GET", "/api/missionen")
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in data["missionen"]], [mission["id"]])

    def test_automatic_mission_requires_explicit_opt_in_and_is_due(self):
        self.offer_import()
        off = self.create_mission()
        status, data = self.post(f"/api/missionen/{off['id']}/lauf", {"automatisch": True})
        self.assertEqual(status, 409)
        self.assertIn("nicht automatisch fällig", data["fehler"])

        on = self.create_mission(name="Opt-in Kamera", automatisch=True)
        status, first = self.post(f"/api/missionen/{on['id']}/lauf", {"automatisch": True})
        self.assertEqual(status, 200, first)
        status, second = self.post(f"/api/missionen/{on['id']}/lauf", {"automatisch": True})
        self.assertEqual(status, 409)
        self.assertIn("nicht automatisch fällig", second["fehler"])

    def test_backup_restore_is_validated_repeatable_and_restores_both_server_stores(self):
        self.offer_import()
        first = self.create_mission()
        status, run = self.post(f"/api/missionen/{first['id']}/lauf", {"automatisch": False})
        self.assertEqual(status, 200, run)
        self.assertEqual(len(run["meldungen"]), 1)
        status, backup = self.request("GET", "/api/backup")
        self.assertEqual(status, 200)
        self.assertEqual(len(backup["missionen"]), 1)
        self.assertEqual(len(backup["blitz_gesehen"]), 1)

        self.create_mission(name="Zusatz", suche="Lampe")
        status, changed = self.request("GET", "/api/backup")
        self.assertEqual(status, 200)
        self.assertEqual(len(changed["missionen"]), 2)

        status, restored = self.post("/api/backup", backup)
        self.assertEqual(status, 200, restored)
        status, restored_again = self.post("/api/backup", backup)
        self.assertEqual(status, 200, restored_again)
        status, state = self.request("GET", "/api/backup")
        self.assertEqual(status, 200)
        self.assertEqual(state["missionen"], backup["missionen"])
        self.assertEqual(state["blitz_gesehen"], backup["blitz_gesehen"])

        broken = {**backup, "blitz_gesehen": {"bad-key": "not a hash"}}
        status, _ = self.post("/api/backup", broken)
        self.assertEqual(status, 400)
        self.assertEqual(self.request("GET", "/api/backup")[1]["missionen"], backup["missionen"])

    def test_failed_two_file_restore_rolls_back_from_durable_journal(self):
        self.offer_import()
        first = self.create_mission()
        status, initial = self.request("GET", "/api/backup")
        self.assertEqual(status, 200)
        self.create_mission(name="Current extra", suche="Lampe")
        status, before = self.request("GET", "/api/backup")
        self.assertEqual(status, 200)
        self.assertEqual(len(before["missionen"]), 2)

        real_write = sicherer_speicher.schreibe_fd
        fail_once = {"done": False}

        def fail_second_store(directory, name, raw):
            if name == "blitz.json" and not fail_once["done"]:
                fail_once["done"] = True
                raise OSError("simulated disk-full after first replacement")
            return real_write(directory, name, raw)

        with mock.patch.object(sicherer_speicher, "schreibe_fd", side_effect=fail_second_store):
            status, _ = self.post("/api/backup", initial)
        self.assertEqual(status, 500)
        self.assertTrue(fail_once["done"])

        # Next safe read recovers the journal to the complete previous snapshot.
        status, after = self.request("GET", "/api/backup")
        self.assertEqual(status, 200)
        self.assertEqual(after["missionen"], before["missionen"])
        self.assertEqual(after["blitz_gesehen"], before["blitz_gesehen"])
        self.assertFalse((self.data_dir / ".schnapper-restore-journal.json").exists())

    def test_partial_edit_and_delete_are_safe(self):
        mission = self.create_mission()
        status, updated = self.post("/api/missionen", {
            "aktion": "bearbeiten", "id": mission["id"], "name": "Neuer Name",
        })
        self.assertEqual(status, 200, updated)
        self.assertEqual(updated["mission"]["name"], "Neuer Name")
        self.assertEqual(updated["mission"]["region"], "Berlin")

        status, deleted = self.post("/api/missionen", {"aktion": "loeschen", "id": mission["id"]})
        self.assertEqual(status, 200, deleted)
        self.assertEqual(self.request("GET", "/api/missionen")[1]["missionen"], [])

    def test_only_one_mission_run_can_be_in_flight(self):
        self.offer_import()
        mission = self.create_mission()
        entered = threading.Event()
        release = threading.Event()
        original = web.finde_in

        def delayed(*args, **kwargs):
            entered.set()
            if not release.wait(3):
                raise TimeoutError("test release timed out")
            return original(*args, **kwargs)

        with mock.patch.object(web, "finde_in", side_effect=delayed):
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(
                    self.post, f"/api/missionen/{mission['id']}/lauf", {"automatisch": False}
                )
                self.assertTrue(entered.wait(2))
                second_status, second = self.post(
                    f"/api/missionen/{mission['id']}/lauf", {"automatisch": False}
                )
                release.set()
                first_status, first_data = first.result(timeout=5)
        self.assertEqual(second_status, 409, second)
        self.assertEqual(first_status, 200, first_data)

    def test_two_server_instances_share_mission_run_lock(self):
        self.offer_import()
        mission = self.create_mission()
        second_server = web.erstelle_server(BEISPIEL, port=0, datenverzeichnis=self.data_dir)
        second_base = f"http://127.0.0.1:{second_server.server_address[1]}"
        second_thread = threading.Thread(target=second_server.serve_forever, daemon=True)
        second_thread.start()
        entered = threading.Event()
        release = threading.Event()
        original = web.finde_in

        def delayed(*args, **kwargs):
            entered.set()
            if not release.wait(3):
                raise TimeoutError("test release timed out")
            return original(*args, **kwargs)

        try:
            with mock.patch.object(web, "finde_in", side_effect=delayed):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    first = pool.submit(
                        self.post, f"/api/missionen/{mission['id']}/lauf", {"automatisch": False}
                    )
                    self.assertTrue(entered.wait(2))
                    second_status, second = self.request(
                        "POST", f"/api/missionen/{mission['id']}/lauf",
                        json.dumps({"automatisch": False}).encode(),
                        {"X-Schnapper": "1", "Content-Type": "application/json"},
                        base=second_base,
                    )
                    release.set()
                    first_status, first_data = first.result(timeout=5)
            self.assertEqual(second_status, 409, second)
            self.assertEqual(first_status, 200, first_data)
        finally:
            release.set()
            second_server.shutdown()
            second_server.server_close()
            second_thread.join(timeout=2)

    def test_sw_is_served_without_caching_api_data(self):
        status, response = self.request("GET", "/sw.js")
        self.assertEqual(status, 200)
        self.assertIn('url.pathname.startsWith("/api/")', response)
        self.assertIn('url.origin !== self.location.origin', response)
        status, html = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("PREISDETEKTIV", html)
        self.assertIn("mission", (ROOT / "app" / "schnapper" / "web" / "app.js").read_text())

    def test_symlink_state_directory_is_rejected(self):
        base = pathlib.Path(self.temp.name)
        real = base / "real"
        real.mkdir()
        link = base / "linked"
        link.symlink_to(real, target_is_directory=True)
        with self.assertRaises((OSError, MissionsFehler)):
            web.erstelle_server(BEISPIEL, port=0, datenverzeichnis=link)


if __name__ == "__main__":
    unittest.main()
