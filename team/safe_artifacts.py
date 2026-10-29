"""POSIX artifact access: anchored directory FDs, no symlink traversal."""
import contextlib
import os
import pathlib
import stat
import uuid


@contextlib.contextmanager
def parent_fd(path, create=False):
    path = pathlib.Path(path).absolute()
    if '..' in path.parts:
        raise OSError('Parent traversal rejected')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open('/', flags)
    try:
        for part in path.parts[1:-1]:
            if create:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            new = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = new
        yield fd, path.name
        check = os.open('/', flags)
        try:
            for part in path.parts[1:-1]:
                new = os.open(part, flags, dir_fd=check)
                os.close(check)
                check = new
            current, original = os.fstat(check), os.fstat(fd)
            if (current.st_dev, current.st_ino) != (original.st_dev, original.st_ino):
                raise OSError('Artifact parent directory changed during access')
        finally:
            os.close(check)
    finally:
        os.close(fd)


def write_bytes(path, raw):
    with parent_fd(path, create=True) as (directory, name):
        temporary = '.artifact-' + uuid.uuid4().hex
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory)
        try:
            with os.fdopen(fd, 'wb') as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            # Atomic rename replaces the directory entry without following a
            # destination symlink or modifying its target.
            os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass


def create_directory(path, mode=0o700):
    """Create one directory under an anchored, symlink-free parent."""
    with parent_fd(path, create=True) as (directory, name):
        os.mkdir(name, mode=mode, dir_fd=directory)
        created = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW |
                          os.O_CLOEXEC, dir_fd=directory)
        try:
            info = os.fstat(created)
            if not stat.S_ISDIR(info.st_mode):
                raise OSError('Directory creation did not produce a directory')
            os.fsync(directory)
        finally:
            os.close(created)


def write_text(path, text, encoding='utf-8'):
    write_bytes(path, text.encode(encoding))


def read_bytes(path, limit=2_000_000):
    raw, _info = read_bytes_with_stat(path, limit=limit)
    return raw


def read_bytes_with_stat(path, limit=2_000_000):
    with parent_fd(path) as (directory, name):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK |
                     os.O_CLOEXEC, dir_fd=directory)
        with os.fdopen(fd, 'rb') as source:
            info = os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise OSError('Regular artifact required')
            raw = source.read(limit + 1)
            if len(raw) > limit:
                raise ValueError('Artifact too large')
            return raw, info


def entry_exists(path):
    try:
        with parent_fd(path) as (directory, name):
            try:
                os.stat(name, dir_fd=directory, follow_symlinks=False)
                return True
            except FileNotFoundError:
                return False
    except FileNotFoundError:
        # A missing ancestor means the named entry cannot exist.
        return False


def read_text(path, limit=128_000):
    return read_bytes(path, limit=limit).decode('utf-8')
