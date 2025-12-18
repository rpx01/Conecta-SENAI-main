from pathlib import Path


def ensure_path_is_safe(path: Path) -> bool:
    return ".." not in path.parts
