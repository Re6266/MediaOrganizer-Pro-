"""重复与相似检测页面：把第三周的算法模块接入可交互流程。"""

from pathlib import Path

import streamlit as st

from modules.detection_storage import (
    ensure_detection_tables, get_saved_detection_results, save_detection_results,
)
from modules.duplicate_detector import find_duplicate_files
from modules.media_library import list_media
from modules.similarity_detector import find_similar_images
from modules.similarity_group import group_similar_images
from modules.ui_theme import apply_theme, page_header, section_label

apply_theme("重复与相似检测", "🔍")
page_header(
    "STEP 02 · 识别冗余",
    "重复与相似检测",
    "SHA-256 识别内容完全一致的文件，pHash 识别视觉相似的图片。只读取已索引图片，不改动原始文件。",
)

# ==========================
# 1. 读取已索引图片
# ==========================

indexed = list_media(file_type="image")
available = [item for item in indexed if Path(item["file_path"]).is_file()]
missing_count = len(indexed) - len(available)
thumbnail_map = {item["id"]: item.get("thumbnail_path") for item in indexed}
path_to_id = {item["file_path"]: item["id"] for item in available}

total_col, ready_col, missing_col = st.columns(3)
total_col.metric("已索引图片", len(indexed))
ready_col.metric("可检测图片", len(available))
missing_col.metric("文件缺失", missing_count)

if missing_count:
    st.warning(f"有 {missing_count} 条索引对应的文件已不存在，本次检测会跳过这些记录。")

if not available:
    st.info("还没有可检测的图片。请先在“本地媒体扫描”页面选择文件夹并完成扫描。")
    st.stop()

# ==========================
# 2. 检测参数
# ==========================

section_label("检测参数", "阈值越小越严格")
threshold = st.slider(
    "相似判定阈值（汉明距离，0-32）",
    min_value=0, max_value=32, value=15,
    help="阈值越小判定越严格；数值越大，被归为相似的图片越多。",
)
st.caption(f"当前阈值 {threshold}：两张图片的感知哈希差异不超过 {threshold} 位时判定为视觉相似。")

if len(available) > 200:
    st.warning(
        f"本次将比较 {len(available)} 张图片，相似检测需要两两比较，耗时可能较长。"
        "建议先在较小范围测试。"
    )

run = st.button("开始检测并保存结果", type="primary")

# ==========================
# 3. 执行检测
# ==========================

if run:
    image_paths = [item["file_path"] for item in available]
    with st.spinner("正在计算文件哈希和感知哈希，请稍候……"):
        duplicate_result = find_duplicate_files(image_paths)
        similarity_result = find_similar_images(image_paths, threshold)
        similar_groups = group_similar_images(similarity_result["pairs"])
        summary = save_detection_results(duplicate_result, similarity_result, similar_groups)

    st.session_state["detection_run"] = {
        "threshold": threshold,
        "duplicate_result": duplicate_result,
        "similarity_result": similarity_result,
        "similar_groups": similar_groups,
        "summary": summary,
    }
    st.success(
        f"检测完成：完全重复 {summary['duplicate_groups']} 个文件、"
        f"相似组 {summary['similarity_groups']} 组、相似对 {summary['similarity_pairs']} 对，结果已保存。"
    )

    errors = duplicate_result["errors"] + similarity_result["errors"]
    if errors:
        with st.expander(f"查看未能处理的文件（{len(errors)} 个）"):
            for error in errors:
                st.write(f"{error['path']}：{error['error']}")

# ==========================
# 4. 展示本次结果
# ==========================

run_data = st.session_state.get("detection_run")


def render_members(paths, caption_builder=None):
    """按缩略图网格展示一组文件。"""
    columns = st.columns(min(4, len(paths)))
    for index, path in enumerate(paths):
        with columns[index % len(columns)]:
            thumbnail = thumbnail_map.get(path_to_id.get(path))
            if thumbnail and Path(thumbnail).is_file():
                st.image(thumbnail, use_container_width=True)
            else:
                st.info("暂无缩略图")
            st.caption(Path(path).name)
            if caption_builder:
                st.caption(caption_builder(path))


if run_data:
    st.divider()
    section_label("本次检测结果", "已写入数据库")
    duplicate_groups = run_data["duplicate_result"]["groups"]
    hashes = run_data["similarity_result"]["hashes"]
    summary = run_data["summary"]

    left, middle, right, extra = st.columns(4)
    left.metric("完全重复组", summary["duplicate_groups"])
    middle.metric("相似组", summary["similarity_groups"])
    right.metric("相似对", summary["similarity_pairs"])
    extra.metric("判定阈值", run_data["threshold"])

    st.markdown(f"**完全重复（SHA-256）** · {len(duplicate_groups)} 组")
    if not duplicate_groups:
        st.caption("没有发现内容完全一致的文件。")
    for index, group in enumerate(duplicate_groups, start=1):
        st.markdown(f"重复组 {index} · {len(group['files'])} 个文件 · 哈希 `{group['hash'][:12]}…`")
        member_paths = [path for path in group["files"] if path in path_to_id]
        if member_paths:
            render_members(member_paths)
        else:
            st.caption("该组文件未建立索引，未纳入数据库结果。")

    st.markdown(
        f"**视觉相似（pHash，阈值 {run_data['threshold']}）** · "
        f"{len(run_data['similar_groups'])} 组"
    )
    if not run_data["similar_groups"]:
        st.caption("当前阈值下没有发现视觉相似图片，可适当调大阈值后重试。")
    for index, group in enumerate(run_data["similar_groups"], start=1):
        st.markdown(f"相似组 {index} · {len(group)} 张图片")
        member_paths = [path for path in group if path in path_to_id]
        if member_paths:
            render_members(member_paths, lambda path: f"pHash {hashes.get(path, '-')}")
        else:
            st.caption("该组图片未建立索引，未纳入数据库结果。")

    st.info("结果已写入数据库。可前往“媒体浏览与照片组”页面查看候选组，并复制为可编辑的人工照片组。")

# ==========================
# 5. 数据库中的历史结果
# ==========================

st.divider()
section_label("数据库中已保存的检测结果")
ensure_detection_tables()
duplicate_rows, similar_rows = get_saved_detection_results()

if not duplicate_rows and not similar_rows:
    st.caption("数据库中还没有检测结果。点击上方按钮运行一次检测即可保存。")
else:
    duplicate_ids = {row["group_id"] for row in duplicate_rows}
    similar_ids = {row["group_id"] for row in similar_rows}
    left, right = st.columns(2)
    left.metric("完全重复组", len(duplicate_ids))
    right.metric("视觉相似组", len(similar_ids))

    if duplicate_ids:
        st.markdown("**完全重复组**")
        for group_id in sorted(duplicate_ids):
            names = "、".join(
                row["file_name"] for row in duplicate_rows if row["group_id"] == group_id
            )
            st.write(f"组 #{group_id}：{names}")

    if similar_ids:
        st.markdown("**视觉相似组**")
        for group_id in sorted(similar_ids):
            names = "、".join(
                row["file_name"] for row in similar_rows if row["group_id"] == group_id
            )
            st.write(f"组 #{group_id}：{names}")
