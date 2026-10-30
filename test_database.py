
import sqlite3
import os

from config import DATABASE_PATH
from database import (
    init_database,
    insert_media,
    create_photo_group,
    add_photo_to_group,
    get_photo_group_items,
    create_ai_composition,
    add_composition_source,
    update_composition_status,
    get_all_media,
)


def test_database():
    print("\n========== MediaOrganizer-Pro 数据库测试 ==========\n")

    # 1. 初始化数据库
    init_database()

    # 2. 检查数据表
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table'
    """)

    tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {
        "media",
        "photo_groups",
        "photo_group_items",
        "ai_compositions",
        "composition_sources",
        "operation_logs",
    }

    assert expected_tables.issubset(tables), "数据表创建不完整！"
    print("测试1：六张数据表创建成功！")

    # 3. 插入测试照片
    test_path = str(DATABASE_PATH.parent / "test_photo_001.jpg")

    insert_media({
        "file_path": test_path,
        "file_name": "test_photo_001.jpg",
        "file_type": "image",
        "file_size": 102400,
        "width": 1920,
        "height": 1080,
        "is_generated": False,
    })

    cursor.execute(
        "SELECT id FROM media WHERE file_path = ?",
        (test_path,)
    )

    media_row = cursor.fetchone()
    assert media_row is not None, "照片插入失败！"
    media_id = media_row[0]

    print("测试2：原始照片插入成功！")

    # 4. 创建照片组
    group_id = create_photo_group(
        "测试连拍照片组",
        "burst"
    )

    add_photo_to_group(group_id, media_id, "burst")

    group_items = get_photo_group_items(group_id)

    assert len(group_items) == 1, "照片组关联失败！"
    print("测试3：照片组创建及关联成功！")

    # 5. 创建 AI 合成任务
    composition_id = create_ai_composition(
        group_id=group_id,
        mode="manual",
        prompt="融合自然表情和良好姿势",
        model_name="test-model"
    )

    assert composition_id is not None
    print("测试4：AI 合成任务创建成功！")

    # 6. 记录照片来源
    add_composition_source(
        composition_id=composition_id,
        media_id=media_id,
        feature_type="expression",
        is_selected=True
    )

    cursor.execute("""
        SELECT COUNT(*)
        FROM composition_sources
        WHERE composition_id = ?
    """, (composition_id,))

    source_count = cursor.fetchone()[0]
    assert source_count == 1, "合成来源记录失败！"

    print("测试5：合成照片来源记录成功！")

    # 7. 更新合成任务状态
    update_composition_status(
        composition_id,
        "completed",
        output_path="data/generated/test_result.jpg"
    )

    cursor.execute("""
        SELECT status, output_path
        FROM ai_compositions
        WHERE composition_id = ?
    """, (composition_id,))

    result = cursor.fetchone()

    assert result[0] == "completed"
    assert result[1] == "data/generated/test_result.jpg"

    print("测试6：AI 合成任务状态更新成功！")

    # 8. 检查媒体查询功能
    media_list = get_all_media()
    assert len(media_list) >= 1

    print("测试7：媒体查询功能正常！")

    # 9. 清理本次测试产生的数据
    cursor.execute(
        "DELETE FROM composition_sources WHERE composition_id = ?",
        (composition_id,)
    )

    cursor.execute(
        "DELETE FROM ai_compositions WHERE composition_id = ?",
        (composition_id,)
    )

    cursor.execute(
        "DELETE FROM photo_group_items WHERE group_id = ?",
        (group_id,)
    )

    cursor.execute(
        "DELETE FROM photo_groups WHERE group_id = ?",
        (group_id,)
    )

    cursor.execute(
        "DELETE FROM media WHERE id = ?",
        (media_id,)
    )

    conn.commit()
    conn.close()

    print("\n所有测试通过！")
    print("测试数据已清理。")
    print("原有媒体数据没有被清除。")
    print("\n====================================================")


if __name__ == "__main__":
    test_database()
