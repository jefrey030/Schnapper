"""SCHNAPPER: sichere Vorab-Diagnose, OHNE KI-Anfrage und ohne Ausgaben.

Aufruf: python3 team/diagnose_local.py
Prüft nur lokalen Ollama-GET /api/tags; keine Downloads, Modellstarts,
GitHub Actions, Cloud-Anfragen oder Änderungen an der Maschine.
"""
import json
import os
import pathlib
import platform
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ki import KINichtVerfuegbar
from local_ollama import MODELL_DEFAULT, _request


def diagnose():
    checks = []
    def pruefe(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    py_ok = sys.version_info >= (3, 11)
    pruefe("Python 3.11+", py_ok, platform.python_version())
    pruefe("Git", shutil.which("git") is not None,
           shutil.which("git") or "Git ist nicht installiert.")
    os_name = platform.system()
    os_version = platform.mac_ver()[0] if os_name == "Darwin" else platform.release()
    pruefe("Betriebssystem", True, f"{os_name} {os_version}")

    # macOS 14 ist die Mindestanforderung des aktuellen Ollama für Mac.
    # Das MacBook Mid 2012 bekommt Sonoma nicht regulär von Apple.
    mac_ok = True
    if os_name == "Darwin":
        try:
            mac_ok = int(os_version.split(".")[0]) >= 14
        except (ValueError, IndexError):
            mac_ok = False
        pruefe("Ollama-kompatibles macOS", mac_ok,
               "Benötigt macOS 14+; altes macOS nicht überschreiben.")

    installed = shutil.which("ollama")
    pruefe("Ollama-Programm", bool(installed),
           installed or "Fehlt: ollama.com/download (nur kompatible Betriebssysteme)")
    name = os.environ.get("SCHNAPPER_OLLAMA_MODELL", MODELL_DEFAULT).strip()
    if not name or name.lower().endswith(":cloud"):
        pruefe("Nur lokales Modell", False, "Cloud-Modelle ausdrücklich verboten.")
    else:
        pruefe("Nur lokales Modell", True, name)
    modell_installiert = False
    if installed and mac_ok and name and not name.lower().endswith(":cloud"):
        try:
            katalog = _request("/api/tags", timeout=3)
            modelle = [x.get("name") for x in katalog.get("models", [])
                       if isinstance(x, dict)]
            modell_installiert = name in modelle
            pruefe("Ollama-Dienst erreichbar", True, "127.0.0.1:11434")
            pruefe("Modell bereits lokal installiert", modell_installiert,
                   name if modell_installiert else
                   f"{name} fehlt. Bei Bedarf bewusst: ollama pull {name}")
        except (KINichtVerfuegbar, AttributeError, TypeError) as exc:
            pruefe("Ollama-Dienst erreichbar", False,
                   "Lokaler Ollama-Server nicht erreichbar; App starten / ollama serve.")
            pruefe("Modell bereits lokal installiert", False, "Nicht prüfbar.")
    else:
        pruefe("Ollama-Dienst erreichbar", False, "Ohne passende lokale Installation.")
        pruefe("Modell bereits lokal installiert", False, "Nicht prüfbar.")
    return {
        "projekt": "SCHNAPPER", "phase": "VORABDIAGNOSE",
        "modell_angerufen": False, "bezahl_api_genutzt": False,
        "startbereit": all(c["ok"] for c in checks),
        "checks": checks,
    }


def main():
    ergebnis = diagnose()
    print(json.dumps(ergebnis, ensure_ascii=False, indent=2))
    return 0 if ergebnis["startbereit"] else 1


if __name__ == "__main__":
    sys.exit(main())
