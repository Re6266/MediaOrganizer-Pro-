
import sqlite3
from dataclasses import asdict, is_dataclass

from config import DATABASE_PATH


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _get_columns(cursor, table_name):
    """获取指定数据表的字段"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row["name"] for row in cursor.fetchall()}


def init_database():
    """初始化数据库，并兼容旧版 media 表"""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. 媒体文件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL DEFAULT 0,
                width INTEGER,
                height INTEGER,
                duration REAL,
                capture_time TEXT,
                file_hash TEXT,
                similarity_group TEXT,
                quality_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 兼容旧版数据库：为 media 表补充新字段
        media_columns = _get_columns(cursor, "media")

        if "is_generated" not in media_columns:
            cursor.execute("""
                ALTER TABLE media
                ADD COLUMN is_generated INTEGER NOT NULL DEFAULT 0
            """)

        if "source_composition_id" not in media_columns:
            cursor.execute("""
                ALTER TABLE media
                ADD COLUMN source_composition_id INTEGER
            """)

        # 2. 照片组表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photo_groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL,
                group_type TEXT NOT NULL DEFAULT 'burst',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. 照片组成员关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photo_group_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                relation_type TEXT DEFAULT 'similar',

                FOREIGN KEY (group_id)
                    REFERENCES photo_groups(group_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (media_id)
                    REFERENCES media(id)
                    ON DELETE CASCADE,

                UNIQUE(group_id, media_id)
            )
        """)

        # 4. AI 合成任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_compositions (
                composition_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                output_path TEXT,
                prompt TEXT,
                model_name TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (group_id)
                    REFERENCES photo_groups(group_id)
            )
        """)

        # 5. AI 合成来源表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS composition_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                composition_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                feature_type TEXT NOT NULL,
                is_selected INTEGER NOT NULL DEFAULT 1,

                FOREIGN KEY (composition_id)
                    REFERENCES ai_compositions(composition_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (media_id)
                    REFERENCES media(id)
            )
        """)

        # 6. 文件操作日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                target_path TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print("数据库初始化成功！")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def insert_media(media):
    """插入媒体记录，兼容 dataclass 和 dict"""

    if is_dataclass(media):
        data = asdict(media)
    else:
        data = dict(media)

    allowed_columns = {
        "file_path", "file_name", "file_type", "file_size",
        "width", "height", "duration", "capture_time",
        "file_hash", "similarity_group", "quality_score",
        "created_at", "is_generated", "source_composition_id"
    }

    data = {
        key: value
        for key, value in data.items()
        if key in allowed_columns and value is not None
    }

    if not data.get("file_path"):
        raise ValueError("媒体文件路径不能为空")

    if not data.get("file_name"):
        raise ValueError("媒体文件名不能为空")

    if not data.get("file_type"):
        raise ValueError("媒体文件类型不能为空")

    columns = list(data.keys())
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)

    sql = f"""
        INSERT OR IGNORE INTO media ({column_sql})
        VALUES ({placeholders})
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, [data[column] for column in columns])
        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def get_all_media():
    """查询所有媒体"""
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media ORDER BY id DESC")
        return cursor.fetchall()

    finally:
        conn.close()


def delete_media_by_path(file_path):
    """根据路径删除媒体数据库记录"""
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM media WHERE file_path = ?",
            (file_path,)
        )
        conn.commit()
        return cursor.rowcount

    finally:
        conn.close()


def create_photo_group(group_name, group_type="burst"):
    """创建照片组"""
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO photo_groups (group_name, group_type)
            VALUES (?, ?)
        """, (group_name, group_type))

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def add_photo_to_group(group_id, media_id, relation_type="similar"):
    """将照片加入照片组"""
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO photo_group_items
            (group_id, media_id, relation_type)
            VALUES (?, ?, ?)
        """, (group_id, media_id, relation_type))

        conn.commit()
        return cursor.rowcount

    finally:
        conn.close()


def get_photo_group_items(group_id):
    """查询照片组中的所有照片"""
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT media.*
            FROM media
            INNER JOIN photo_group_items
                ON media.id = photo_group_items.media_id
            WHERE photo_group_items.group_id = ?
            ORDER BY media.id
        """, (group_id,))

        return cursor.fetchall()

    finally:
        conn.close()


def create_ai_composition(
    group_id,
    mode,
    prompt=None,
    model_name=None
):
    """创建 AI 合成任务"""

    if mode not in ("automatic", "manual"):
        raise ValueError("合成模式必须是 automatic 或 manual")

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_compositions
            (group_id, mode, prompt, model_name)
            VALUES (?, ?, ?, ?)
        """, (group_id, mode, prompt, model_name))

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def add_composition_source(
    composition_id,
    media_id,
    feature_type,
    is_selected=True
):
    """记录参与合成的原始照片及其作用"""

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO composition_sources
            (composition_id, media_id, feature_type, is_selected)
            VALUES (?, ?, ?, ?)
        """, (
            composition_id,
            media_id,
            feature_type,
            int(is_selected)
        ))

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def update_composition_status(
    composition_id,
    status,
    output_path=None,
    error_message=None
):
    """更新 AI 合成任务状态"""

    allowed_status = {
        "pending", "processing", "completed", "failed"
    }

    if status not in allowed_status:
        raise ValueError("不支持的合成任务状态")

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ai_compositions
            SET status = ?,
                output_path = ?,
                error_message = ?
            WHERE composition_id = ?
        """, (
            status,
            output_path,
            error_message,
            composition_id
        ))

        conn.commit()
        return cursor.rowcount

    finally:
        conn.close()


def add_operation_log(
    operation_type,
    target_path,
    status,
    description=None
):
    """记录文件操作日志"""

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO operation_logs
            (operation_type, target_path, status, description)
            VALUES (?, ?, ?, ?)
        """, (
            operation_type,
            target_path,
            status,
            description
        ))

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
