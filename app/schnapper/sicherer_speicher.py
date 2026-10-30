"""POSIX-Dateispeicher mit dirfd-Ankern, No-Follow und Prozesssperre."""
from __future__ import annotations

import contextlib
import base64
import binascii
import fcntl
import hashlib
import json
import os
import pathlib
import secrets
import stat


_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
_LOCK_FLAGS = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
_RESTORE_JOURNAL = ".schnapper-restore-journal.json"
_RESTORE_FILES = frozenset({"missionen.json", "blitz.json"})
_MAX_DATEI = 2_000_000
_MAX_JOURNAL = 12_000_000


def _pfad(pfad: pathlib.Path | str) -> pathlib.Path:
    result = pathlib.Path(pfad)
    if not result.is_absolute():
        result = pathlib.Path.cwd() / result
    if ".." in result.parts or not result.name or result.name in (".", ".."):
        raise OSError("Unsicherer Speicherpfad")
    return result


@contextlib.contextmanager
def _eltern_fd(pfad: pathlib.Path | str, *, anlegen: bool):
    result = _pfad(pfad)
    fd = os.open("/", _DIR_FLAGS)
    try:
        for teil in result.parts[1:-1]:
            if anlegen:
                try:
                    os.mkdir(teil, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            neu = os.open(teil, _DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = neu
        yield fd, result.name, result
    finally:
        os.close(fd)


def _benannter_elternordner_ist_gleich(pfad: pathlib.Path, fd: int) -> bool:
    try:
        with _eltern_fd(pfad, anlegen=False) as (aktuell, _name, _pfad):
            a, b = os.fstat(fd), os.fstat(aktuell)
            return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)
    except OSError:
        return False


@contextlib.contextmanager
def dateisperre(pfad: pathlib.Path | str):
    """Sperrt alle SCHNAPPER-Dateioperationen desselben Speicherordners."""
    with _eltern_fd(pfad, anlegen=True) as (directory, name, absolute):
        ordnerinfo = os.fstat(directory)
        if (ordnerinfo.st_uid != os.geteuid() or ordnerinfo.st_mode & 0o022):
            raise OSError("Speicherverzeichnis ist fremd oder für andere Benutzer beschreibbar")
        lock_name = ".schnapper-storage.lock"
        lock_fd = os.open(lock_name, _LOCK_FLAGS, 0o600, dir_fd=directory)
        locked = False
        try:
            info = os.fstat(lock_fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or info.st_uid != os.geteuid() or info.st_mode & 0o077):
                raise OSError("Speichersperre ist keine private reguläre Datei")
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            locked = True
            if not _benannter_elternordner_ist_gleich(absolute, directory):
                raise OSError("Speicherverzeichnis wurde während des Zugriffs ausgetauscht")
            _repariere_wiederherstellung(directory)
            yield directory, name
            if not _benannter_elternordner_ist_gleich(absolute, directory):
                raise OSError("Speicherverzeichnis wurde während des Zugriffs ausgetauscht")
        finally:
            try:
                if locked:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(lock_fd)


@contextlib.contextmanager
def missionslauf_sperre(pfad: pathlib.Path | str, mission_id: str):
    """Nicht blockierende, tab-/prozessübergreifende Sperre pro Mission."""
    if not isinstance(mission_id, str) or not mission_id or len(mission_id) > 200:
        raise ValueError("Ungültige Missions-ID für Lauf-Sperre")
    lock_name = ".schnapper-run-" + hashlib.sha256(mission_id.encode("utf-8")).hexdigest() + ".lock"
    with _eltern_fd(pfad, anlegen=True) as (directory, _name, absolute):
        ordnerinfo = os.fstat(directory)
        if ordnerinfo.st_uid != os.geteuid() or ordnerinfo.st_mode & 0o022:
            raise OSError("Speicherverzeichnis ist fremd oder für andere Benutzer beschreibbar")
        fd = os.open(lock_name, _LOCK_FLAGS, 0o600, dir_fd=directory)
        locked = False
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or info.st_uid != os.geteuid() or info.st_mode & 0o077):
                raise OSError("Missionslauf-Sperre ist keine private reguläre Datei")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except BlockingIOError:
                yield False
                return
            if not _benannter_elternordner_ist_gleich(absolute, directory):
                raise OSError("Speicherverzeichnis wurde während des Zugriffs ausgetauscht")
            yield True
            if not _benannter_elternordner_ist_gleich(absolute, directory):
                raise OSError("Speicherverzeichnis wurde während des Zugriffs ausgetauscht")
        finally:
            try:
                if locked:
                    fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)


def lese_fd(directory: int, name: str, *, limit: int = 2_000_000) -> bytes | None:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(name, flags, dir_fd=directory)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "rb") as quelle:
        info = os.fstat(quelle.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_uid != os.geteuid() or info.st_mode & 0o077
                or info.st_size > limit):
            raise OSError("Speicherdatei ist kein privates, begrenztes reguläres Dokument")
        inhalt = quelle.read(limit + 1)
        if len(inhalt) > limit:
            raise OSError("Speicherdatei überschreitet die zulässige Größe")
        return inhalt


def _kodierte_dateien(files: dict[str, bytes | None]) -> dict[str, str | None]:
    return {name: None if raw is None else base64.b64encode(raw).decode("ascii")
            for name, raw in sorted(files.items())}


