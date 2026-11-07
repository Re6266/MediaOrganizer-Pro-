"""Persist browser-selected files locally before indexing them."""
from hashlib import sha256
from pathlib import Path
import re

from config import DATA_DIR, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from modules.scanner import scan_files


def import_selected_files(files):
    destination = DATA_DIR / "imported"
    destination.mkdir(parents=True, exist_ok=True)
    ignored = 0
    paths, errors = [], []
    for item in files:
        try:
            name = item.name.replace("\\", "/").split("/")[-1]
            if Path(name).suffix.lower() not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
                ignored += 1
                continue
            content = item.getbuffer()
            digest = sha256(content).hexdigest()
            safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
            target = destination / (digest + "_" + safe_name)
            if not target.exists():
                target.write_bytes(content)
            paths.append(target)
        except (OSError, ValueError) as exc:
            errors.append(f"{item.name}: {exc}")
    result = scan_files(paths)
    result["ignored"] += ignored
    result["failed"] += len(errors)
    result["errors"].extend(errors)
    return result
