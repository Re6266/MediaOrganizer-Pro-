from pathlib import Path

import streamlit as st

from modules.media_library import (
    add_group_members, create_manual_group, list_detected_groups, list_manual_groups,
    list_media, remove_group_member,
)

st.set_page_config(page_title="媒体浏览与照片组", page_icon="🖼️", layout="wide")
st.title("媒体浏览与照片组")
st.caption("浏览已索引的媒体，查看第三周检测候选组，并按需要建立或调整人工照片组。不会修改原始文件。")


def show_thumbnail(item, caption_prefix=""):
    """统一展示缩略图，缺失时给出提示。"""
    thumbnail = item.get("thumbnail_path")
    if thumbnail and Path(thumbnail).is_file():
        st.image(thumbnail, use_container_width=True)
    else:
        st.info("暂无缩略图")
    if caption_prefix:
        st.caption(f"{caption_prefix}{item['file_name']}")


with st.expander("筛选媒体", expanded=True):
    left, middle, right = st.columns(3)
    keyword = left.text_input("文件名关键词")
    kind_label = middle.selectbox("媒体类型", ["全部", "图片", "视频"])
    folder = right.text_input("路径包含")
    dates = st.date_input("拍摄日期范围（可选）", value=())
kind = {"图片": "image", "视频": "video"}.get(kind_label, "全部")
start = dates[0] if isinstance(dates, tuple) and len(dates) == 2 else None
end = dates[1] if isinstance(dates, tuple) and len(dates) == 2 else None
media = list_media(keyword, kind, folder, start, end)

st.subheader(f"媒体库（{len(media)} 项）")
if not media:
    st.info("没有符合条件的媒体。请先在“本地媒体扫描”页面建立索引，或调整筛选条件。")
else:
    cards = st.columns(4)
    for index, item in enumerate(media):
        with cards[index % 4]:
            show_thumbnail(item)
            st.write(f"**{item['file_name']}**")
            st.caption(
                f"{'图片' if item['file_type'] == 'image' else '视频'} · "
                f"{item['width'] or '-'} × {item['height'] or '-'}"
            )
            with st.expander("查看详情"):
                preview = item["file_path"] if item["file_type"] == "image" else None
                if preview and Path(preview).is_file():
                    st.image(preview, use_container_width=True)
                st.write("拍摄时间：", item["capture_time"] or "未读取")
                st.write("文件大小：", item["file_size"])
                st.write("重复哈希：", item.get("file_hash") or "未计算")
                st.write("相似组标记：", item.get("similarity_group") or "无")
                st.code(item["file_path"], language=None)

st.divider()
st.subheader("检测候选组")
detected = list_detected_groups()
if not detected:
    st.info("尚无已保存的重复或相似检测结果。可先完成扫描并运行检测。")
else:
    for group in detected:
        st.markdown(f"**{group['kind']}组 #{group['group_id']}**（{len(group['members'])} 项）")
        previews = st.columns(min(4, len(group["members"])))
        for index, member in enumerate(group["members"]):
            with previews[index % len(previews)]:
                show_thumbnail(member)
        labels = {f"{member['file_name']} 〔#{member['id']}〕": member for member in group["members"]}
        chosen = st.multiselect(
            "选择要复制的成员（默认全选，可去掉本次不整理的图片）",
            list(labels),
            default=list(labels),
            key=f"pick_{group['kind']}_{group['group_id']}",
        )
        if st.button("复制所选为可编辑的人工组", key=f"copy_{group['kind']}_{group['group_id']}"):
            try:
                new_group_id = create_manual_group(
                    f"{group['kind']}候选组 {group['group_id']}",
                    [labels[label]["id"] for label in chosen],
                    group_type="review",
                )
                st.success(f"已创建可编辑照片组 #{new_group_id}")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

st.divider()
st.subheader("人工照片组管理")
options = {f"{item['file_name']} 〔#{item['id']}〕": item["id"] for item in media}
with st.form("create_manual_group", clear_on_submit=True):
    name = st.text_input("新照片组名称")
    selected = st.multiselect("选择至少两张已筛选的媒体", list(options))
    submitted = st.form_submit_button("创建人工照片组", type="primary")
if submitted:
    try:
        group_id = create_manual_group(name, [options[label] for label in selected])
        st.success(f"已创建照片组 #{group_id}")
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))

manual_groups = list_manual_groups()
if not manual_groups:
    st.caption("尚未创建人工照片组。")
for group in manual_groups:
    st.markdown(f"#### {group['group_name']} · {group['group_type']}")
    st.write("当前成员：", "、".join(member['file_name'] for member in group['members']))
    member_previews = st.columns(4)
    for index, member in enumerate(group['members']):
        with member_previews[index % 4]:
            show_thumbnail(member)
    member_ids = {member['id'] for member in group['members']}
    available = [label for label, media_id in options.items() if media_id not in member_ids]
    add_labels = st.multiselect("添加成员", available, key=f"add_{group['group_id']}")
    if st.button("添加所选成员", key=f"add_button_{group['group_id']}"):
        add_group_members(group['group_id'], [options[label] for label in add_labels])
        st.rerun()
    for member in group['members']:
        col_a, col_b = st.columns([5, 1])
        col_a.caption(f"{member['file_name']} · {member['relation_type']}")
        if col_b.button("移除", key=f"remove_{group['group_id']}_{member['id']}"):
            remove_group_member(group['group_id'], member['id'])
            st.rerun()
