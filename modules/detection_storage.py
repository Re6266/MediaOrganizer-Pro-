"""将第三周检测结果保存到现有 SQLite 媒体库。"""

from contextlib import closing
from database import get_connection, init_database


def ensure_detection_tables():
    """创建重复检测和相似检测所需的数据表。"""
    init_database()

    with closing(get_connection()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS duplicate_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS duplicate_group_items (
                group_id INTEGER NOT NULL REFERENCES duplicate_groups(id)
                    ON DELETE CASCADE,
                media_id INTEGER NOT NULL REFERENCES media(id)
                    ON DELETE CASCADE,
                PRIMARY KEY(group_id, media_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS similarity_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS similarity_group_items (
                group_id INTEGER NOT NULL REFERENCES similarity_groups(id)
                    ON DELETE CASCADE,
                media_id INTEGER NOT NULL REFERENCES media(id)
                    ON DELETE CASCADE,
                phash TEXT,
                PRIMARY KEY(group_id, media_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS similarity_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id_1 INTEGER NOT NULL REFERENCES media(id)
                    ON DELETE CASCADE,
                media_id_2 INTEGER NOT NULL REFERENCES media(id)
                    ON DELETE CASCADE,
                distance INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(media_id_1, media_id_2)
            )
        """)


def save_detection_results(
        duplicate_result,
        similarity_result,
        similarity_groups
):
    """
    保存完全重复检测、相似图片检测和分组结果。

    注意：图片必须已经存在于 media 表中。
    """

    ensure_detection_tables()

    with closing(get_connection()) as conn, conn:

        # 建立图片路径与数据库 ID 的对应关系
        path_to_id = {
            row["file_path"]: row["id"]
            for row in conn.execute(
                "SELECT id, file_path FROM media WHERE file_type='image'"
            )
        }

        # 清除上一次检测结果
        conn.execute("DELETE FROM duplicate_group_items")
        conn.execute("DELETE FROM duplicate_groups")

        conn.execute("DELETE FROM similarity_group_items")
        conn.execute("DELETE FROM similarity_groups")
        conn.execute("DELETE FROM similarity_pairs")

        # 1. 保存 SHA-256 哈希值
        for path, file_hash in duplicate_result.get("hashes", {}).items():

            media_id = path_to_id.get(path)

            if media_id is not None:
                conn.execute(
                    "UPDATE media SET file_hash=? WHERE id=?",
                    (file_hash, media_id)
                )

        # 2. 保存完全重复图片组
        duplicate_count = 0

        for group in duplicate_result.get("groups", []):

            member_ids = [
                path_to_id[path]
                for path in group["files"]
                if path in path_to_id
            ]

            if len(member_ids) < 2:
                continue

            cursor = conn.execute(
                "INSERT INTO duplicate_groups(file_hash) VALUES (?)",
                (group["hash"],)
            )

            group_id = cursor.lastrowid

            conn.executemany(
                """
                INSERT OR IGNORE INTO duplicate_group_items
                (group_id, media_id)
                VALUES (?, ?)
                """,
                [
                    (group_id, media_id)
                    for media_id in member_ids
                ]
            )

            duplicate_count += len(member_ids)

        # 3. 保存 pHash 哈希值，并清除旧的相似分组标记
        for path, phash in similarity_result.get("hashes", {}).items():

            media_id = path_to_id.get(path)

            if media_id is not None:
                conn.execute(
                    "UPDATE media SET similarity_group=NULL WHERE id=?",
                    (media_id,)
                )

        # 4. 保存相似图片对及汉明距离
        pair_count = 0

        for pair in similarity_result.get("pairs", []):

            id1 = path_to_id.get(pair["path1"])
            id2 = path_to_id.get(pair["path2"])

            if id1 is None or id2 is None:
                continue

            a, b = sorted((id1, id2))

            conn.execute(
                """
                INSERT OR IGNORE INTO similarity_pairs
                (media_id_1, media_id_2, distance)
                VALUES (?, ?, ?)
                """,
                (a, b, pair["distance"])
            )

            pair_count += 1

        # 5. 保存相似图片分组
        for group in similarity_groups:

            member_ids = [
                path_to_id[path]
                for path in group
                if path in path_to_id
            ]

            if len(member_ids) < 2:
                continue

            cursor = conn.execute(
                "INSERT INTO similarity_groups DEFAULT VALUES"
            )

            group_id = cursor.lastrowid

            # 保存分组成员及其 pHash
            for path in group:

                media_id = path_to_id.get(path)

                if media_id is None:
                    continue

                phash = similarity_result.get(
                    "hashes", {}
                ).get(path)

                conn.execute(
                    """
                    INSERT OR IGNORE INTO similarity_group_items
                    (group_id, media_id, phash)
                    VALUES (?, ?, ?)
                    """,
                    (group_id, media_id, phash)
                )

                conn.execute(
                    "UPDATE media SET similarity_group=? WHERE id=?",
                    (str(group_id), media_id)
                )

        return {
            "duplicate_groups": duplicate_count,
            "similarity_groups": sum(
                1 for group in similarity_groups if len(group) > 1
            ),
            "similarity_pairs": pair_count
        }


def get_saved_detection_results():
    """读取数据库中保存的检测结果。"""

    ensure_detection_tables()

    with closing(get_connection()) as conn:

        duplicate_groups = conn.execute("""
            SELECT g.id AS group_id, m.*
            FROM duplicate_groups g
            JOIN duplicate_group_items i
                ON i.group_id = g.id
            JOIN media m
                ON m.id = i.media_id
            ORDER BY g.id, m.file_name
        """).fetchall()

        similar_groups = conn.execute("""
            SELECT g.id AS group_id, m.*, i.phash
            FROM similarity_groups g
            JOIN similarity_group_items i
                ON i.group_id = g.id
            JOIN media m
                ON m.id = i.media_id
            ORDER BY g.id, m.file_name
        """).fetchall()

        return duplicate_groups, similar_groups