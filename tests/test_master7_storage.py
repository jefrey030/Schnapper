"""MASTER 7 P0 regressions: concurrency, path anchoring and exchange races."""
import datetime as dt
import hashlib
import json
import multiprocessing
import os
import pathlib
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "team"))

from schnapper.alarm import Wunsch  # noqa: E402
from schnapper.angebot import Angebot  # noqa: E402
from schnapper.blitz import Blitz, BlitzFehler, BlitzKonflikt  # noqa: E402
from schnapper.einlesen import Importergebnis  # noqa: E402
from schnapper.mission import Mission, MissionsFehler, MissionsKonflikt, Missionsspeicher  # noqa: E402
import schnapper.sicherer_speicher as sicherer_speicher  # noqa: E402


JETZT = dt.datetime(2026, 10, 26, 12, tzinfo=dt.timezone.utc)


def _angebot():
    return Importergebnis(angebote=[Angebot(
        id="camera-1", titel="Kamera", preis=Decimal("20.00"),
        url="https://offers.example/camera", quelle="eigene",
        erfasst_am=JETZT, referenzpreis=Decimal("30.00"),
    )])


def _wunsch():
    return Wunsch.aus_dict({"name": "Kamera", "suche": "Kamera", "max_preis": "25"})


def _prozess_mission_erstellen(pfad, name, start_barriere, ausgabe):
    store = Missionsspeicher.laden(pfad)
    start_barriere.wait(timeout=5)
    try:
        store.erstellen(name=name, suche=name, jetzt=JETZT)
        ausgabe.put("gespeichert")
    except MissionsKonflikt:
        ausgabe.put("konflikt")


def _prozess_missionslauf_sperren(pfad, mission_id, ausgabe):
    with sicherer_speicher.missionslauf_sperre(pfad, mission_id) as gesperrt:
        ausgabe.put(gesperrt)


