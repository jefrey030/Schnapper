"""MASTER 86: PR90-Ollama-Proofs in MASTER85-Sicherheitskette integrieren.

Alle Rollen- und API-Antworten sind synthetische Offline-Fixtures.
"""
import copy
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_master77_proof import TestMaster77Nachweise
from test_local_ollama import gueltige_antwort

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import local_ollama as lokal
import local_service as dienst
from ki import KINichtVerfuegbar


class TestMaster86IntegrierteNachweise(unittest.TestCase):
    def setUp(self):
        fixture = TestMaster77Nachweise("test_mock_is_consistent_but_not_a_live_ai_proof")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture

    def _proof_changed(self, rolle, modifier):
        entry = self.fixture.report["agenten"][rolle]
        modifier(entry["ki"])
        (self.fixture.lauf / (rolle + ".json")).write_text(
            json.dumps(entry, ensure_ascii=False), encoding="utf-8")
        return dienst.pruefe_nachweise(
            self.fixture.report, self.fixture.lauf, self.fixture.steps)

    def test_positive_offline_report_accepted_for_format_only(self):
        self.assertEqual(self.fixture.check(), [])

    def test_local_uuid_explicitly_is_not_provider_attestation(self):
        for role in dienst.ROLES:
            self.assertEqual(
                self.fixture.report["agenten"][role]["ki"]["antwort_id_typ"],
                "nur-lokale-kennung")

    def test_missing_type_blocks(self):
        errors = self._proof_changed("LEAD", lambda ki: ki.pop("antwort_id_typ"))
        self.assertTrue(any("lokale Kennung" in e for e in errors), errors)

    def test_wrong_type_blocks(self):
        errors = self._proof_changed(
            "BRAIN", lambda ki: ki.update(antwort_id_typ="provider-attestiert"))
        self.assertTrue(any("lokale Kennung" in e for e in errors), errors)

    def test_missing_ollama_evidence_blocks(self):
        errors = self._proof_changed(
            "CHECK", lambda ki: ki.pop("ollama_beleg"))
        self.assertTrue(any("Abschlussbeleg" in e for e in errors), errors)

    def test_wrong_reported_model_blocks(self):
        errors = self._proof_changed(
            "COMMAND", lambda ki: ki["ollama_beleg"].update(
                modell_antwort="anderes:1b"))
        self.assertTrue(any("Abschlussbeleg" in e for e in errors), errors)

    def test_incomplete_chat_blocks(self):
        errors = self._proof_changed(
            "LEAD", lambda ki: ki["ollama_beleg"].update(done=False))
        self.assertTrue(any("Abschlussbeleg" in e for e in errors), errors)

    def test_length_stop_blocks(self):
        errors = self._proof_changed(
            "BRAIN", lambda ki: ki["ollama_beleg"].update(done_reason="length"))
        self.assertTrue(any("Abschlussbeleg" in e for e in errors), errors)

    def test_wrong_message_role_blocks(self):
        errors = self._proof_changed(
            "CHECK", lambda ki: ki["ollama_beleg"].update(rolle="user"))
        self.assertTrue(any("Abschlussbeleg" in e for e in errors), errors)

    def test_missing_or_naive_timestamp_blocks(self):
        for stamp in (None, "2026-10-25T12:00:00"):
            with self.subTest(stamp=stamp):
                original = copy.deepcopy(
                    self.fixture.report["agenten"]["COMMAND"]["ki"]["ollama_beleg"])
                errors = self._proof_changed(
                    "COMMAND", lambda ki: ki["ollama_beleg"].update(created_at=stamp))
                self.assertTrue(any("Abschlussbeleg" in e for e in errors), errors)
                self.fixture.report["agenten"]["COMMAND"]["ki"]["ollama_beleg"] = original

    def test_zero_eval_tokens_block(self):
        errors = self._proof_changed(
            "LEAD", lambda ki: ki["ollama_beleg"].update(eval_count=0))
        self.assertTrue(any("Abschlussbeleg" in e for e in errors), errors)

    def test_boolean_tokens_block(self):
        errors = self._proof_changed(
            "BRAIN", lambda ki: ki["ollama_beleg"].update(eval_count=True))
        self.assertTrue(any("Abschlussbeleg" in e for e in errors), errors)

    def test_validator_keeps_actual_text_but_does_not_sign_it(self):
        response = gueltige_antwort(model="qwen2.5:1.5b")
        val = lokal._validiere_chat_antwort(response, "qwen2.5:1.5b")
        self.assertEqual(val["text"], "Testtext")
        self.assertEqual(val["modell_antwort"], "qwen2.5:1.5b")
        self.assertEqual(val["eval_count"], 4)
        self.assertNotIn("signature", val)

    def test_validator_missing_ollama_fields_blocks(self):
        response = gueltige_antwort(model="qwen2.5:1.5b")
        response.pop("done")
        with self.assertRaises(KINichtVerfuegbar):
            lokal._validiere_chat_antwort(response, "qwen2.5:1.5b")

    def test_no_return_to_unprotected_counter_implementation(self):
        self.assertTrue(hasattr(lokal, "_hole_zaehlersperre"))
        self.assertEqual(lokal.MAX_SICHERE_AUFRUFE, 6)


if __name__ == "__main__":
    unittest.main()
