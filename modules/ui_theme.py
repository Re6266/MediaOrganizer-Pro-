"""统一界面主题：把 prototype 的立体主义视觉语言映射到 Streamlit 组件。

只改样式，不改业务逻辑与数据流，因此不影响既有页面结构与后续模块计划。
"""

import streamlit as st

# 设计令牌与 prototype/cubism.css 保持一致
CANVAS = "#e8dcc8"
PAPER = "#f3eadb"
SIDEBAR = "#ddd0b8"
INK = "#5c4033"
INK_SOFT = "#705648"
BLUE = "#3d5c6e"
RED = "#9b3d25"
SHADOW = "#8b7355"
LINE_SOFT = "#b9a78b"

_CSS = """
<style>
:root {
  --mo-canvas: #e8dcc8;
  --mo-paper: #f3eadb;
  --mo-sidebar: #ddd0b8;
  --mo-ink: #5c4033;
  --mo-blue: #3d5c6e;
  --mo-red: #9b3d25;
  --mo-shadow: #8b7355;
  --mo-soft: #b9a78b;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--mo-canvas) !important;
  color: var(--mo-ink);
  font-family: 'Microsoft YaHei UI', 'Noto Sans SC', 'PingFang SC', sans-serif;
  font-size: 14px;
}
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1360px; }

/* 标题层级 */
h1, h2, h3, h4, h5 { color: var(--mo-ink) !important; font-weight: 800 !important; letter-spacing: -0.4px; }
h1 { font-size: 30px !important; }
h2 { font-size: 22px !important; }
h3 { font-size: 18px !important; }
p, li, label, span, div { color: var(--mo-ink); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
  color: var(--mo-ink) !important; font-family: Consolas, 'Microsoft YaHei UI', monospace;
  font-size: 12px !important; opacity: .85;
}

/* 侧边栏 */
[data-testid="stSidebar"] {
  background: var(--mo-sidebar) !important;
  border-right: 2px solid var(--mo-ink);
  box-shadow: 4px 0 0 var(--mo-soft);
}
[data-testid="stSidebar"] * { color: var(--mo-ink); }
[data-testid="stSidebarNav"] { padding-top: 6px; }
[data-testid="stSidebarNav"] ul { gap: 6px; }
[data-testid="stSidebarNav"] a {
  border: 2px solid transparent; border-radius: 0 !important;
  padding: 6px 10px; font-weight: 600; font-size: 13px;
}
[data-testid="stSidebarNav"] a:hover { background: var(--mo-canvas); border-color: var(--mo-shadow); }
[data-testid="stSidebarNav"] a[aria-current="page"] {
  background: var(--mo-ink); border-color: var(--mo-ink);
  box-shadow: 3px 3px 0 var(--mo-shadow);
}
[data-testid="stSidebarNav"] a[aria-current="page"] span { color: var(--mo-paper) !important; font-weight: 800; }

/* 按钮 */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button,
button[data-testid="baseButton-secondary"], button[data-testid="baseButton-primary"] {
  border-radius: 0 !important;
  border: 2px solid var(--mo-ink) !important;
  background: var(--mo-canvas) !important;
  color: var(--mo-ink) !important;
  font-weight: 800 !important;
  letter-spacing: .4px;
  box-shadow: 3px 3px 0 var(--mo-shadow) !important;
  transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
  min-height: 42px;
}
.stButton > button:hover, .stFormSubmitButton > button:hover,
button[data-testid="baseButton-secondary"]:hover, button[data-testid="baseButton-primary"]:hover {
  transform: translate(2px, 2px);
  box-shadow: 1px 1px 0 var(--mo-shadow) !important;
  background: var(--mo-sidebar) !important;
  color: var(--mo-ink) !important;
  border-color: var(--mo-ink) !important;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"],
button[data-testid="baseButton-primary"] {
  background: var(--mo-ink) !important;
  color: var(--mo-paper) !important;
  box-shadow: 4px 4px 0 var(--mo-shadow) !important;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
  background: var(--mo-blue) !important; color: var(--mo-paper) !important;
}
.stButton > button:focus, .stFormSubmitButton > button:focus {
  outline: 3px solid var(--mo-red) !important; outline-offset: 3px;
}

/* 输入控件 */
input, textarea, [data-baseweb="input"], [data-baseweb="textarea"],
[data-baseweb="select"] > div, .stDateInput [data-baseweb="input"] {
  border-radius: 0 !important;
  border: 2px solid var(--mo-shadow) !important;
  background: var(--mo-paper) !important;
  color: var(--mo-ink) !important;
  box-shadow: none !important;
}
input:focus, textarea:focus, [data-baseweb="input"]:focus-within,
[data-baseweb="select"] > div:focus-within {
  border-color: var(--mo-red) !important;
  box-shadow: 3px 3px 0 var(--mo-red) !important;
}
[data-baseweb="tag"] {
  border-radius: 0 !important; background: var(--mo-blue) !important;
  border: 2px solid var(--mo-ink) !important;
}
[data-baseweb="tag"] span { color: var(--mo-paper) !important; font-weight: 700; }
[data-baseweb="popover"], [data-baseweb="menu"] { border-radius: 0 !important; }
label, .stSelectbox label, .stTextInput label, .stMultiSelect label, .stSlider label {
  font-weight: 800 !important; font-size: 12px !important;
  letter-spacing: .3px; text-transform: uppercase;
}

/* 指标卡 */
[data-testid="stMetric"] {
  background: var(--mo-paper);
  border: 2px solid var(--mo-ink);
  box-shadow: 5px 5px 0 var(--mo-shadow);
  padding: 14px 16px;
}
[data-testid="stMetricLabel"] p {
  font-size: 11px !important; font-weight: 800 !important;
  letter-spacing: 1px; text-transform: uppercase; color: var(--mo-ink) !important;
}
[data-testid="stMetricValue"] {
  color: var(--mo-red) !important; font-weight: 900 !important;
  font-size: 30px !important; line-height: 1.2;
}

/* 折叠面板 */
[data-testid="stExpander"] details {
  border: 2px solid var(--mo-ink) !important;
  border-radius: 0 !important;
  background: var(--mo-paper) !important;
  box-shadow: 4px 4px 0 var(--mo-shadow);
}
[data-testid="stExpander"] summary { font-weight: 800 !important; }
[data-testid="stExpander"] summary:hover { color: var(--mo-red) !important; }

/* 图片：硬边框 + 偏移阴影 */
[data-testid="stImage"] img {
  border: 2px solid var(--mo-ink);
  box-shadow: 3px 3px 0 var(--mo-shadow);
  border-radius: 0 !important;
}

/* 提示条 */
[data-testid="stAlert"] {
  border-radius: 0 !important;
  border: 2px solid var(--mo-ink) !important;
  box-shadow: 3px 3px 0 var(--mo-shadow);
  background: var(--mo-paper) !important;
}
[data-testid="stAlert"] p { color: var(--mo-ink) !important; font-weight: 600; }
[data-testid="stNotification"] { border-radius: 0 !important; }

/* 表格 */
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border: 2px solid var(--mo-ink); box-shadow: 4px 4px 0 var(--mo-shadow);
}

/* 分隔线、滑杆 */
hr { border-color: var(--mo-ink) !important; border-width: 2px !important; opacity: 1 !important; }
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
  border: 2px solid var(--mo-ink) !important; background: var(--mo-red) !important;
  border-radius: 0 !important;
}
[data-testid="stSlider"] [data-testid="stTickBar"] { color: var(--mo-ink); }

/* 代码块与路径展示 */
code, pre, .stCode { border-radius: 0 !important; }
pre { border: 2px solid var(--mo-shadow) !important; background: var(--mo-sidebar) !important; }
code { color: var(--mo-ink) !important; background: var(--mo-sidebar) !important; }

/* 标签页 */
[data-testid="stTabs"] button { font-weight: 800; letter-spacing: .4px; }
[data-testid="stTabs"] [aria-selected="true"] { color: var(--mo-red) !important; }

/* 表格行悬停提示 */
[data-testid="stToast"] { border-radius: 0 !important; border: 2px solid var(--mo-ink) !important; }
</style>
"""


