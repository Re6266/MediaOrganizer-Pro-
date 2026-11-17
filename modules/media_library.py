"""媒体浏览与人工照片组管理的数据访问层。"""

from contextlib import closing
from pathlib import Path

from database import get_connection, init_database


def _has_table(conn, table_name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    ).fetchone() is not None


def list_media(keyword="", file_type="全部", folder="", start_date=None, end_date=None):
    """按媒体库页面的条件查询索引，不读取或修改源文件。"""
    init_database()
    clauses, params = ["1=1"], []
    if keyword.strip():
        clauses.append("file_name LIKE ?")
        params.append(f"%{keyword.strip()}%")
    if file_type in ("image", "video"):
        clauses.append("file_type=?")
        params.append(file_type)
    if folder.strip():
        clauses.append("file_path LIKE ?")
        params.append(f"%{folder.strip()}%")
    if start_date:
        clauses.append("COALESCE(capture_time, created_at) >= ?")
        params.append(str(start_date))
    if end_date:
        clauses.append("COALESCE(capture_time, created_at) < date(?, '+1 day')")
        params.append(str(end_date))

    with closing(get_connection()) as conn:
        thumbnails = _thumbnail_map(conn)
        rows = conn.execute(
            "SELECT * FROM media WHERE " + " AND ".join(clauses) +
            " ORDER BY COALESCE(capture_time, created_at) DESC, id DESC", params
        ).fetchall()
    return [dict(row, thumbnail_path=thumbnails.get(row["id"])) for row in rows]


def _thumbnail_map(conn):
    """读取缩略图索引；未生成缩略图时返回空字典。"""
    if not _has_table(conn, "media_thumbnails"):
        return {}
    return {
        row["media_id"]: row["thumbnail_path"]
        for row in conn.execute("SELECT media_id, thumbnail_path FROM media_thumbnails")
    }


def list_detected_groups():
    """读取第三周检测结果；没有结果时返回空列表。"""
    init_database()
    groups = []
    with closing(get_connection()) as conn:
        thumbnails = _thumbnail_map(conn)
        for kind, group_table, item_table in (
            ("完全重复", "duplicate_groups", "duplicate_group_items"),
            ("视觉相似", "similarity_groups", "similarity_group_items"),
        ):
            if not (_has_table(conn, group_table) and _has_table(conn, item_table)):
                continue
            rows = conn.execute(
                f"SELECT g.id AS group_id, m.* FROM {group_table} g "
                f"JOIN {item_table} i ON i.group_id=g.id "
                "JOIN media m ON m.id=i.media_id ORDER BY g.id, m.file_name"
            ).fetchall()
            bucket = {}
            for row in rows:
                bucket.setdefault(row["group_id"], []).append(
                    dict(row, thumbnail_path=thumbnails.get(row["id"]))
                )
            groups.extend({"kind": kind, "group_id": group_id, "members": members}
                          for group_id, members in bucket.items())
    return groups


def list_manual_groups():
    init_database()
    with closing(get_connection()) as conn:
        thumbnails = _thumbnail_map(conn)
        groups = conn.execute(
            "SELECT * FROM photo_groups ORDER BY group_id DESC"
        ).fetchall()
        result = []
        for group in groups:
            members = conn.execute(
                "SELECT m.*, i.relation_type FROM photo_group_items i "
                "JOIN media m ON m.id=i.media_id WHERE i.group_id=? ORDER BY m.file_name",
                (group["group_id"],),
            ).fetchall()
            result.append({"group_id": group["group_id"], "group_name": group["group_name"],
                           "group_type": group["group_type"],
                           "members": [dict(x, thumbnail_path=thumbnails.get(x["id"]))
                                       for x in members]})
    return result


def create_manual_group(name, media_ids, group_type="manual"):
    name = name.strip()
    media_ids = sorted({int(item) for item in media_ids})
    if not name:
        raise ValueError("请输入照片组名称")
    if len(media_ids) < 2:
        raise ValueError("照片组至少需要两张媒体")
    init_database()
    with closing(get_connection()) as conn, conn:
        group_id = conn.execute(
            "INSERT INTO photo_groups(group_name, group_type) VALUES (?, ?)", (name, group_type)
        ).lastrowid
        existing = {row["id"] for row in conn.execute(
            "SELECT id FROM media WHERE id IN (" + ",".join("?" * len(media_ids)) + ")", media_ids
        )}
        if len(existing) != len(media_ids):
            raise ValueError("部分媒体记录不存在，请刷新页面后重试")
        conn.executemany(
            "INSERT INTO photo_group_items(group_id, media_id, relation_type) VALUES (?, ?, ?)",
            [(group_id, media_id, "manual") for media_id in media_ids],
        )
    return group_id


def add_group_members(group_id, media_ids):
    media_ids = sorted({int(item) for item in media_ids})
    if not media_ids:
        return 0
    with closing(get_connection()) as conn, conn:
        return sum(conn.execute(
            "INSERT OR IGNORE INTO photo_group_items(group_id, media_id, relation_type) VALUES (?, ?, ?)",
            (group_id, media_id, "manual"),
        ).rowcount for media_id in media_ids)


def remove_group_member(group_id, media_id):
    with closing(get_connection()) as conn, conn:
        return conn.execute(
            "DELETE FROM photo_group_items WHERE group_id=? AND media_id=?", (group_id, media_id)
        ).rowcount