class MissionKonflikte(unittest.TestCase):
    def test_zwei_instanz_aenderungen_erkennen_konflikt_und_rebase_nicht_still(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            links, rechts = Missionsspeicher.laden(pfad), Missionsspeicher.laden(pfad)
            start = threading.Barrier(2)

            def erstellen(speicher, name):
                start.wait(timeout=5)
                try:
                    speicher.erstellen(name=name, suche=name, jetzt=JETZT)
                    return "gespeichert"
                except MissionsKonflikt:
                    return "konflikt"

            with ThreadPoolExecutor(max_workers=2) as pool:
                ergebnisse = list(pool.map(
                    lambda args: erstellen(*args), ((links, "Lampe"), (rechts, "Kamera"))))
            self.assertCountEqual(ergebnisse, ["gespeichert", "konflikt"])
            gewinner = Missionsspeicher.laden(pfad)
            self.assertEqual(len(gewinner.alle()), 1)

            # Der Konfliktnehmer kann nach dem frischen Lesen bewusst erneut schreiben.
            verlierer = links if "konflikt" in ergebnisse else rechts
            zweiter = verlierer.erstellen(name="Tasse", suche="Tasse", jetzt=JETZT)
            self.assertEqual({m.name for m in Missionsspeicher.laden(pfad).alle()},
                             {gewinner.alle()[0].name, zweiter.name})

    def test_separate_prozesse_erkennen_konflikt_statt_still_zu_ueberschreiben(self):
        if os.name != "posix":
            self.skipTest("flock-/dirfd-Prozesssperre erfordert POSIX")
        with tempfile.TemporaryDirectory() as tmp:
            pfad = str(pathlib.Path(tmp, "missionen.json"))
            context = multiprocessing.get_context("fork")
            barrier, result_queue = context.Barrier(2), context.Queue()
            processes = [
                context.Process(target=_prozess_mission_erstellen,
                                args=(pfad, name, barrier, result_queue))
                for name in ("Lampe", "Kamera")
            ]
            for process in processes:
                process.start()
            for process in processes:
                process.join(timeout=10)
            self.assertTrue(all(not process.is_alive() for process in processes))
            self.assertTrue(all(process.exitcode == 0 for process in processes))
            self.assertCountEqual([result_queue.get(timeout=2) for _ in processes],
                                  ["gespeichert", "konflikt"])
            self.assertEqual(len(Missionsspeicher.laden(pfad).alle()), 1)

    def test_acht_vorgeladene_instanz_aenderungen_bleiben_nach_explizitem_retry_erhalten(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            stores = [Missionsspeicher.laden(pfad) for _ in range(8)]
            barrier = threading.Barrier(len(stores))

            def erstellen(index):
                barrier.wait(timeout=10)
                try:
                    stores[index].erstellen(name=f"Mission {index}", suche=f"Artikel {index}", jetzt=JETZT)
                    return index, "gespeichert"
                except MissionsKonflikt:
                    return index, "konflikt"

            with ThreadPoolExecutor(max_workers=len(stores)) as pool:
                results = list(pool.map(erstellen, range(len(stores))))
            self.assertEqual(sum(status == "gespeichert" for _index, status in results), 1)
            self.assertEqual(sum(status == "konflikt" for _index, status in results), 7)

            for index, status in results:
                if status == "konflikt":
                    store = Missionsspeicher.laden(pfad)
                    store.erstellen(
                        name=f"Mission {index}", suche=f"Artikel {index}", jetzt=JETZT)
            self.assertEqual({m.name for m in Missionsspeicher.laden(pfad).alle()},
                             {f"Mission {index}" for index in range(8)})

    def test_speicherfehler_laesst_alte_missionen_unveraendert(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            speicher = Missionsspeicher.laden(pfad)
            mission = speicher.erstellen(name="Kamera", suche="Kamera", jetzt=JETZT)
            original = pfad.read_bytes()
            with mock.patch.object(sicherer_speicher.os, "replace", side_effect=OSError("disk full")):
                with self.assertRaises(MissionsFehler):
                    speicher.pausieren(mission.id)
            self.assertEqual(pfad.read_bytes(), original)
            self.assertEqual(Missionsspeicher.laden(pfad).alle()[0].status, "aktiv")

    def test_uebergeordneter_symlink_und_leaf_symlink_blockiert(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            outside = root / "outside"
            outside.mkdir()
            (outside / "missionen.json").write_text('{"version":2,"missionen":[]}', encoding="utf-8")
            link = root / "linked"
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(MissionsFehler):
                Missionsspeicher.laden(link / "missionen.json")

            safe = root / "safe"
            safe.mkdir()
            (safe / "target.json").write_bytes((outside / "missionen.json").read_bytes())
            (safe / "missionen.json").symlink_to(safe / "target.json")
            with self.assertRaises(MissionsFehler):
                Missionsspeicher.laden(safe / "missionen.json")

    def test_fremde_oder_beschreibbare_speicherorte_blockieren(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            directory = root / "shared"
            directory.mkdir()
            directory.chmod(0o770)
            with self.assertRaises(MissionsFehler):
                Missionsspeicher.laden(directory / "missionen.json")

            private = root / "private"
            private.mkdir(mode=0o700)
            lock = private / ".schnapper-storage.lock"
            lock.write_text("lock", encoding="utf-8")
            lock.chmod(0o644)
            with self.assertRaises(MissionsFehler):
                Missionsspeicher.laden(private / "missionen.json")

    def test_verlinkte_oder_fremdlesbare_speicherdatei_blockiert(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            pfad = directory / "missionen.json"
            speicher = Missionsspeicher.laden(pfad)
            speicher.erstellen(name="Kamera", suche="Kamera", jetzt=JETZT)
            hardlink = directory / "alias.json"
            os.link(pfad, hardlink)
            with self.assertRaises(MissionsFehler):
                Missionsspeicher.laden(pfad)

    def test_speicherlock_symlink_und_beschaedigte_datei_bleiben_unveraendert(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            pfad = root / "missionen.json"
            ziel = root / "ziel"
            ziel.write_text("UNVERAENDERT", encoding="utf-8")
            (root / ".schnapper-storage.lock").symlink_to(ziel)
            with self.assertRaises(MissionsFehler):
                Missionsspeicher.laden(pfad)
            self.assertEqual(ziel.read_text(encoding="utf-8"), "UNVERAENDERT")

        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            store = Missionsspeicher.laden(pfad)
            store.erstellen(name="Vorher", suche="Kamera", jetzt=JETZT)
            pfad.write_bytes(b"{kaputt")
            with self.assertRaises(MissionsFehler):
                store.erstellen(name="Nachher", suche="Lampe", jetzt=JETZT)
            self.assertEqual(pfad.read_bytes(), b"{kaputt")

    def test_private_mission_datei_ueberlebt_neustart(self):
        import stat
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            mission = Missionsspeicher.laden(pfad).erstellen(
                name="Gesichert", suche="Preis", jetzt=JETZT)
            self.assertEqual(stat.S_IMODE(pfad.stat().st_mode), 0o600)
            self.assertEqual(Missionsspeicher.laden(pfad).alle()[0].id, mission.id)

    def test_missionslauf_sperre_blockiert_andere_prozesse(self):
        if os.name != "posix":
            self.skipTest("flock-/dirfd-Prozesssperre erfordert POSIX")
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            context = multiprocessing.get_context("fork")
            result_queue = context.Queue()
            with sicherer_speicher.missionslauf_sperre(pfad, "mission-123") as erworben:
                self.assertTrue(erworben)
                process = context.Process(
                    target=_prozess_missionslauf_sperren,
                    args=(str(pfad), "mission-123", result_queue))
                process.start()
                process.join(timeout=5)
                self.assertFalse(process.is_alive())
                self.assertEqual(process.exitcode, 0)
                self.assertFalse(result_queue.get(timeout=2))
            with sicherer_speicher.missionslauf_sperre(pfad, "mission-123") as danach:
                self.assertTrue(danach)

    def test_missionslauf_sperre_verweigert_symlink_und_hardlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            pfad = root / "missionen.json"
            lock = root / (".schnapper-run-" + hashlib.sha256(b"mission-123").hexdigest() + ".lock")
            target = root / "target"
            target.write_text("unchanged", encoding="utf-8")
            lock.symlink_to(target)
            with self.assertRaises(OSError):
                with sicherer_speicher.missionslauf_sperre(pfad, "mission-123"):
                    self.fail("Symlink-Sperre wurde akzeptiert")
            self.assertEqual(target.read_text(encoding="utf-8"), "unchanged")

            lock.unlink()
            lock.hardlink_to(target)
            with self.assertRaises(OSError):
                with sicherer_speicher.missionslauf_sperre(pfad, "mission-123"):
                    self.fail("Hardlink-Sperre wurde akzeptiert")

    def test_verzeichnisaustausch_waehrend_schreiben_beruehrt_aussen_nicht(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            data_dir = root / "state"
            data_dir.mkdir()
            outside = root / "outside"
            outside.mkdir()
            marker = outside / "missionen.json"
            marker.write_text("unchanged", encoding="utf-8")
            store = Missionsspeicher.laden(data_dir / "missionen.json")
            moved = root / "state-original"
            real_replace = os.replace
            exchanged = False

            def exchange(source, destination, *args, **kwargs):
                nonlocal exchanged
                if not exchanged:
                    exchanged = True
                    data_dir.rename(moved)
                    data_dir.symlink_to(outside, target_is_directory=True)
                return real_replace(source, destination, *args, **kwargs)

            with mock.patch.object(sicherer_speicher.os, "replace", side_effect=exchange):
                with self.assertRaises(MissionsFehler):
                    store.erstellen(name="Kamera", suche="Kamera", jetzt=JETZT)
            self.assertTrue(exchanged)
            self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged")
            self.assertEqual(len(json.loads((moved / "missionen.json").read_text())["missionen"]), 1)


class BlitzKonflikte(unittest.TestCase):
    def test_gleichzeitige_deduplizierung_meldet_einmal_und_keinen_stillverlust(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "blitz.json")
            links, rechts = Blitz.laden(pfad), Blitz.laden(pfad)
            barrier = threading.Barrier(2)

            def pruefen(blitz):
                barrier.wait(timeout=5)
                try:
                    return ("gespeichert", blitz.pruefen(_angebot(), [_wunsch()], JETZT))
                except BlitzKonflikt:
                    return ("konflikt", [])

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(pruefen, (links, rechts)))
            self.assertEqual(sum(len(meldungen) for _status, meldungen in results), 1)
            self.assertEqual(sum(status == "konflikt" for status, _meldungen in results), 1)

            frisch = Blitz.laden(pfad)
            self.assertEqual(len(frisch), 1)
            # Wiederholung nach Neustart wird sicher unterdrückt.
            self.assertEqual(frisch.pruefen(_angebot(), [_wunsch()], JETZT), [])

    def test_sechs_vorgeladene_instanz_duplizieren_treffer_nicht(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "blitz.json")
            queues = [Blitz.laden(pfad) for _ in range(6)]
            barrier = threading.Barrier(len(queues))

            def pruefen(queue):
                barrier.wait(timeout=10)
                try:
                    return ("gespeichert", queue.pruefen(_angebot(), [_wunsch()], JETZT))
                except BlitzKonflikt:
                    return ("konflikt", [])

            with ThreadPoolExecutor(max_workers=len(queues)) as pool:
                results = list(pool.map(pruefen, queues))
            self.assertEqual(sum(len(messages) for _status, messages in results), 1)
            self.assertEqual(sum(status == "konflikt" for status, _messages in results), 5)
            self.assertEqual(len(Blitz.laden(pfad)), 1)

    def test_blitz_symlink_im_uebergeordneten_ordner_blockiert(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            outside = root / "outside"
            outside.mkdir()
            link = root / "linked"
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(BlitzFehler):
                Blitz.laden(link / "blitz.json")

    def test_blitz_leaf_und_speicherlock_symlink_werden_abgewiesen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            target = root / "target"
            target.write_text("UNVERAENDERT", encoding="utf-8")
            pfad = root / "blitz.json"
            pfad.symlink_to(target)
            with self.assertRaises(BlitzFehler):
                Blitz.laden(pfad)
            self.assertEqual(target.read_text(encoding="utf-8"), "UNVERAENDERT")

            pfad.unlink()
            (root / ".schnapper-storage.lock").unlink()
            (root / ".schnapper-storage.lock").symlink_to(target)
            with self.assertRaises(BlitzFehler):
                Blitz.laden(pfad)
            self.assertEqual(target.read_text(encoding="utf-8"), "UNVERAENDERT")

    def test_blitz_beschaedigung_nach_laden_bleibt_unveraendert(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "blitz.json")
            blitz = Blitz.laden(pfad)
            blitz.pruefen(_angebot(), [_wunsch()], JETZT)
            pfad.write_bytes(b"{kaputt")
            with self.assertRaises(BlitzFehler):
                blitz.pruefen(_angebot(), [_wunsch()], JETZT)
            self.assertEqual(pfad.read_bytes(), b"{kaputt")

    def test_blitz_private_datei_ueberlebt_neustart(self):
        import stat
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "blitz.json")
            blitz = Blitz.laden(pfad)
            self.assertEqual(len(blitz.pruefen(_angebot(), [_wunsch()], JETZT)), 1)
            self.assertEqual(stat.S_IMODE(pfad.stat().st_mode), 0o600)
            self.assertEqual(len(Blitz.laden(pfad)), 1)

    def test_blitz_verzeichnisaustausch_waehrend_schreiben_beruehrt_aussen_nicht(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            data_dir = root / "state"
            data_dir.mkdir()
            outside = root / "outside"
            outside.mkdir()
            marker = outside / "blitz.json"
            marker.write_text("unchanged", encoding="utf-8")
            store = Blitz.laden(data_dir / "blitz.json")
            moved = root / "state-original"
            real_replace = os.replace
            exchanged = False

            def exchange(source, destination, *args, **kwargs):
                nonlocal exchanged
                if not exchanged:
                    exchanged = True
                    data_dir.rename(moved)
                    data_dir.symlink_to(outside, target_is_directory=True)
                return real_replace(source, destination, *args, **kwargs)

            with mock.patch.object(sicherer_speicher.os, "replace", side_effect=exchange):
                with self.assertRaises(BlitzFehler):
                    store.pruefen(_angebot(), [_wunsch()], JETZT)
            self.assertTrue(exchanged)
            self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged")


if __name__ == "__main__":
    unittest.main()
