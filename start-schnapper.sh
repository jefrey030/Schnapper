#!/usr/bin/env bash
# SCHNAPPER – Ein-Befehl-Start (gedacht für Android/Termux, läuft auch auf Linux/macOS)
#
# Stand 22.10.2026 (F5 / S-012): am Computer geprüft, auf echtem Gerät ungetestet
# (auf einem echten Android-Gerät noch nicht getestet).
#
# Aufruf (aus dem entpackten SCHNAPPER-Ordner oder von überall mit Pfad):
#   bash start-schnapper.sh                 -> nimmt app/vorlagen/meine-angebote.csv
#   bash start-schnapper.sh DATEI           -> nimmt DATEI (relativ zum Aufrufort oder absolut)
#   SCHNAPPER_PORT=8800 bash start-schnapper.sh   -> anderer Port (Standard 8765)
#   SCHNAPPER_PYTHON=/pfad/zu/python bash start-schnapper.sh -> bestimmter Interpreter
#
# Verhalten:
#   - Höchstens ein Argument (die Datei). Weitere Argumente -> Fehlermeldung, Exit 2.
#   - Fehlt die Datei oder ist sie keine normale Datei -> Fehlermeldung, Exit 2, kein Start.
#   - Der Server lauscht immer nur auf 127.0.0.1 (nur dieses Gerät). Das ist hier fest.
#   - Port muss eine ganze Zahl von 1 bis 65535 sein, sonst Exit 2.
#   - Python 3.8 oder neuer nötig (python3 bevorzugt, sonst python), sonst Exit 2.
#   - Lädt nichts herunter, installiert nichts. Beenden mit Strg+C.
#   - Nutzt nur bash-Befehle und Python (keine weiteren Programme).
#   - Start mit sh/dash (statt bash) -> Hinweis "Bitte mit bash starten", Exit 2.

# Nur mit bash lauffähig (BASH_SOURCE, 10#). Bei sh/dash/zsh verständlich abbrechen.
if [ -z "${BASH_VERSION:-}" ]; then
    printf '%s\n' "Bitte mit bash starten: bash start-schnapper.sh" >&2
    exit 2
fi
set -eu

fehler() {
    printf '%s\n' "$*" >&2
    exit 2
}

AUFRUF_DIR=$PWD

# Eigenes Verzeichnis ermitteln (nur Builtins).
QUELLE=${BASH_SOURCE[0]}
case "$QUELLE" in
    */*) SKRIPT_DIR=${QUELLE%/*} ;;
    *) SKRIPT_DIR=. ;;
esac
SKRIPT_DIR=$(CDPATH= cd -- "$SKRIPT_DIR" && pwd)

# Argumente prüfen.
if [ "$#" -gt 1 ]; then
    fehler "Zu viele Argumente. Aufruf: bash start-schnapper.sh [DATEI]"
fi
if [ "$#" -eq 1 ]; then
    case "$1" in
        /*) DATEI=$1 ;;
        *) DATEI=$AUFRUF_DIR/$1 ;;
    esac
else
    DATEI=$SKRIPT_DIR/app/vorlagen/meine-angebote.csv
fi
if [ ! -f "$DATEI" ]; then
    fehler "Datei nicht gefunden: $DATEI"
fi

# Port prüfen (nur Ziffern, 1 bis 65535).
PORT=${SCHNAPPER_PORT:-8765}
case "$PORT" in
    ''|*[!0-9]*) fehler "Ungültiger Port in SCHNAPPER_PORT: '$PORT' (erlaubt: ganze Zahl 1 bis 65535)" ;;
esac
if [ "${#PORT}" -gt 5 ]; then
    fehler "Ungültiger Port in SCHNAPPER_PORT: '$PORT' (erlaubt: ganze Zahl 1 bis 65535)"
fi
PORT=$((10#$PORT))
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    fehler "Ungültiger Port in SCHNAPPER_PORT: '$PORT' (erlaubt: ganze Zahl 1 bis 65535)"
fi

# Python suchen.
PY=
if [ -n "${SCHNAPPER_PYTHON:-}" ]; then
    PY=$(command -v -- "$SCHNAPPER_PYTHON" || true)
    if [ -z "$PY" ]; then
        fehler "Python nicht gefunden: SCHNAPPER_PYTHON='$SCHNAPPER_PYTHON' ist nicht ausführbar."
    fi
else
    PY=$(command -v python3 || command -v python || true)
fi
if [ -z "$PY" ]; then
    printf '%s\n' "Python wurde nicht gefunden. SCHNAPPER braucht Python 3.8 oder neuer." >&2
    printf '%s\n' "In Termux installieren mit:  pkg install python" >&2
    exit 2
fi
if ! "$PY" -c 'import sys; sys.exit(sys.version_info < (3, 8))' 2>/dev/null; then
    printf '%s\n' "Python ist zu alt ($PY). SCHNAPPER braucht Python 3.8 oder neuer." >&2
    printf '%s\n' "In Termux aktualisieren mit:  pkg install python" >&2
    exit 2
fi

cd -- "$SKRIPT_DIR"
if [ -n "${PYTHONPATH:-}" ]; then
    export PYTHONPATH="$SKRIPT_DIR/app:$PYTHONPATH"
else
    export PYTHONPATH="$SKRIPT_DIR/app"
fi
export PYTHONUNBUFFERED=1

printf '%s\n' "SCHNAPPER startet: http://127.0.0.1:$PORT – in Chrome öffnen. Beenden: Strg+C"
printf '%s\n' "Datei: $DATEI"

exec "$PY" -u -m schnapper.web "$DATEI" --host 127.0.0.1 --port "$PORT"
