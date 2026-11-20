"""统一界面主题：把 prototype/MediaOrganizer-Pro-浅色简洁版.html 的视觉语言映射到 Streamlit。

只改样式，不改业务逻辑与数据流，因此不影响既有页面结构与后续模块计划。
设计令牌（--ink/--green/--mint/--line/--bg/--shadow）与原型 :root 保持一致。
"""

import streamlit as st

# 与 prototype/MediaOrganizer-Pro-浅色简洁版.html 的 :root 一致
INK = "#24332f"
MUTED = "#909996"
GREEN = "#27836a"
GREEN_DARK = "#176850"
MINT = "#e8f3ed"
LINE = "#e8ece9"
BG = "#f6f8f7"
WHITE = "#ffffff"
SHADOW = "0 8px 28px rgba(38,59,46,.06)"
LINE_SOFT = "#e2e8e3"

_CSS = """
<style>
:root {
  --mo-ink: #24332f;
  --mo-muted: #909996;
  --mo-green: #27836a;
  --mo-green-dark: #176850;
  --mo-mint: #e8f3ed;
  --mo-line: #e8ece9;
  --mo-line-soft: #e2e8e3;
  --mo-bg: #f6f8f7;
  --mo-white: #ffffff;
  --mo-shadow: 0 8px 28px rgba(38,59,46,.06);
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--mo-bg) !important;
  color: var(--mo-ink);
  font-family: 'Noto Sans SC', 'Microsoft YaHei', 'PingFang SC', sans-serif;
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
}
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }

/* 标题层级：h1 26/600，h2 17/600，h3 14 */
h1, h2, h3, h4, h5 { color: var(--mo-ink) !important; }
h1 { font-size: 26px !important; font-weight: 600 !important; letter-spacing: -.6px; }
h2 { font-size: 17px !important; font-weight: 600 !important; }
h3 { font-size: 14px !important; font-weight: 600 !important; }
p, li, label, span, div { color: var(--mo-ink); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
  color: var(--mo-muted) !important; font-size: 11px !important; line-height: 1.9;
}

/* 侧边栏：白底 + 右侧细线 */
[data-testid="stSidebar"] {
  background: var(--mo-white) !important;
  border-right: 1px solid var(--mo-line);
  box-shadow: none !important;
}
[data-testid="stSidebar"] * { color: #5f7266; }
[data-testid="stSidebarNav"] { padding-top: 10px; }
[data-testid="stSidebarNav"] ul { gap: 3px; }
[data-testid="stSidebarNav"] a {
  border-radius: 7px !important;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 500;
  transition: background .18s, color .18s;
}
[data-testid="stSidebarNav"] a:hover { background: #f4f8f5; }
[data-testid="stSidebarNav"] a[aria-current="page"] {
  background: var(--mo-mint);
}
[data-testid="stSidebarNav"] a[aria-current="page"] span {
  color: var(--mo-green-dark) !important; font-weight: 600;
}

/* 按钮：白底细边 / 主按钮绿底 */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button,
button[data-testid="baseButton-secondary"], button[data-testid="baseButton-primary"] {
  border-radius: 7px !important;
  border: 1px solid #dde5df !important;
  background: var(--mo-white) !important;
  color: var(--mo-ink) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  box-shadow: none !important;
  min-height: 38px;
  transition: background .18s, border-color .18s;
}
.stButton > button:hover, .stFormSubmitButton > button:hover,
button[data-testid="baseButton-secondary"]:hover, button[data-testid="baseButton-primary"]:hover {
  background: #f7faf7 !important;
  border-color: #cadbd0 !important;
  color: var(--mo-green-dark) !important;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"],
button[data-testid="baseButton-primary"] {
  background: var(--mo-green) !important;
  border-color: var(--mo-green) !important;
  color: #fff !important;
  font-weight: 500 !important;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
  background: var(--mo-green-dark) !important;
  border-color: var(--mo-green-dark) !important;
  color: #fff !important;
}
.stButton > button:focus-visible, .stFormSubmitButton > button:focus-visible {
  outline: 3px solid #67b49b !important; outline-offset: 2px;
}

/* 输入控件 */
input, textarea, [data-baseweb="input"], [data-baseweb="textarea"],
[data-baseweb="select"] > div, .stDateInput [data-baseweb="input"] {
  border-radius: 7px !important;
  border: 1px solid var(--mo-line-soft) !important;
  background: var(--mo-white) !important;
  color: #5d7465 !important;
  box-shadow: none !important;
}
input:focus, textarea:focus, [data-baseweb="input"]:focus-within,
[data-baseweb="select"] > div:focus-within {
  border-color: #91b29e !important;
  box-shadow: 0 0 0 3px #eef4ee !important;
}
[data-baseweb="tag"] {
  border-radius: 4px !important; background: var(--mo-mint) !important;
  border: 1px solid #d7e6dc !important;
}
[data-baseweb="tag"] span { color: var(--mo-green-dark) !important; font-weight: 500; }
[data-baseweb="popover"], [data-baseweb="menu"] { border-radius: 8px !important; }
label, .stSelectbox label, .stTextInput label, .stMultiSelect label, .stSlider label {
  font-weight: 500 !important; font-size: 12px !important; color: #6a7f73 !important;
}

/* 指标卡：白卡 + 细边 + 极淡投影 */
[data-testid="stMetric"] {
  background: var(--mo-white);
  border: 1px solid var(--mo-line);
  border-radius: 10px;
  box-shadow: var(--mo-shadow);
  padding: 16px 18px;
}
[data-testid="stMetricLabel"] p {
  font-size: 10px !important; font-weight: 500 !important;
  color: var(--mo-muted) !important; letter-spacing: .2px;
}
[data-testid="stMetricValue"] {
  color: var(--mo-ink) !important; font-weight: 600 !important;
  font-size: 22px !important; line-height: 1.3; letter-spacing: -.7px;
}

/* 折叠面板 */
[data-testid="stExpander"] details {
  border: 1px solid var(--mo-line) !important;
  border-radius: 10px !important;
  background: var(--mo-white) !important;
  box-shadow: var(--mo-shadow);
}
[data-testid="stExpander"] summary { font-weight: 500 !important; font-size: 12px !important; }
[data-testid="stExpander"] summary:hover { color: var(--mo-green-dark) !important; }

/* 图片：圆角，无硬边 */
[data-testid="stImage"] img {
  border-radius: 9px !important;
  border: 1px solid var(--mo-line);
  box-shadow: var(--mo-shadow);
}

/* 提示条：浅绿 notice 风格 */
[data-testid="stAlert"] {
  border-radius: 8px !important;
  border: 1px solid #e0eade !important;
  background: #edf4eb !important;
  box-shadow: none;
}
[data-testid="stAlert"] p { color: #6d8a65 !important; font-size: 11px !important; line-height: 1.8; }
[data-testid="stNotification"] { border-radius: 9px !important; }

/* 表格 */
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border: 1px solid var(--mo-line); border-radius: 10px; overflow: hidden;
  box-shadow: var(--mo-shadow);
}

/* 分隔线、滑杆 */
hr { border-color: var(--mo-line) !important; border-width: 1px !important; opacity: 1 !important; }
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
  border: 2px solid #fff !important; background: var(--mo-green) !important;
  box-shadow: 0 2px 8px rgba(39,131,106,.35) !important;
}
[data-testid="stSlider"] [data-testid="stTickBar"] { color: var(--mo-muted); }
[data-testid="stSlider"] [data-baseweb="slider"] > div > div { background: var(--mo-green) !important; }

/* 代码块与路径展示 */
code, pre, .stCode { border-radius: 7px !important; }
pre { border: 1px solid var(--mo-line) !important; background: #f7f9f7 !important; }
code { color: #4c8064 !important; background: #f1f5ef !important; }

/* 标签页 */
[data-testid="stTabs"] button { font-size: 12px; font-weight: 500; }
[data-testid="stTabs"] [aria-selected="true"] { color: var(--mo-green-dark) !important; }

/* 复选框 / 单选框 */
[data-testid="stCheckbox"] label span, [data-testid="stRadio"] label span {
  font-size: 12px !important;
}
[data-baseweb="checkbox"] [aria-checked="true"] > div,
[data-baseweb="radio"] [aria-checked="true"] > div {
  background-color: var(--mo-green) !important; border-color: var(--mo-green) !important;
}
[data-testid="stToast"] { border-radius: 9px !important; border: 1px solid var(--mo-line) !important; }
</style>
"""


