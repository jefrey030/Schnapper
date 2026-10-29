"""Tests S-012: Ein-Befehl-Start start-schnapper.sh (Android/Termux)."""
import os
import pathlib
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKRIPT = ROOT / "start-schnapper.sh"
DOKU = ROOT / "docs" / "HANDY-START.md"
BEISPIEL = ROOT / "app" / "beispiele" / "angebote.csv"
BASH = shutil.which("bash")
HINWEIS = "auf echtem Gerät ungetestet"


def freier_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def lauscht(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def ohne_schnapper_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("SCHNAPPER_PORT", "SCHNAPPER_PYTHON")}
    env.update(extra)
    return env


@unittest.skipUnless(BASH, "bash nicht verfügbar")
class StartSkriptLauf(unittest.TestCase):
    def starte(self, *args, cwd=None, env_extra=None):
        port = freier_port()
        if cwd is None:
            tmp = tempfile.TemporaryDirectory()
            self.addCleanup(tmp.cleanup)
            cwd = tmp.name
        proc = subprocess.Popen(
            [BASH, str(SKRIPT), *args], cwd=cwd,
            env=ohne_schnapper_env(SCHNAPPER_PORT=str(port), **(env_extra or {})),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        def aufraeumen():
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)
            proc.stdout.close()
            proc.stderr.close()
        self.addCleanup(aufraeumen)
        return proc, port

    def warte_auf_seite(self, proc, port):
        frist = time.monotonic() + 15
        letzter = None
        while time.monotonic() < frist:
            if proc.poll() is not None:
                self.fail("Skript beendet (Exit %s): %s" % (proc.returncode, proc.stderr.read()))
            try:
                with urllib.request.urlopen("http://127.0.0.1:%d/" % port, timeout=2) as r:
                    return r.status, r.read().decode("utf-8")
            except (urllib.error.URLError, ConnectionError, OSError) as e:
                letzter = e
                time.sleep(0.2)
        self.fail("Server nicht erreichbar: %r" % (letzter,))

    def beende(self, proc):
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=10)
        return proc.stdout.read(), proc.stderr.read()

    def test_start_ohne_argument_aus_fremdem_cwd(self):
        proc, port = self.starte()
        status, html = self.warte_auf_seite(proc, port)
        self.assertEqual(status, 200)
        self.assertIn("SCHNAPPER", html)
        out, _ = self.beende(proc)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("http://127.0.0.1:%d" % port, out)
        self.assertIn("SCHNAPPER läuft: http://127.0.0.1:%d" % port, out)
        self.assertIn("meine-angebote.csv", out)
        self.assertFalse(lauscht(port))

    def test_start_mit_datei_argument(self):
        proc, port = self.starte(str(BEISPIEL))
        status, html = self.warte_auf_seite(proc, port)
        self.assertEqual(status, 200)
        self.assertIn("SCHNAPPER", html)
        out, _ = self.beende(proc)
        self.assertIn(str(BEISPIEL), out)
        self.assertNotIn("meine-angebote.csv", out)

    def test_relativer_python_pfad_zum_aufrufort(self):
        for rel in ("bin/python", "./bin/python"):
            with self.subTest(schnapper_python=rel):
                tmp = tempfile.TemporaryDirectory()
                self.addCleanup(tmp.cleanup)
                aufruf = pathlib.Path(tmp.name)
                self.assertNotEqual(aufruf.resolve(), ROOT)
                (aufruf / "bin").mkdir()
                os.symlink(sys.executable, aufruf / "bin" / "python")
                proc, port = self.starte(cwd=str(aufruf),
                                         env_extra={"SCHNAPPER_PYTHON": rel})
                status, html = self.warte_auf_seite(proc, port)
                self.assertEqual(status, 200)
                self.assertIn("SCHNAPPER", html)
                out, err = self.beende(proc)
                self.assertEqual(proc.returncode, 0, err)
                self.assertIn("SCHNAPPER läuft: http://127.0.0.1:%d" % port, out)
                self.assertFalse(lauscht(port))

    def test_fehlende_datei(self):
        port = freier_port()
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([BASH, str(SKRIPT), "/gibt/es/nicht.csv"], cwd=tmp,
                               env=ohne_schnapper_env(SCHNAPPER_PORT=str(port)),
                               capture_output=True, text=True, timeout=15)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("/gibt/es/nicht.csv", r.stderr)
        self.assertIn("Datei nicht gefunden", r.stderr)
        self.assertFalse(lauscht(port))

    def test_relative_datei_zum_aufrufort(self):
        port = freier_port()
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([BASH, str(SKRIPT), "app/beispiele/angebote.csv"], cwd=tmp,
                               env=ohne_schnapper_env(SCHNAPPER_PORT=str(port)),
                               capture_output=True, text=True, timeout=15)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(os.path.join(tmp, "app/beispiele/angebote.csv"), r.stderr)

    def test_zu_viele_argumente(self):
        r = subprocess.run([BASH, str(SKRIPT), str(BEISPIEL), "extra"],
                           env=ohne_schnapper_env(SCHNAPPER_PORT="1"),
                           capture_output=True, text=True, timeout=15)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Zu viele Argumente", r.stderr)

    def test_fehlendes_python(self):
        with tempfile.TemporaryDirectory() as leer:
            r = subprocess.run([BASH, str(SKRIPT)], cwd=leer, env={"PATH": leer},
                               capture_output=True, text=True, timeout=15)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Python", r.stderr)
        self.assertIn("pkg install python", r.stderr)
        self.assertEqual(r.stdout, "")

    def test_falscher_interpreter_wird_abgelehnt(self):
        echo_pfad = "/bin/echo" if os.path.exists("/bin/echo") else shutil.which("echo")
        for interp in ("echo", echo_pfad, "true"):
            if not interp:
                continue
            with self.subTest(interpreter=interp):
                port = freier_port()
                with tempfile.TemporaryDirectory() as tmp:
                    r = subprocess.run([BASH, str(SKRIPT)], cwd=tmp,
                                       env=ohne_schnapper_env(SCHNAPPER_PORT=str(port),
                                                              SCHNAPPER_PYTHON=interp),
                                       capture_output=True, text=True, timeout=15)
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn("Python", r.stderr)
                self.assertIn("3.8", r.stderr)
                self.assertNotIn("SCHNAPPER startet", r.stdout)
                self.assertFalse(lauscht(port))

    def test_ungueltiger_port(self):
        for wert in ("abc", "0", "65536", "-1", "80a", "1234567"):
            with self.subTest(port=wert):
                r = subprocess.run([BASH, str(SKRIPT)],
                                   env=ohne_schnapper_env(SCHNAPPER_PORT=wert),
                                   capture_output=True, text=True, timeout=15)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("Ungültiger Port", r.stderr)
                self.assertNotIn("SCHNAPPER läuft", r.stdout)

    def test_start_mit_sh_meldet_bash(self):
        shell = shutil.which("dash")
        if not shell and os.path.exists("/bin/sh") \
                and os.path.basename(os.path.realpath("/bin/sh")) != "bash":
            shell = "/bin/sh"
        if not shell:
            self.skipTest("keine Nicht-bash-Shell (dash bzw. /bin/sh) vorhanden")
        port = freier_port()
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([shell, str(SKRIPT)], cwd=tmp,
                               env=ohne_schnapper_env(SCHNAPPER_PORT=str(port)),
                               capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("Bitte mit bash starten", r.stderr)
        self.assertIn("bash start-schnapper.sh", r.stderr)
        self.assertNotIn("Bad substitution", r.stderr)
        self.assertEqual(r.stdout, "")
        self.assertFalse(lauscht(port))

    def test_bash_n(self):
        r = subprocess.run([BASH, "-n", str(SKRIPT)], capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 0, r.stderr)


class StartSkriptStatisch(unittest.TestCase):
    def setUp(self):
        self.text = SKRIPT.read_text(encoding="utf-8")

    def test_shebang_und_set(self):
        zeilen = self.text.splitlines()
        self.assertEqual(zeilen[0], "#!/usr/bin/env bash")
        self.assertIn("set -eu", zeilen)

    def test_ausfuehrbar(self):
        self.assertTrue(os.access(SKRIPT, os.X_OK))

    def test_host_fest_127(self):
        self.assertIn("--host 127.0.0.1", self.text)
        self.assertNotIn("0.0.0.0", self.text)
        self.assertNotRegex(self.text, r"--host\s+\"?\$")

    def test_exec_und_unbuffered(self):
        self.assertRegex(self.text, r"(?m)^exec \"\$PY\" .*-m schnapper\.web")
        self.assertIn("PYTHONUNBUFFERED=1", self.text)

    def test_keine_downloads_oder_installation(self):
        verboten = re.compile(r"\b(curl|wget|pip3?|git|apt|apt-get|npm|pkg)\b")
        for nr, zeile in enumerate(self.text.splitlines(), 1):
            s = zeile.strip()
            if s.startswith("#") or s.startswith("printf") or s.startswith("echo") \
                    or s.startswith("fehler "):
                continue
            self.assertIsNone(verboten.search(s), "Zeile %d: %s" % (nr, zeile))

    def test_keine_externen_hilfsprogramme(self):
        code = "\n".join(z for z in self.text.splitlines()
                         if not z.strip().startswith("#"))
        for wort in ("dirname", "readlink", "realpath", "basename", "curl"):
            self.assertNotIn(wort, code)

    def test_hinweis_ungetestet(self):
        self.assertIn(HINWEIS, self.text)
        self.assertIn(HINWEIS, DOKU.read_text(encoding="utf-8"))

    def test_doku_ein_befehl(self):
        doku = DOKU.read_text(encoding="utf-8")
        self.assertIn("bash start-schnapper.sh", doku)
        self.assertIn("SCHNAPPER_PORT=8800 bash start-schnapper.sh", doku)
        self.assertIn("bash start-schnapper.sh app/beispiele/angebote.csv", doku)
        self.assertIn("PYTHONPATH=app python -m schnapper.web", doku)
        self.assertIn("pkg install python unzip", doku)


if __name__ == "__main__":
    unittest.main()
