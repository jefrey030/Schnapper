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
    finally:
        os.close(fd)


def write_text(path, text, encoding='utf-8'):
    with parent_fd(path, create=True) as (directory, name):
        temporary = '.artifact-' + uuid.uuid4().hex
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory)
        try:
            with os.fdopen(fd, 'w', encoding=encoding) as output:
                output.write(text)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
        finally:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass


def read_text(path, limit=128_000):
    with parent_fd(path) as (directory, name):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK |
                     os.O_CLOEXEC, dir_fd=directory)
        with os.fdopen(fd, 'rb') as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise OSError('Regular artifact required')
            raw = source.read(limit + 1)
            if len(raw) > limit:
                raise ValueError('Artifact too large')
            return raw.decode('utf-8')
