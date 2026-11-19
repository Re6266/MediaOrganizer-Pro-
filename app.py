
import streamlit as st

from database import init_database, get_all_media
from config import DATABASE_PATH, APP_NAME
from modules.ui_theme import apply_theme, page_header, section_label


# ==========================
# 1. 页面配置与主题
# ==========================

apply_theme(APP_NAME)


# ==========================
# 2. 初始化数据库
# ==========================

init_database()


# ==========================
# 3. 页面标题
# ==========================

page_header(
    "LOCAL MEDIA WORKSPACE",
    "MediaOrganizer-Pro",
    "本地媒体库智能索引与整理建议工具 · 索引、重复识别、智能选片与安全整理",
)

st.divider()


# ==========================
# 4. 获取媒体数据
# ==========================

media_list = get_all_media()


# ==========================
# 5. 统计信息
# ==========================

image_count = sum(
    1 for item in media_list
    if item["file_type"] == "image"
)

video_count = sum(
    1 for item in media_list
    if item["file_type"] == "video"
)

section_label("媒体库概览")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="媒体文件总数", value=len(media_list))

with col2:
    st.metric(label="图片数量", value=image_count)

with col3:
    st.metric(label="视频数量", value=video_count)


st.divider()


# ==========================
# 6. 系统信息
# ==========================

section_label("系统状态", "本地运行 · 数据不出本机")

system_left, system_right = st.columns([3, 2])

with system_left:
    st.write(f"**项目名称：** {APP_NAME}")
    st.write(f"**索引数据库：** `{DATABASE_PATH}`")
    st.write("**文件原则：** 扫描、检测与分组只读取原始媒体，不删除、不移动、不改名。")

with system_right:
    st.success("系统运行正常 · 数据库可读写")


# ==========================
# 7. 媒体文件列表
# ==========================

section_label("媒体文件列表", f"{len(media_list)} 条记录")

if media_list:
    st.dataframe(
        media_list,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("当前还没有媒体文件记录。请先在“本地媒体扫描”页面选择文件夹并完成扫描。")


st.divider()


# ==========================
# 8. 功能开发进度
# ==========================

section_label("模块进度", "按八周计划推进")

features = [
    ("本地媒体扫描与索引", "已完成", "#3d5c6e"),
    ("完全重复与相似图片检测", "已完成", "#3d5c6e"),
    ("媒体浏览、筛选与照片组管理", "已完成", "#3d5c6e"),
    ("图片质量评价与智能选片", "第5–6周", "#9b3d25"),
    ("AI 最佳瞬间合成", "第5周", "#9b3d25"),
    ("安全整理与操作日志", "第7周", "#9b3d25"),
]

for name, status, color in features:
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'border-bottom:2px solid #b9a78b;padding:10px 2px">'
        f'<span style="font-weight:700;font-size:13px">{name}</span>'
        f'<span style="font-size:10px;font-weight:800;letter-spacing:1px;color:#f3eadb;'
        f'background:{color};border:2px solid #5c4033;padding:2px 8px">{status}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


st.caption("MediaOrganizer-Pro | 第四周开发版本 · 媒体浏览与照片组")
