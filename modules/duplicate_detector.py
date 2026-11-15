import hashlib
from collections import defaultdict
from pathlib import Path


def calculate_file_hash(file_path):
    """
    使用 SHA-256 计算文件哈希值
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:

            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def find_duplicate_files(file_paths):
    """
    查找完全重复的文件

    返回：
        groups：重复文件分组
        hashes：每个文件对应的哈希值
        errors：读取失败的文件
    """

    hash_dict = defaultdict(list)

    hashes = {}

    errors = []

    for file_path in file_paths:

        try:

            file_hash = calculate_file_hash(file_path)

            path = str(file_path)

            hash_dict[file_hash].append(path)

            hashes[path] = file_hash

        except (OSError, PermissionError) as e:

            errors.append({
                "path": str(file_path),
                "error": str(e)
            })

            print(f"文件读取失败：{file_path}，原因：{e}")

    duplicate_groups = []

    for file_hash, paths in hash_dict.items():

        if len(paths) > 1:

            duplicate_groups.append({

                "hash": file_hash,

                "files": paths

            })

    return {
        "groups": duplicate_groups,
        "hashes": hashes,
        "errors": errors
    }


def scan_duplicates(folder_path):
    """
    扫描指定文件夹中的完全重复图片
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

    return find_duplicate_files(image_paths)