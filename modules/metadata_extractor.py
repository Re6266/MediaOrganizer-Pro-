from datetime import datetime
from pathlib import Path
import json
import shutil
import subprocess
import sys
import cv2
from PIL import Image


def extract_video_dates(path):
    """Return explicitly labelled recording time and separate creation metadata."""
    executable = shutil.which("ffprobe")
    if not executable:
        try:
            try:
                from pymediainfo import MediaInfo
            except ImportError:
                sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '.local_dependencies'))
                from pymediainfo import MediaInfo
            media = MediaInfo.parse(str(path))
            tracks = [t for t in media.tracks if t.track_type in ('General', 'Video')]
            if not tracks:
                return {"video_date_status": "probe_failed"}

            def read_date(name):
                for track in tracks:
                    value = getattr(track, name, None)
                    if not isinstance(value, str):
                        continue
                    value = value.strip()
                    if value.startswith('UTC '):
                        value = value[4:] + '+00:00'
                    try:
                        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        if date.year >= 1970:
                            return date.isoformat(sep=' ', timespec='seconds')
                    except ValueError:
                        continue
                return None

            return {"video_date_status": "read", "capture_time": read_date('recorded_date'),
                    "video_creation_time": None}
        except (ImportError, OSError, RuntimeError, ValueError, AttributeError):
            return {"video_date_status": "ffprobe_unavailable"}
    try:
        result = subprocess.run(
            [executable, "-v", "error", "-show_entries", "format_tags:stream=codec_type:stream_tags",
             "-of", "json", str(path)],
            capture_output=True, check=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        metadata = json.loads(result.stdout.decode("utf-8-sig"))
        tags = [metadata.get("format", {}).get("tags", {})]
        tags.extend(stream.get("tags", {}) for stream in metadata.get("streams", [])
                    if stream.get("codec_type") == "video")
        recording = None
        creation = None
        for group in tags:
            for key, value in group.items():
                key = key.lower()
                if not isinstance(value, str):
                    continue
                try:
                    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
                except ValueError:
                    continue
                if parsed.year < 1970:
                    continue
                date = parsed.isoformat(sep=" ", timespec="seconds")
                if key in ("date_recorded", "recording_time", "recording_date"):
                    recording = recording or date
                elif key in ("com.apple.quicktime.creationdate", "creation_time"):
                    creation = creation or date
        return {"video_date_status": "read", "capture_time": recording, "video_creation_time": creation}
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError, AttributeError):
        return {"video_date_status": "probe_failed"}


def extract_metadata(path, kind):
    path = Path(path)
    info = {'file_path': str(path.resolve()), 'file_name': path.name,
            'file_type': kind, 'file_size': path.stat().st_size}
    if kind == 'image':
        with Image.open(path) as image:
            info['width'], info['height'] = image.size
            exif = image.getexif()
            # DateTimeOriginal is capture time; DateTime may be an edit time.
            date = exif.get(36867) or exif.get_ifd(34665).get(36867)
            if date:
                try:
                    info['capture_time'] = datetime.strptime(str(date), '%Y:%m:%d %H:%M:%S').isoformat(' ')
                except ValueError:
                    pass
        with Image.open(path) as image:
            image.verify()
    else:
        video = cv2.VideoCapture(str(path))
        try:
            if not video.isOpened():
                raise ValueError('无法读取视频')
            info['width'] = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            info['height'] = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = video.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                info['duration'] = video.get(cv2.CAP_PROP_FRAME_COUNT) / fps
        finally:
            video.release()
        info.update(extract_video_dates(path))
    return info
