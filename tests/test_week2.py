import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
from PIL import Image

import database
from modules import scanner
from modules import upload_import
from modules import metadata_extractor


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.patches = [patch.object(database, 'DATABASE_PATH', self.root / 'test.db'),
                        patch.object(scanner, 'THUMBNAIL_DIR', self.root / 'thumbs')]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_images_repeat_corruption_and_originals(self):
        sub = self.source / '子目录'
        sub.mkdir()
        original = sub / '照片.JPG'
        exif = Image.Exif()
        exif[36867] = '2025:02:03 04:05:06'
        Image.new('RGB', (60, 40), 'red').save(original, exif=exif)
        Image.new('RGB', (20, 10)).save(self.source / 'plain.png')
        (self.source / 'broken.jpg').write_bytes(b'broken')
        (self.source / 'ignored.txt').write_text('ignored')
        before = hashlib.sha256(original.read_bytes()).digest()
        for _ in range(2):
            result = scanner.scan_folder(self.source)
            self.assertEqual((result['success'], result['failed']), (2, 1))
        rows = [dict(row) for row in database.get_all_media()]
        self.assertEqual(len(rows), 2)
        photo = next(row for row in rows if row['file_name'] == original.name)
        self.assertEqual((photo['width'], photo['height']), (60, 40))
        self.assertEqual(photo['capture_time'], '2025-02-03 04:05:06')
        self.assertIsNone(next(row for row in rows if row['file_name'] == 'plain.png')['capture_time'])
        self.assertEqual(before, hashlib.sha256(original.read_bytes()).digest())
        with database.get_connection() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM media_thumbnails').fetchone()[0], 2)

    def test_video(self):
        path = self.source / 'clip.avi'
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'MJPG'), 10, (64, 48))
        self.assertTrue(writer.isOpened())
        for _ in range(10):
            writer.write(np.zeros((48, 64, 3), dtype=np.uint8))
        writer.release()
        result = scanner.scan_folder(self.source)
        self.assertEqual((result['success'], result['failed']), (1, 0))
        row = database.get_all_media()[0]
        self.assertEqual((row['width'], row['height']), (64, 48))
        self.assertAlmostEqual(row['duration'], 1.0, places=1)

    def test_invalid_directory(self):
        for path in ('', str(self.root / 'missing')):
            with self.assertRaises(ValueError):
                scanner.scan_folder(path)

    def test_folder_selection_can_exclude_a_file_without_deleting_it(self):
        folder = self.source / '子目录'
        folder.mkdir()
        first = self.source / '一.png'
        second = folder / '二.png'
        for path in (first, second):
            Image.new('RGB', (20, 20)).save(path)
        paths, errors = scanner.discover_folder(self.source)
        self.assertFalse(errors)
        self.assertEqual(set(paths), {str(first), str(second)})
        result = scanner.scan_files([path for path in paths if path != str(second)])
        self.assertEqual(result['success'], 1)
        self.assertEqual(database.get_all_media()[0]['file_path'], str(first.resolve()))
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())

    def test_batch_limit_accepts_100_and_rejects_101_before_scanning(self):
        limit = scanner.MAX_SELECTION_FILES
        self.assertEqual(len(scanner.validate_selection_size(str(i) for i in range(limit))), limit)
        with self.assertRaisesRegex(ValueError, "最多选择"):
            scanner.scan_files(str(i) for i in range(limit + 1))
        self.assertFalse(database.DATABASE_PATH.exists())

    def test_folder_limit_includes_subfolders_and_does_not_index_partial_batch(self):
        child = self.source / '子目录'
        child.mkdir()
        for index in range(scanner.MAX_SELECTION_FILES):
            (child / f'{index}.txt').touch()
        paths, errors = scanner.discover_folder(self.source)
        self.assertEqual(len(paths), scanner.MAX_SELECTION_FILES)
        self.assertEqual(errors, [])
        (self.source / 'extra.png').touch()
        with self.assertRaisesRegex(ValueError, "文件夹及子文件夹"):
            scanner.scan_folder(self.source)
        self.assertFalse(database.DATABASE_PATH.exists())

    def test_capture_time_from_exif_subdirectory(self):
        path = self.source / 'camera.jpg'
        exif = Image.Exif()
        exif[34665] = {36867: '2024:08:09 10:11:12'}
        Image.new('RGB', (40, 30)).save(path, exif=exif)
        result = scanner.scan_folder(self.source)
        self.assertEqual(result['success'], 1)
        self.assertEqual(database.get_all_media()[0]['capture_time'], '2024-08-09 10:11:12')

    def test_video_dates_are_distinguished_and_preserved(self):
        path = self.source / 'clip.avi'
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'MJPG'), 10, (64, 48))
        self.assertTrue(writer.isOpened())
        writer.write(np.zeros((48, 64, 3), dtype=np.uint8))
        writer.release()
        payload = {'format': {'tags': {'date_recorded': '2024-08-09T10:11:12+08:00',
                                       'creation_time': '2025-01-02T03:04:05Z'}}, 'streams': []}
        from types import SimpleNamespace
        output = SimpleNamespace(stdout=json.dumps(payload).encode('utf-8'))
        with patch.object(metadata_extractor.shutil, 'which', return_value='ffprobe'), \
                patch.object(metadata_extractor.subprocess, 'run', return_value=output):
            self.assertEqual(scanner.scan_folder(self.source)['success'], 1)
        row = database.get_all_media()[0]
        self.assertEqual(row['capture_time'], '2024-08-09 10:11:12+08:00')
        from contextlib import closing
        with closing(database.get_connection()) as conn:
            date = conn.execute('SELECT creation_time, read_status FROM video_date_metadata').fetchone()
            self.assertEqual(tuple(date), ('2025-01-02 03:04:05+00:00', 'read'))
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '.local_dependencies'))
        import pymediainfo
        with patch.object(metadata_extractor.shutil, 'which', return_value=None), \
                patch.object(pymediainfo.MediaInfo, 'parse', side_effect=OSError('unavailable')):
            self.assertEqual(scanner.scan_folder(self.source)['success'], 1)
        self.assertEqual(database.get_all_media()[0]['capture_time'], '2024-08-09 10:11:12+08:00')

    def test_creation_time_is_not_claimed_as_capture(self):
        from types import SimpleNamespace
        metadata = {'format': {'tags': {'creation_time': '2025-01-02T03:04:05Z'}}, 'streams': []}
        with patch.object(metadata_extractor.shutil, 'which', return_value='ffprobe'), \
                patch.object(metadata_extractor.subprocess, 'run', return_value=SimpleNamespace(stdout=json.dumps(metadata).encode())):
            result = metadata_extractor.extract_video_dates('unused.mp4')
        self.assertIsNone(result['capture_time'])
        self.assertEqual(result['video_creation_time'], '2025-01-02 03:04:05+00:00')

    def test_mediainfo_recorded_date_without_ffprobe(self):
        from types import SimpleNamespace
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '.local_dependencies'))
        import pymediainfo
        track = SimpleNamespace(track_type='General', recorded_date='UTC 2024-08-09 10:11:12')
        with patch.object(metadata_extractor.shutil, 'which', return_value=None), \
                patch.object(pymediainfo.MediaInfo, 'parse', return_value=SimpleNamespace(tracks=[track])):
            result = metadata_extractor.extract_video_dates('unused.mp4')
        self.assertEqual(result['capture_time'], '2024-08-09 10:11:12+00:00')
        self.assertIsNone(result['video_creation_time'])

    def test_uploaded_batches_only_scan_selected_and_ignore_other_types(self):
        class Uploaded(io.BytesIO):
            def __init__(self, name, data):
                super().__init__(data)
                self.name = name

        def image_data(color):
            data = io.BytesIO()
            Image.new('RGB', (32, 24), color).save(data, format='PNG')
            return data.getvalue()

        with patch.object(upload_import, 'DATA_DIR', self.root):
            first = upload_import.import_selected_files([
                Uploaded('one.png', image_data('red')),
                Uploaded('note.txt', b'ignored'),
            ])
            second = upload_import.import_selected_files([Uploaded('two.png', image_data('blue'))])
        self.assertEqual((first['success'], first['failed'], first['ignored']), (1, 0, 1))
        self.assertEqual((second['success'], second['failed']), (1, 0))
        self.assertEqual(len(database.get_all_media()), 2)


if __name__ == '__main__':
    unittest.main()
