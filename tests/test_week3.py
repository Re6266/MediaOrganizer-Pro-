import unittest
import tempfile
import shutil

from pathlib import Path
from PIL import Image, ImageDraw

from modules.duplicate_detector import find_duplicate_files

from modules.similarity_detector import (
    calculate_phash,
    calculate_hash_distance,
    find_similar_pairs
)

from modules.similarity_group import group_similar_images


class TestWeek3(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.mkdtemp()
        self.folder = Path(self.temp_dir)

        # 第一组：完全重复图片
        self.image1 = self.folder / "image1.jpg"
        self.image2 = self.folder / "image2.jpg"

        image = Image.new("RGB", (300, 300), color="red")
        image.save(self.image1)

        shutil.copy(self.image1, self.image2)

        # 第二组：内容相似的图片
        self.image3 = self.folder / "image3.jpg"
        self.image4 = self.folder / "image4.jpg"

        image3 = Image.new("RGB", (300, 300), color="white")
        draw3 = ImageDraw.Draw(image3)
        draw3.rectangle((50, 50, 200, 200), fill="red")
        image3.save(self.image3)

        image4 = Image.new("RGB", (300, 300), color="white")
        draw4 = ImageDraw.Draw(image4)
        draw4.rectangle((55, 50, 205, 200), fill="red")
        image4.save(self.image4)

        # 第三组：另一组完全重复图片
        self.image5 = self.folder / "image5.jpg"
        self.image6 = self.folder / "image6.jpg"

        image5 = Image.new("RGB", (300, 300), color="blue")
        image5.save(self.image5)

        shutil.copy(self.image5, self.image6)

    def tearDown(self):

        shutil.rmtree(self.temp_dir)

    def test_duplicate_detection(self):

        result = find_duplicate_files([
            self.image1,
            self.image2,
            self.image3,
            self.image4,
            self.image5,
            self.image6
        ])

        groups = result["groups"]

        # 两组完全重复图片
        self.assertEqual(len(groups), 2)

        for group in groups:
            self.assertEqual(len(group["files"]), 2)

    def test_phash(self):

        hash1 = calculate_phash(self.image1)
        hash2 = calculate_phash(self.image2)

        distance = calculate_hash_distance(
            hash1,
            hash2
        )

        self.assertEqual(distance, 0)

    def test_similar_detection(self):

        result = find_similar_pairs(
            [
                self.image3,
                self.image4
            ],
            threshold=15
        )

        pairs = result["pairs"]

        self.assertEqual(len(pairs), 1)

        self.assertLessEqual(
            pairs[0]["distance"],
            15
        )

    def test_grouping(self):

        pairs = [
            {
                "path1": "A.jpg",
                "path2": "B.jpg",
                "distance": 2
            },
            {
                "path1": "B.jpg",
                "path2": "C.jpg",
                "distance": 3
            },
            {
                "path1": "D.jpg",
                "path2": "E.jpg",
                "distance": 1
            }
        ]

        groups = group_similar_images(pairs)

        # 两组独立的相似图片组
        self.assertEqual(len(groups), 2)

        group_sizes = sorted(len(group) for group in groups)

        self.assertEqual(group_sizes, [2, 3])


if __name__ == "__main__":

    unittest.main(verbosity=2)