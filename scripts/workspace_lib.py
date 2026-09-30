"""Small file-based primitives for private writing workspaces (Python 3.9+)."""
import hashlib
import json
import os
import tempfile
import fcntl
from contextlib import contextmanager
from functools import wraps
from pathlib import Path


@contextmanager
def write_lock(root):
    """Serialize cooperating workspace writers; fail clearly if another owns it."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.writing.lock').open('a') as lock:
        os.chmod(lock.name, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('Another writer owns this workspace/project; retry after it finishes') from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def locked(function):
    @wraps(function)
    def wrapper(root, *args, **kwargs):
        with write_lock(root):
            return function(Path(root), *args, **kwargs)
    return wrapper


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def scoped_path(root, relative):
    """Reject traversal, absolute paths and symlink escape before reading/writing."""
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Expected a relative path inside the selected workspace')
    result = root / relative
    if not result.resolve().is_relative_to(root):
        raise ValueError('Path escapes selected workspace')
    return result


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def atomic_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_json(path, value):
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def immutable_copy(source, target, expected=None):
    source, target = Path(source), Path(target)
    if source.is_symlink() or not source.is_file():
        raise ValueError('Source must be a regular file')
    before = digest(source)
    if expected and before != expected:
        raise ValueError('Source changed since inventory: ' + str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise ValueError('Immutable target cannot be a symlink')
    try:
        with target.open('xb') as out, source.open('rb') as inp:
            os.chmod(target, 0o600)
            for chunk in iter(lambda: inp.read(1024 * 1024), b''):
                out.write(chunk)
    except FileExistsError:
        if digest(target) != before:
            raise ValueError('Refusing to overwrite a different existing file: ' + str(target))
    if digest(target) != before or digest(source) != before:
        raise ValueError('Copy verification failed: ' + str(source))
    return before
