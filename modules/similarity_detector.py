import cv2
import numpy as np
from pathlib import Path


def calculate_phash(image_path):
    """
    使用感知哈希算法计算图片哈希值
    """

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(f"无法读取图片：{image_path}")

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    resized = cv2.resize(
        gray,
        (32, 32)
    )

    resized = np.float32(resized)

    dct = cv2.dct(resized)

    dct_low = dct[:8, :8]

    pixels = dct_low.flatten()[1:]

    median = np.median(pixels)

    bits = pixels > median

    hash_value = 0

    for bit in bits:

        hash_value = (hash_value << 1) | int(bit)

    return format(hash_value, "016x")


def calculate_hash_distance(hash1, hash2):
    """
    计算两个感知哈希之间的汉明距离
    """

    value1 = int(hash1, 16)
    value2 = int(hash2, 16)

    return (value1 ^ value2).bit_count()


def find_similar_images(image_paths, threshold=8):
    """
    查找相似图片

    threshold：汉明距离阈值
    """

    if not 0 <= threshold <= 63:
        raise ValueError("threshold 必须在 0 到 63 之间")

    hash_dict = {}

    errors = []

    for image_path in image_paths:

        try:

            hash_dict[str(image_path)] = calculate_phash(
                image_path
            )

        except (OSError, ValueError, cv2.error) as e:

            errors.append({
                "path": str(image_path),
                "error": str(e)
            })

    paths = list(hash_dict.keys())

    similar_pairs = []

    for i in range(len(paths)):

        for j in range(i + 1, len(paths)):

            path1 = paths[i]
            path2 = paths[j]

            distance = calculate_hash_distance(
                hash_dict[path1],
                hash_dict[path2]
            )

            if distance <= threshold:

                similar_pairs.append({

                    "path1": path1,

                    "path2": path2,

                    "distance": distance

                })

    return {
        "pairs": similar_pairs,
        "hashes": hash_dict,
        "errors": errors
    }


def find_similar_pairs(image_paths, threshold=8):
    """
    兼容原有函数名称
    """

    return find_similar_images(
        image_paths,
        threshold
    )


def scan_similar_images(folder_path, threshold=8):
    """
    扫描指定文件夹中的相似图片
    """

    folder = Path(folder_path)

    if not folder.exists():

        raise FileNotFoundError("文件夹不存在")

    extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp"
    }

    image_paths = [

        str(path)

        for path in folder.rglob("*")

        if path.is_file()
        and path.suffix.lower() in extensions

    ]

    return find_similar_images(
        image_paths,
        threshold
    )