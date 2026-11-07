from pathlib import Path
import os
import sqlite3
from itertools import islice
import cv2
from contextlib import closing
from config import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, THUMBNAIL_DIR
from database import get_connection, init_database
from modules.metadata_extractor import extract_metadata
from modules.thumbnail_generator import create_thumbnail

MAX_SELECTION_FILES = 100


def validate_selection_size(paths):
    """Read at most one item beyond the limit and reject oversized batches."""
    selected = list(islice(iter(paths), MAX_SELECTION_FILES + 1))
    if len(selected) > MAX_SELECTION_FILES:
        raise ValueError(f"一次最多选择 {MAX_SELECTION_FILES} 个文件，请分批选择。")
    return selected


def scan_files(paths):
    """Index explicitly selected media paths, isolating errors per file."""
    paths = validate_selection_size(paths)
    init_database()
    result = {'success': 0, 'failed': 0, 'errors': [], 'ignored': 0}
    with closing(get_connection()) as conn, conn:
        conn.execute('CREATE TABLE IF NOT EXISTS media_thumbnails (media_id INTEGER PRIMARY KEY REFERENCES media(id) ON DELETE CASCADE, thumbnail_path TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS video_date_metadata (media_id INTEGER PRIMARY KEY REFERENCES media(id) ON DELETE CASCADE, creation_time TEXT, read_status TEXT NOT NULL)')
    for raw_path in paths:
        path = Path(raw_path)
        suffix = path.suffix.lower()
        kind = 'image' if suffix in IMAGE_EXTENSIONS else 'video' if suffix in VIDEO_EXTENSIONS else None
        if not kind:
            result['ignored'] += 1
            continue
        try:
            data = extract_metadata(path, kind)
            thumb = create_thumbnail(path, kind, THUMBNAIL_DIR)
            with closing(get_connection()) as conn, conn:
                conn.execute("""INSERT INTO media (file_path,file_name,file_type,file_size,width,height,duration,capture_time)
                    VALUES (:file_path,:file_name,:file_type,:file_size,:width,:height,:duration,:capture_time)
                    ON CONFLICT(file_path) DO UPDATE SET file_name=excluded.file_name,file_type=excluded.file_type,
                    file_size=excluded.file_size,width=excluded.width,height=excluded.height,duration=excluded.duration,
                    capture_time=CASE WHEN :keep_capture=1 THEN media.capture_time ELSE excluded.capture_time END""",
                    {**{'width': None, 'height': None, 'duration': None, 'capture_time': None}, **data,
                     'keep_capture': int(kind == 'video' and data.get('video_date_status') != 'read')})
                media_id = conn.execute('SELECT id FROM media WHERE file_path=?', (data['file_path'],)).fetchone()['id']
                conn.execute('INSERT OR REPLACE INTO media_thumbnails (media_id, thumbnail_path) VALUES (?, ?)', (media_id, thumb))
                if kind == 'video':
                    conn.execute('''INSERT INTO video_date_metadata (media_id, creation_time, read_status) VALUES (?, ?, ?)
                        ON CONFLICT(media_id) DO UPDATE SET
                        creation_time=CASE WHEN excluded.read_status='read' THEN excluded.creation_time ELSE video_date_metadata.creation_time END,
                        read_status=excluded.read_status''',
                                 (media_id, data.get('video_creation_time'), data.get('video_date_status', 'probe_failed')))
            result['success'] += 1
        except (OSError, ValueError, RuntimeError, sqlite3.Error, cv2.error) as exc:
            result['failed'] += 1
            result['errors'].append(f'{path}: {exc}')
    return result


def discover_folder(folder):
    """Collect a folder's files without changing or indexing them."""
    if not str(folder).strip():
        raise ValueError('请输入文件夹路径')
    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        raise ValueError('文件夹不存在或无法访问')
    paths, errors = [], []
    for directory, dirs, files in os.walk(root, onerror=lambda error: errors.append(str(error))):
        dirs[:] = [name for name in dirs if not (Path(directory) / name).resolve().is_relative_to(THUMBNAIL_DIR.resolve())]
        for name in sorted(files, key=str.casefold):
            paths.append(str(Path(directory) / name))
            if len(paths) > MAX_SELECTION_FILES:
                raise ValueError(f"文件夹及子文件夹超过 {MAX_SELECTION_FILES} 个文件，请选择较小的文件夹或分批选择文件。")
    return paths, errors


def scan_folder(folder):
    paths, errors = discover_folder(folder)
    result = scan_files(paths)
    result['failed'] += len(errors)
    result['errors'].extend(errors)
    return result
