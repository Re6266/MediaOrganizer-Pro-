from pathlib import Path
import re
import importlib
from html import escape
from contextlib import closing
import sqlite3

import streamlit as st
from database import get_all_media, init_database, get_connection, delete_media_by_path
from modules.folder_dialog import choose_paths
import modules.scanner as scanner

# A Streamlit process started before this feature may still hold the older
# scanner module in memory after the page itself is refreshed.
if not all(hasattr(scanner, name) for name in ("discover_folder", "validate_selection_size")):
    scanner = importlib.reload(scanner)
scan_files, discover_folder = scanner.scan_files, scanner.discover_folder

st.set_page_config(page_title="MediaOrganizer Pro", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
.stApp {background: #f6f8fc; color: #17243a;}
header[data-testid="stHeader"] {background: transparent;}
[data-testid="stSidebar"] {background: #ffffff;}
.block-container {max-width: 1160px; padding-top: 2.8rem; padding-bottom: 4rem;}
h1,h2,h3,p,label {color: #17243a;}
.eyebrow {font-size: 15px; font-weight: 750; color: #4568db; letter-spacing: .1em;}
.hero {background: linear-gradient(115deg,#e9efff,#f1f5ff 65%,#e7f6f5); border:1px solid #dce5fb;
 border-radius:22px; padding:30px 32px; margin: 12px 0 24px;}
.hero h1 {font-size: 36px; margin: 8px 0; letter-spacing:-.03em;}
.hero p {font-size:18px; color:#53627a; margin:0; line-height:1.6;}
div[data-testid="stMetric"] {background: white; border: 1px solid #e4eaf3; border-radius: 16px; padding: 20px;}
div[data-testid="stMetricLabel"] p {font-size:16px; color:#5c6c84;}
div.stButton > button {min-height: 50px; border-radius: 11px; font-size:17px; font-weight:650;}
div.stButton > button[kind="secondary"] {background:#ffffff; color:#3157bd; border:1px solid #bdcae6;}
div.stButton > button[kind="secondary"] p {color:#3157bd;}
div.stButton > button[kind="primary"] {background:#4167df; border-color:#4167df; color:white;}
div.stButton > button[kind="primary"] p {color:white;}
div[data-testid="stTextInput"] label p {font-size:16px;}
div[data-testid="stTextInput"] input {font-size:16px; color:#26364d; background:#ffffff;}
div[data-testid="stTextInput"] div[data-baseweb="input"] {background:#ffffff; border:1px solid #cad5e8; border-radius:10px;}
.st-key-recent_page div[data-baseweb="base-input"],
.st-key-recent_page div[data-baseweb="input"],
.st-key-recent_page input {background:#ffffff !important; color:#17243a !important;}
.st-key-recent_page button {background:#ffffff !important; color:#3157bd !important;}
.st-key-recent_page button svg {fill:#3157bd !important;}
section[data-testid="stFileUploaderDropzone"] {background:transparent; padding:0; border:0;}
section[data-testid="stFileUploaderDropzone"] small {display:none;}
section[data-testid="stFileUploaderDropzone"] button {background:#ffffff; border:1px solid #bdcae6; color:#3157bd; border-radius:11px; min-height:50px; font-size:0;}
section[data-testid="stFileUploaderDropzone"] button > * {display:none;}
.st-key-selected_files section[data-testid="stFileUploaderDropzone"] button::after {content:"📁  上传文件"; font-size:17px; font-weight:650; color:#3157bd;}
.hint {color:#687890; font-size:16px; line-height:1.6;}
.empty {background:white; border:1px dashed #cad4e5; border-radius:18px; padding:38px; text-align:center; color:#63738b; font-size:17px;}
.section-label {font-size:14px; font-weight:700; color:#5870a5; letter-spacing:.08em; margin-top:20px;}
div[data-testid="stDialog"] div[role="dialog"] {background:#ffffff; color:#17243a; border-radius:18px;}
div[data-testid="stDialog"] button {color:#30466d;}
div[data-testid="stDialog"] video[data-testid="stVideo"] {
  display:block; width:100%; height:auto; max-height:55vh; object-fit:contain; background:#111;
}
div[data-testid="stDialog"] [data-testid="stImage"] img {
  max-width:100%; max-height:55vh; width:auto; object-fit:contain; margin:auto; display:block;
}
div[data-testid="stDialog"] h3 {color:#17243a !important; overflow-wrap:anywhere;}
div[data-testid="stVerticalBlockBorderWrapper"] > div {background:#fff; border:1px solid #e4eaf3; border-radius:12px;}
.media-name {color:#17243a; font-size:17px; font-weight:600; overflow-wrap:anywhere; padding-top:8px;}
.media-meta {color:#73819a; font-size:14px; padding-bottom:4px;}
div[class*="st-key-preview_"] button {background:#edf2ff !important; border:1px solid #d5e0fa !important; color:#3157bd !important; border-radius:10px; min-width:48px;}
div[class*="st-key-preview_"] button:hover {background:#dfe9ff !important; border-color:#92aceb !important;}
div[class*="st-key-preview_"] button:focus-visible {outline:2px solid #3157bd; outline-offset:2px;}
div[class*="st-key-remove_"] button {background:#fff !important; border:1px solid #e1e7f0 !important; color:#64748b !important; border-radius:10px; min-width:48px;}
div[class*="st-key-remove_"] button p {color:#64748b !important;}
div[class*="st-key-remove_"] button:hover {background:#fff3f3 !important; border-color:#f0caca !important;}
div[class*="st-key-remove_"] button:hover p {color:#b34141 !important;}
div[data-testid="stPopover"] button {background:#ffffff !important; color:#3157bd !important; border:1px solid #bdcae6 !important; border-radius:11px; min-height:50px;}
div[data-testid="stPopover"] button p {color:#3157bd !important;}
[data-testid="stPopoverBody"], [data-baseweb="popover"], [data-baseweb="popover"] > div {background:#ffffff !important; color:#17243a !important; border-color:#dce5f2 !important;}
div[data-testid="stAlert"] p {color:#17243a;}
div[data-testid="stExpander"] details > summary,
div[data-testid="stExpander"] details[open] > summary {
  background:#edf2fb !important; color:#17243a !important;
}
div[data-testid="stExpander"] details > summary p,
div[data-testid="stExpander"] details > summary span,
div[data-testid="stExpander"] details > summary svg {color:#17243a !important; fill:#17243a;}
</style>
""", unsafe_allow_html=True)

init_database()
st.markdown('<div class="eyebrow">✦ &nbsp; MEDIAORGANIZER PRO</div>', unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">你的本地媒体库</div><h1>让照片与视频，井然有序。</h1><p>选择本地文件或文件夹，轻松建立媒体库。<br>原始文件留在原处，随时安心浏览。</p></div>', unsafe_allow_html=True)

st.subheader("开始建立媒体库")
@st.dialog("文件预览", width="large")
def preview_selected(path):
    selected = Path(path)
    st.subheader(selected.name)
    if not selected.is_file():
        st.warning("原文件不可用：文件可能已移动、删除，或所在设备未连接。")
        return
    try:
        if selected.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            st.image(str(selected), width="stretch")
        elif selected.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv"}:
            st.video(str(selected))
        else:
            st.info("此类型暂不支持预览。")
    except (OSError, ValueError) as exc:
        st.error(f"无法预览此文件：{exc}")


@st.fragment
def media_selection():
    pending = st.session_state.get("pending_media")
    if not pending:
        if st.button("＋  添加媒体", key="add_media"):
            st.session_state["show_media_choices"] = not st.session_state.get("show_media_choices", False)
        if st.session_state.get("show_media_choices"):
            file_col, folder_col = st.columns(2)
            for mode, label in (("files", "选择文件"), ("folder", "选择文件夹")):
                with file_col if mode == "files" else folder_col:
                    if st.button(label, key=f"choose_{mode}", use_container_width=True):
                        try:
                            paths = choose_paths(mode)
                            if paths:
                                if mode == "folder":
                                    folder = paths[0]
                                    with st.spinner("正在读取文件夹内容……"):
                                        files, errors = discover_folder(folder)
                                    st.session_state["pending_media"] = {"mode": mode, "folder": folder, "paths": files, "errors": errors}
                                else:
                                    paths = scanner.validate_selection_size(paths)
                                    st.session_state["pending_media"] = {"mode": mode, "paths": paths}
                                st.session_state["show_media_choices"] = False
                                st.rerun()
                        except (RuntimeError, OSError, ValueError) as exc:
                            st.error(str(exc))
    else:
        mode, paths = pending["mode"], pending["paths"]
        if mode == "folder":
            st.info(f"已选择文件夹：{pending['folder']} · {len(paths)} 个文件")
        else:
            st.info(f"已选择 {len(paths)} 个文件")
        if pending.get("errors"):
            st.warning(f"有 {len(pending['errors'])} 个文件夹无法读取，将在扫描结果中列出。")
        if paths:
            with st.expander("查看已选择的文件"):
                    for index, path in enumerate(paths):
                        name_col, preview_col, remove_col = st.columns([10, 1, 1], vertical_alignment="center")
                        with name_col:
                            display = str(Path(path).relative_to(pending["folder"])) if mode == "folder" else Path(path).name
                            st.markdown(f'<div class="media-name">{escape(display)}</div>', unsafe_allow_html=True)
                        with preview_col:
                            if st.button("🔍", key=f"preview_selected_{index}"):
                                preview_selected(path)
                        with remove_col:
                            if st.button("✕", key=f"remove_selected_{index}"):
                                remaining = paths[:index] + paths[index + 1:]
                                if remaining:
                                    st.session_state["pending_media"] = {**pending, "paths": remaining}
                                else:
                                    del st.session_state["pending_media"]
                                    st.session_state["show_media_choices"] = True
                                st.rerun()
        else:
            st.write("文件夹中没有可查看的文件。")
        scan_col, cancel_col, _ = st.columns([1, 1, 6])
        with scan_col:
            if st.button("开始扫描", type="primary", use_container_width=True):
                try:
                    with st.spinner("正在扫描，请稍候……"):
                        result = scan_files(paths)
                        result["failed"] += len(pending.get("errors", []))
                        result["errors"].extend(pending.get("errors", []))
                    st.session_state["scan_result"] = result
                    del st.session_state["pending_media"]
                    st.rerun()
                except (OSError, ValueError) as exc:
                    st.error(f"无法扫描：{exc}")
        with cancel_col:
            if st.button("取消", use_container_width=True):
                del st.session_state["pending_media"]
                st.rerun()
    result = st.session_state.pop("scan_result", None)
    if result is not None:
        st.success(f"本次扫描完成：成功 {result['success']} 个，失败 {result['failed']} 个，跳过 {result['ignored']} 个不支持的文件。")
        if result["errors"]:
            with st.expander("查看未能处理的文件"):
                for error in result["errors"]:
                    st.write(error)


media_selection()

items = get_all_media()
st.markdown('<div class="section-label">LIBRARY OVERVIEW</div>', unsafe_allow_html=True)
st.subheader("媒体库概览")
a, b, c = st.columns(3)
a.metric("全部媒体", len(items))
b.metric("图片", sum(item["file_type"] == "image" for item in items))
c.metric("视频", sum(item["file_type"] == "video" for item in items))
st.markdown('<div class="section-label">RECENTLY ADDED</div>', unsafe_allow_html=True)
st.subheader("最近添加")
def display_name(item):
    name = item["file_name"]
    if Path(item["file_path"]).parent.name == "imported":
        return re.sub(r"^[0-9a-f]{64}_", "", name)
    return name


@st.dialog("媒体预览", width="large")
def preview_media(item):
    path = Path(item["file_path"])
    st.subheader(display_name(item))
    if not path.is_file():
        st.warning("原文件不可用：文件可能已移动、删除，或所在设备未连接。")
        return
    try:
        if item["file_type"] == "image":
            st.image(str(path), width="stretch")
        else:
            st.video(str(path))
        width, height = item.get("width"), item.get("height")
        st.write(f"文件大小：{item['file_size'] / 1024:.1f} KB")
        st.write(f"分辨率：{width} × {height}" if width and height else "分辨率：未知")
        if item["file_type"] == "video":
            with closing(get_connection()) as conn:
                exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='video_date_metadata'").fetchone()
                dates = conn.execute("SELECT creation_time, read_status FROM video_date_metadata WHERE media_id=?", (item["id"],)).fetchone() if exists else None
            if item.get("capture_time"):
                st.write(f"录制时间（文件元数据）：{item['capture_time']}")
            else:
                st.write("录制时间：未知")
            if dates and dates["creation_time"]:
                st.write(f"视频创建时间（文件元数据，不一定是拍摄时间）：{dates['creation_time']}")
            if not dates or dates["read_status"] == "ffprobe_unavailable":
                st.caption("录制时间暂未检测，请重新扫描文件。")
            elif dates["read_status"] == "probe_failed":
                st.caption("视频时间读取失败，可稍后重新扫描。")
            duration = item.get("duration")
            st.write(f"视频时长：{duration:.1f} 秒" if duration is not None else "视频时长：未知")
        else:
            st.write(f"拍摄时间：{item.get('capture_time') or '未知（文件中没有可用的拍摄时间）'}")
    except (OSError, ValueError) as exc:
        st.error(f"无法预览此文件：{exc}")


if not items:
    st.markdown('<div class="empty">✦<br><br>这里还没有媒体文件<br><span style="font-size:15px">选择文件并开始扫描，你的照片和视频会显示在这里。</span></div>', unsafe_allow_html=True)
else:
    with closing(get_connection()) as conn:
        table = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='media_thumbnails'").fetchone()
        thumbnails = {row["media_id"]: row["thumbnail_path"] for row in conn.execute("SELECT media_id, thumbnail_path FROM media_thumbnails")} if table else {}
    page_size = 20
    pages = (len(items) + page_size - 1) // page_size
    page = st.number_input("页码", min_value=1, max_value=pages, value=1, step=1, label_visibility="collapsed", key="recent_page") if pages > 1 else 1
    for item in items[(page - 1) * page_size:page * page_size]:
        with st.container(border=True):
            icon, detail, action, remove = st.columns([1, 8, 1, 1], vertical_alignment="center")
            with icon:
                thumb = thumbnails.get(item["id"])
                if thumb and Path(thumb).is_file():
                    st.image(thumb, width=60)
                else:
                    st.write("🖼️")
            with detail:
                st.markdown(f'<div class="media-name">{escape(display_name(item))}</div>', unsafe_allow_html=True)
                kind = "图片" if item["file_type"] == "image" else "视频"
                availability = "" if Path(item["file_path"]).is_file() else " · 原文件不可用"
                st.markdown(f'<div class="media-meta">{kind} · {item["file_size"] / 1024:.0f} KB{availability}</div>', unsafe_allow_html=True)
            with action:
                if st.button("🔍", key=f"preview_{item['id']}"):
                    preview_media(dict(item))
            with remove:
                if st.button("✕", key=f"remove_media_{item['id']}"):
                    st.session_state["confirm_remove_id"] = item["id"]
                    st.rerun()
            if st.session_state.get("confirm_remove_id") == item["id"]:
                st.write("移出媒体库记录？电脑上的文件会保留。")
                confirm_col, cancel_remove_col, _ = st.columns([1, 1, 6])
                with confirm_col:
                    if st.button("确认移出", key=f"confirm_remove_{item['id']}"):
                        try:
                            delete_media_by_path(item["file_path"])
                            del st.session_state["confirm_remove_id"]
                            st.rerun()
                        except sqlite3.Error:
                            st.error("无法移出该记录，文件可能正在被其他记录使用。")
                with cancel_remove_col:
                    if st.button("取消", key=f"cancel_remove_{item['id']}"):
                        del st.session_state["confirm_remove_id"]
                        st.rerun()
