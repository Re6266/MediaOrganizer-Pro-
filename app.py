
import streamlit as st

from database import init_database, get_all_media
from config import DATABASE_PATH, APP_NAME
from modules.ui_theme import apply_theme, hero_banner, page_header, section_label


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

hero_banner(
    "PRIVACY FIRST · 全程本地处理",
    "所有分析都在本机完成，原始文件只读不动",
    "扫描目录建立索引，用 SHA-256 找出完全重复的文件，用感知哈希找出视觉相似的图片。"
    "整理建议先预览、再确认，任何一步都不会自动删掉你的照片。",
    "入口 · 左侧 02 重复与相似检测 → 03 浏览与分组",
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
    ("本地媒体扫描与索引", "已完成", "#eaf2ee", "#4c8064"),
    ("完全重复与相似图片检测", "已完成", "#eaf2ee", "#4c8064"),
    ("媒体浏览、筛选与照片组管理", "已完成", "#eaf2ee", "#4c8064"),
    ("AI 最佳瞬间合成", "第5周", "#fbf4e7", "#b49861"),
    ("图片质量评价与智能选片", "第5–6周", "#fbf4e7", "#b49861"),
    ("安全整理与操作日志", "第7周", "#fbf4e7", "#b49861"),
]

for name, status, bg, fg in features:
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'border-bottom:1px solid #e8ece9;padding:12px 2px">'
        f'<span style="font-weight:500;font-size:12px;color:#24332f">{name}</span>'
        f'<span style="font-size:9px;font-weight:500;color:{fg};'
        f'background:{bg};padding:4px 8px;border-radius:4px">{status}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


st.caption("MediaOrganizer-Pro | 第四周开发版本 · 媒体浏览与照片组")
