import tempfile
import unittest
from pathlib import Path
from contextlib import closing

import cv2
import numpy as np

import database
from modules import media_library
from modules.detection_storage import ensure_detection_tables, save_detection_results
from modules.duplicate_detector import find_duplicate_files
from modules.similarity_detector import find_similar_images
from modules.similarity_group import group_similar_images


class TestMediaLibrary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_path = database.DATABASE_PATH
        database.DATABASE_PATH = Path(self.temp.name) / "week4.db"
        database.init_database()
        with closing(database.get_connection()) as conn, conn:
            conn.executemany(
                "INSERT INTO media(file_path,file_name,file_type,file_size,capture_time) VALUES (?, ?, ?, ?, ?)",
                [("C:/photos/a.jpg", "a.jpg", "image", 10, "2026-11-01 10:00:00"),
                 ("C:/photos/b.jpg", "b.jpg", "image", 20, "2026-11-02 10:00:00"),
                 ("C:/videos/c.mp4", "c.mp4", "video", 30, "2026-11-03 10:00:00")],
            )

    def tearDown(self):
        database.DATABASE_PATH = self.old_path
        self.temp.cleanup()

    def test_filters_media_by_name_type_and_folder(self):
        self.assertEqual([item["file_name"] for item in media_library.list_media("a")], ["a.jpg"])
        self.assertEqual(len(media_library.list_media(file_type="image")), 2)
        self.assertEqual([item["file_name"] for item in media_library.list_media(folder="videos")], ["c.mp4"])

    def test_create_add_and_remove_manual_group(self):
        group_id = media_library.create_manual_group("旅行", [1, 2])
        self.assertEqual(len(media_library.list_manual_groups()[0]["members"]), 2)
        self.assertEqual(media_library.add_group_members(group_id, [3]), 1)
        self.assertEqual(media_library.remove_group_member(group_id, 2), 1)
        self.assertEqual({item["id"] for item in media_library.list_manual_groups()[0]["members"]}, {1, 3})

    def test_rejects_invalid_group_input(self):
        with self.assertRaises(ValueError):
            media_library.create_manual_group("", [1, 2])
        with self.assertRaises(ValueError):
            media_library.create_manual_group("只有一张", [1])

    def test_reads_saved_detection_candidates(self):
        ensure_detection_tables()
        with closing(database.get_connection()) as conn, conn:
            group_id = conn.execute("INSERT INTO similarity_groups DEFAULT VALUES").lastrowid
            conn.executemany(
                "INSERT INTO similarity_group_items(group_id, media_id, phash) VALUES (?, ?, ?)",
                [(group_id, 1, "aa"), (group_id, 2, "bb")],
            )
        groups = media_library.list_detected_groups()
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["kind"], "视觉相似")
        self.assertEqual({item["id"] for item in groups[0]["members"]}, {1, 2})

    def _write_image(self, name, pixels):
        path = Path(self.temp.name) / name
        cv2.imwrite(str(path), pixels)
        return path

    def test_detection_pipeline_saves_candidates(self):
        base = np.full((48, 48, 3), (10, 120, 200), dtype=np.uint8)
        first = self._write_image("dup_a.jpg", base)
        second = self._write_image("dup_b.jpg", base)
        shifted = base.copy()
        shifted[12:36, 12:36] = (200, 60, 10)
        variant = self._write_image("variant.jpg", shifted)

        with closing(database.get_connection()) as conn, conn:
            conn.executemany(
                "INSERT INTO media(file_path,file_name,file_type,file_size) VALUES (?, ?, ?, ?)",
                [(str(first), first.name, "image", 100),
                 (str(second), second.name, "image", 100),
                 (str(variant), variant.name, "image", 100)],
            )

        paths = [str(first), str(second), str(variant)]
        duplicate_result = find_duplicate_files(paths)
        similarity_result = find_similar_images(paths, threshold=15)
        similar_groups = group_similar_images(similarity_result["pairs"])
        summary = save_detection_results(duplicate_result, similarity_result, similar_groups)

        self.assertEqual(summary["duplicate_groups"], 2)
        duplicate_groups = [
            group for group in media_library.list_detected_groups() if group["kind"] == "完全重复"
        ]
        self.assertEqual(len(duplicate_groups), 1)
        self.assertEqual(
            {member["file_name"] for member in duplicate_groups[0]["members"]},
            {"dup_a.jpg", "dup_b.jpg"},
        )


if __name__ == "__main__":
    unittest.main()
