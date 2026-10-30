
import streamlit as st

from database import init_database, get_all_media
from config import DATABASE_PATH, APP_NAME


# ==========================
# 1. 页面配置
# ==========================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🗂️",
    layout="wide"
)


# ==========================
# 2. 初始化数据库
# ==========================

init_database()


# ==========================
# 3. 页面标题
# ==========================

st.title("🗂️ MediaOrganizer-Pro")

st.subheader("本地媒体库智能索引与整理建议工具")

st.write(
    "帮助用户管理本地图片和视频，"
    "实现媒体索引、重复识别、智能选片和安全整理。"
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


col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="媒体文件总数",
        value=len(media_list)
    )

with col2:
    st.metric(
        label="图片数量",
        value=image_count
    )

with col3:
    st.metric(
        label="视频数量",
        value=video_count
    )


st.divider()


# ==========================
# 6. 系统信息
# ==========================

st.subheader("系统信息")

st.write("项目名称：", APP_NAME)

st.write("数据库位置：", str(DATABASE_PATH))

st.success("系统运行正常")


# ==========================
# 7. 媒体文件列表
# ==========================

st.subheader("媒体文件列表")

if media_list:

    st.dataframe(
        media_list,
        use_container_width=True
    )

else:

    st.info(
        "当前还没有媒体文件记录。"
        "第二周将接入本地媒体扫描功能。"
    )


st.divider()


# ==========================
# 8. 功能开发进度
# ==========================

st.subheader("系统功能")

features = [
    "本地媒体扫描与索引",
    "完全重复与相似图片检测",
    "图片质量评价与智能选片",
    "用户偏好管理",
    "安全整理与操作日志"
]

for feature in features:
    st.write("🔧", feature)


st.caption(
    "MediaOrganizer-Pro | 第一周开发版本"
)