def _journal_payload(previous: dict[str, bytes | None], next_files: dict[str, bytes | None]) -> bytes:
    body = {"version": 1, "previous": _kodierte_dateien(previous),
            "next": _kodierte_dateien(next_files)}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    body["sha256"] = hashlib.sha256(canonical).hexdigest()
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(raw) > _MAX_JOURNAL:
        raise OSError("Wiederherstellungsjournal überschreitet die Größenbegrenzung")
    return raw


def _parse_journal(raw: bytes) -> tuple[dict[str, bytes | None], dict[str, bytes | None]]:
    try:
        body = json.loads(raw.decode("utf-8"))
        if (not isinstance(body, dict) or set(body) != {"version", "previous", "next", "sha256"}
                or type(body["version"]) is not int or body["version"] != 1
                or not isinstance(body["previous"], dict)
                or not isinstance(body["next"], dict)
                or set(body["previous"]) != _RESTORE_FILES
                or set(body["next"]) != _RESTORE_FILES):
            raise ValueError("Ungültige Journalstruktur")
        checksum = body["sha256"]
        unsigned = {"version": body["version"], "previous": body["previous"], "next": body["next"]}
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if not isinstance(checksum, str) or not hashlib.sha256(canonical).hexdigest() == checksum:
            raise ValueError("Journalprüfsumme stimmt nicht")
        decoded = []
        for dateien in (body["previous"], body["next"]):
            result = {}
            for name, encoded in dateien.items():
                if encoded is None:
                    result[name] = None
                    continue
                if not isinstance(encoded, str):
                    raise ValueError("Ungültiger Journalinhalt")
                data = base64.b64decode(encoded, validate=True)
                if len(data) > _MAX_DATEI:
                    raise ValueError("Journaldatei überschreitet die Größenbegrenzung")
                result[name] = data
            decoded.append(result)
        return decoded[0], decoded[1]
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise OSError("Wiederherstellungsjournal ist beschädigt; Zugriff gesperrt") from exc


def _repariere_wiederherstellung(directory: int) -> None:
    journal = lese_fd(directory, _RESTORE_JOURNAL, limit=_MAX_JOURNAL)
    if journal is None:
        return
    previous, _next_files = _parse_journal(journal)
    # Eine unvollständige Wiederherstellung wird zurückgerollt, nie still
    # fortgesetzt: Der Restore kann nach Prüfung durch den Benutzer erneut laufen.
    for name in sorted(previous):
        raw = previous[name]
        if raw is None:
            loesche_fd(directory, name)
        else:
            schreibe_fd(directory, name, raw)
    loesche_fd(directory, _RESTORE_JOURNAL)


def dateien_wiederherstellen(pfad: pathlib.Path | str, files: dict[str, bytes | None]) -> None:
    """Wiederherstellt MISSION und BLITZ; abgebrochene Transaktionen rollen zurück."""
    if set(files) != _RESTORE_FILES or any(
            raw is not None and (not isinstance(raw, bytes) or len(raw) > _MAX_DATEI)
            for raw in files.values()):
        raise ValueError("Ungültiger Wiederherstellungsumfang")
    try:
        with dateisperre(pfad) as (directory, _name):
            previous = {name: lese_fd(directory, name) for name in files}
            journal = _journal_payload(previous, files)
            schreibe_fd(directory, _RESTORE_JOURNAL, journal)
            # Alte Bytes sind vor der ersten Änderung dauerhaft journalisiert;
            # bei Unterbrechung rollt der nächste Datei-Zugriff beide Dateien zurück.
            for name in sorted(files):
                raw = files[name]
                if raw is None:
                    loesche_fd(directory, name)
                else:
                    schreibe_fd(directory, name, raw)
            loesche_fd(directory, _RESTORE_JOURNAL)
    except OSError:
        # Ein verbleibendes Journal ist absichtlich der Recovery-Quelle.
        raise


def schreibe_fd(directory: int, name: str, inhalt: bytes) -> None:
    if not isinstance(inhalt, bytes):
        raise TypeError("Speicherinhalt muss bytes sein")
    try:
        ziel = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        ziel = None
    if ziel is not None and not stat.S_ISREG(ziel.st_mode):
        raise OSError("Speicherziel ist keine reguläre Datei")

    temporaer = ".schnapper-tmp-" + secrets.token_hex(16)
    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
             | getattr(os, "O_CLOEXEC", 0))
    fd = os.open(temporaer, flags, 0o600, dir_fd=directory)
    try:
        with os.fdopen(fd, "wb") as ausgabe:
            ausgabe.write(inhalt)
            ausgabe.flush()
            os.fsync(ausgabe.fileno())
        # Der Aufrufer hält dateisperre(); die Umbenennung ist auf den bereits
        # verankerten Verzeichnisdeskriptor beschränkt und folgt keinem Link.
        os.replace(temporaer, name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    except BaseException:
        try:
            os.unlink(temporaer, dir_fd=directory)
        except FileNotFoundError:
            pass
        raise


def loesche_fd(directory: int, name: str) -> None:
    try:
        os.unlink(name, dir_fd=directory)
        os.fsync(directory)
    except FileNotFoundError:
        pass


def digest(inhalt: bytes | None) -> str | None:
    return None if inhalt is None else hashlib.sha256(inhalt).hexdigest()