def apply_theme(page_title, page_icon="🗂️", layout="wide"):
    """设置页面基础配置并注入统一主题，应在每个页面开头调用一次。"""
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(eyebrow, title, subtitle=""):
    """页面头：小号红字导语 + 大标题 + 等宽副标题。"""
    subtitle_html = (
        f'<div style="font-family:Consolas,\'Microsoft YaHei UI\',monospace;'
        f'font-size:12px;margin-top:6px;opacity:.85">{subtitle}</div>'
    ) if subtitle else ""
    st.markdown(
        f'<div style="margin-bottom:26px">'
        f'<div style="font-size:10px;font-weight:800;letter-spacing:2px;'
        f'color:{RED};text-transform:uppercase;margin-bottom:8px">{eyebrow}</div>'
        f'<div style="font-size:40px;font-weight:900;letter-spacing:-1.4px;'
        f'line-height:1.25;color:{INK}">{title}</div>'
        f'{subtitle_html}</div>',
        unsafe_allow_html=True,
    )


def section_label(text, hint=""):
    """区块小标题：左侧竖条 + 标签，hint 为右侧说明。"""
    hint_html = (
        f'<span style="font-family:Consolas,monospace;font-size:11px;'
        f'font-weight:600;margin-left:14px;opacity:.75">{hint}</span>'
    ) if hint else ""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin:26px 0 12px">'
        f'<span style="width:6px;height:16px;background:{RED};display:inline-block"></span>'
        f'<span style="font-size:13px;font-weight:800;letter-spacing:1px;'
        f'text-transform:uppercase">{text}</span>{hint_html}</div>',
        unsafe_allow_html=True,
    )
