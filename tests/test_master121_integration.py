"""Master 121: ensure all real local-KI entry points fail closed, offline."""
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
from ki import KINichtVerfuegbar
import local_ollama as ollama
import local_service as service


class TestMaster121Integration(unittest.TestCase):
    def test_direct_chat_http_denied_before_network(self):
        with mock.patch.object(ollama, "pruefe_freigabe",
                               side_effect=KINichtVerfuegbar("not approved")), \
             mock.patch.object(ollama._HTTP, "open") as network:
            with self.assertRaises(KINichtVerfuegbar):
                ollama._request("/api/chat", {"messages": []})
            network.assert_not_called()

    def test_backend_env_does_not_start_local_ki_without_approval(self):
        with mock.patch.dict("os.environ", {"SCHNAPPER_KI_BACKEND": "ollama"}), \
             mock.patch.object(ollama, "pruefe_freigabe",
                               side_effect=KINichtVerfuegbar("not approved")), \
             mock.patch.object(ollama._HTTP, "open") as network:
            with self.assertRaises(KINichtVerfuegbar):
                ollama.KI("/tmp/no-model-calls")
            network.assert_not_called()

    def test_service_does_not_launch_agent_without_approval(self):
        with mock.patch.object(service, "gestoppt", return_value=False), \
             mock.patch.object(service, "pruefe_freigabe",
                               side_effect=KINichtVerfuegbar("not approved")), \
             mock.patch.object(service.subprocess, "run") as spawn:
            self.assertEqual(service.einmal(), 2)
            spawn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
