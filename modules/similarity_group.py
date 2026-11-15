from collections import defaultdict

from database import (
    get_connection,
    create_photo_group,
    add_photo_to_group
)


class UnionFind:

    def __init__(self, items):

        self.parent = {
            item: item for item in items
        }

    def find(self, item):

        if self.parent[item] != item:

            self.parent[item] = self.find(
                self.parent[item]
            )

        return self.parent[item]

    def union(self, a, b):

        root_a = self.find(a)

        root_b = self.find(b)

        if root_a != root_b:

            self.parent[root_b] = root_a


def group_similar_images(similar_pairs):
    """
    使用并查集将相似图片归为一组
    """

    parent = {}

    def find(x):
        if x not in parent:
            parent[x] = x

        if parent[x] != x:
            parent[x] = find(parent[x])

        return parent[x]

    def union(x, y):
        root_x = find(x)
        root_y = find(y)

        if root_x != root_y:
            parent[root_y] = root_x

    # 合并相似图片
    for pair in similar_pairs:

        path1 = pair.get("path1", pair.get("image1"))
        path2 = pair.get("path2", pair.get("image2"))

        if path1 is None or path2 is None:
            continue

        union(path1, path2)

    # 整理分组
    groups = {}

    for item in parent:
        root = find(item)

        if root not in groups:
            groups[root] = []

        groups[root].append(item)

    return [
        group
        for group in groups.values()
        if len(group) >= 2
    ]


def save_groups_to_database(groups, group_type="similar"):
    """
    将相似图片分组结果保存到原有 SQLite 数据库
    """

    saved_count = 0

    for index, group in enumerate(groups, start=1):

        group_name = f"{group_type}_group_{index}"

        group_id = create_photo_group(
            group_name,
            group_type
        )

        for image_path in group:

            with get_connection() as conn:

                row = conn.execute(
                    "SELECT id FROM media WHERE file_path = ?",
                    (str(image_path),)
                ).fetchone()

            if row:

                add_photo_to_group(
                    group_id,
                    row["id"],
                    group_type
                )

        saved_count += 1

    return saved_count