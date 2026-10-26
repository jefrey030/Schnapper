"""Sichere POSIX-Dateioperationen für lokalen SCHNAPPER-Status.

Directory FDs sichern jeden Pfadbestandteil gegen Symlink-Folgen ab.
Auf demselben Verzeichnis-FD werden Inhalte atomar ersetzt.
Keine externen Dienste, keine Shell, keine automatischen Hintergrundjobs.
"""
from __future__ import annotations

import contextlib
import os
import pathlib
import stat
import uuid


@contextlib.contextmanager
def verzeichnis(pfad):
    path = pathlib.Path(pfad).absolute()
    if ".." in path.parts or not path.name:
        raise OSError("Ungültiger Speicherpfad")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open("/", flags)
    try:
        for part in path.parts[1:-1]:
            try:
                os.mkdir(part, mode=0o700, dir_fd=fd)
            except FileExistsError:
                pass
            nachfolger = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = nachfolger
        yield fd, path.name
    finally:
        os.close(fd)


def lesen(ordner: int, name: str, maximal: int = 256_000) -> str | None:
    if not name or name in (".", "..") or "/" in name:
        raise OSError("Ungültiger Dateiname")
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK |
                     os.O_CLOEXEC, dir_fd=ordner)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "rb") as eingabe:
        info = os.fstat(eingabe.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise OSError("Nur reguläre private Dateien erlaubt")
        roh = eingabe.read(maximal + 1)
        if len(roh) > maximal:
            raise OSError("Gespeicherte Datei ist zu groß")
        return roh.decode("utf-8")


def schreiben(ordner: int, name: str, inhalt: str):
    if not name or name in (".", "..") or "/" in name:
        raise OSError("Ungültiger Dateiname")
    temporaer = ".schnapper-" + uuid.uuid4().hex
    fd = os.open(temporaer, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                 os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=ordner)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as ausgabe:
            ausgabe.write(inhalt)
            ausgabe.flush()
            os.fsync(ausgabe.fileno())
        os.replace(temporaer, name, src_dir_fd=ordner, dst_dir_fd=ordner)
        os.fsync(ordner)
    finally:
        try:
            os.unlink(temporaer, dir_fd=ordner)
        except FileNotFoundError:
            pass
