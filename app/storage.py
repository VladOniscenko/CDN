import os
import shutil
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path(os.environ.get('STORAGE_ROOT', '/data'))
BASE_DIR.mkdir(parents=True, exist_ok=True)


def safe_join(*parts: str) -> Path:
    p = BASE_DIR.joinpath(*parts).resolve()
    if not str(p).startswith(str(BASE_DIR.resolve())):
        raise ValueError("Invalid path")
    return p


def list_dir(rel_path: str = '') -> Tuple[List[dict], List[dict]]:
    p = safe_join(rel_path) if rel_path else BASE_DIR
    dirs, files = [], []
    if not p.exists():
        return dirs, files
    for child in sorted(p.iterdir()):
        rel = str(child.relative_to(BASE_DIR)).replace('\\', '/')
        if child.is_dir():
            dirs.append({'name': child.name, 'path': rel})
        else:
            files.append({'name': child.name, 'path': rel, 'size': child.stat().st_size})
    return dirs, files


def make_dir(rel_path: str):
    p = safe_join(rel_path)
    p.mkdir(parents=True, exist_ok=True)


def save_file(rel_dir: str, filename: str, file_obj):
    """Sla bestand op in de gegeven submap."""
    pdir = safe_join(rel_dir) if rel_dir else BASE_DIR
    pdir.mkdir(parents=True, exist_ok=True)
    dest = pdir.joinpath(filename)
    with open(dest, 'wb') as f:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b''):
            f.write(chunk)
    return str(dest.relative_to(BASE_DIR)).replace('\\', '/')


def delete_path(rel_path: str):
    p = safe_join(rel_path)
    if p == BASE_DIR:
        raise ValueError("Cannot delete base directory")
    if p.exists():
        if p.is_dir():
            shutil.rmtree(p)
            return True
        elif p.is_file():
            p.unlink()
            return True
    return False