def apply_theme(page_title, page_icon="🗂️", layout="wide"):
    """设置页面基础配置并注入统一主题，应在每个页面开头调用一次。"""
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(eyebrow, title, subtitle=""):
    """页面头：绿色导语 + 26px 标题 + 灰色副标题（对应原型 .page-heading）。"""
    subtitle_html = (
        f'<div style="font-size:11px;color:{MUTED};line-height:1.9;margin-top:8px;'
        f'max-width:760px">{subtitle}</div>'
    ) if subtitle else ""
    st.markdown(
        f'<div style="margin-bottom:26px">'
        f'<div style="font-size:10px;font-weight:600;letter-spacing:2px;'
        f'color:#6b9375;margin-bottom:10px">{eyebrow}</div>'
        f'<div style="font-size:26px;font-weight:600;letter-spacing:-.6px;'
        f'line-height:1.4;color:{INK}">{title}</div>'
        f'{subtitle_html}</div>',
        unsafe_allow_html=True,
    )


def section_label(text, hint=""):
    """区块小标题：14px 标题 + 右侧 10px 说明（对应原型 .section-title）。"""
    hint_html = (
        f'<span style="font-size:10px;color:#a2ada4;margin-left:12px">{hint}</span>'
    ) if hint else ""
    st.markdown(
        f'<div style="display:flex;align-items:baseline;margin:30px 0 14px">'
        f'<span style="font-size:14px;font-weight:600;color:{INK}">{text}</span>'
        f'{hint_html}</div>',
        unsafe_allow_html=True,
    )


def hero_banner(kicker, title, description, action_hint=""):
    """首页横幅（对应原型 .hero）：浅绿渐变 + 装饰圆环。"""
    hint_html = (
        f'<div style="font-size:10px;color:#4e7754;margin-top:14px;'
        f'background:#ffffff60;border:1px solid #cbdcc9;border-radius:6px;'
        f'display:inline-block;padding:6px 10px">{action_hint}</div>'
    ) if action_hint else ""
    st.markdown(
        f'<div style="position:relative;overflow:hidden;'
        f'background:linear-gradient(105deg,#e8f1e8,#eef4e9 58%,#e1ede4);'
        f'border:1px solid #dfe9de;border-radius:12px;padding:24px 28px;'
        f'margin-bottom:22px">'
        f'<div style="height:290px;width:290px;border:1px solid rgba(199,216,199,.45);'
        f'border-radius:50%;position:absolute;right:40px;top:-110px"></div>'
        f'<div style="font-size:9px;letter-spacing:2px;color:#6b9375;'
        f'margin-bottom:10px;position:relative">{kicker}</div>'
        f'<div style="font-size:21px;font-weight:500;letter-spacing:.3px;'
        f'color:{INK};position:relative">{title}</div>'
        f'<div style="font-size:11px;color:#879b86;margin-top:10px;'
        f'max-width:620px;line-height:1.9;position:relative">{description}</div>'
        f'{hint_html}</div>',
        unsafe_allow_html=True,
    )
