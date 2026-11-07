from contextlib import closing
from pathlib import Path

import streamlit as st
from database import get_connection, get_all_media, init_database
from modules.scanner import scan_folder
from modules.folder_dialog import choose_folder

st.markdown("""
<style>
.stApp { font-size: 18px; }
.stTextInput label p, .stButton button p, .stMarkdown p { font-size: 18px; }
.stButton button { min-height: 48px; padding: 0.5rem 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.title('本地媒体扫描')
st.write('选择文件夹，扫描其中的图片和视频。原始文件不会被移动或修改。')
if st.button('选择文件夹'):
    try:
        selected = choose_folder()
        if selected:
            st.session_state['scan_folder_path'] = selected
    except (OSError, RuntimeError, UnicodeError) as exc:
        st.error(str(exc))
folder = st.text_input('文件夹路径', key='scan_folder_path', placeholder='选择文件夹，或在这里输入路径')
if st.button('开始扫描', type='primary'):
    try:
        with st.spinner('正在扫描，请稍候……'):
            result = scan_folder(folder)
        st.success(f"扫描完成：成功 {result['success']} 个，失败 {result['failed']} 个。")
        if result['errors']:
            with st.expander('查看未能处理的文件'):
                for error in result['errors']:
                    st.write(error)
    except (ValueError, OSError) as exc:
        st.error(str(exc))

init_database()
items = get_all_media()
st.divider()
st.subheader('媒体库概览')
total, images, videos = st.columns(3)
total.metric('媒体总数', len(items))
images.metric('图片', sum(item['file_type'] == 'image' for item in items))
videos.metric('视频', sum(item['file_type'] == 'video' for item in items))

if not items:
    st.info('还没有媒体记录。选择文件夹后点击“开始扫描”。')
else:
    st.subheader('最近添加的媒体')
    with closing(get_connection()) as conn:
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='media_thumbnails'").fetchone()
        thumbnails = {row['media_id']: row['thumbnail_path'] for row in conn.execute(
            'SELECT media_id, thumbnail_path FROM media_thumbnails'
        ).fetchall()} if exists else {}
    columns = st.columns(4)
    for index, item in enumerate(items[:12]):
        with columns[index % len(columns)]:
            thumbnail = thumbnails.get(item['id'])
            if thumbnail and Path(thumbnail).is_file():
                st.image(thumbnail, use_container_width=True)
            else:
                st.write('暂无缩略图')
            st.write(item['file_name'])
    with st.expander('查看文件信息'):
        st.dataframe([
            {'文件名': item['file_name'], '类型': '图片' if item['file_type'] == 'image' else '视频',
             '宽度': item['width'], '高度': item['height'], '拍摄时间': item['capture_time'],
             '文件路径': item['file_path']}
            for item in items
        ], use_container_width=True, hide_index=True)
