import hashlib
from pathlib import Path
import cv2
from PIL import Image, ImageOps


def create_thumbnail(path, kind, directory):
    path, directory = Path(path), Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (hashlib.sha256(str(path.resolve()).encode('utf-8')).hexdigest() + '.jpg')
    if kind == 'image':
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert('RGB')
    else:
        video = cv2.VideoCapture(str(path))
        try:
            ok, frame = video.read()
            if not ok:
                raise ValueError('无法读取视频画面')
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        finally:
            video.release()
    image.thumbnail((256, 256))
    image.save(target, 'JPEG', quality=85)
    return str(target)
