"""Shared dark theme: CSS injection + small HTML helpers for card-style panels."""

import html as _html

import streamlit as st


def esc(value) -> str:
    """Escape user- or computation-derived text before it goes into raw HTML."""
    return _html.escape(str(value))

_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg-app:#1B1B1B;
  --bg-sidebar:#181818;
  --bg-panel:#212121;
  --bg-panel-2:#262626;
  --bg-key:#2A2A2A;
  --bg-key-hover:#363636;
  --accent:#5DCBFF;
  --accent-dim:#2B3E47;
  --on-accent:#08222B;
  --text-primary:#F2F2F2;
  --text-secondary:#A3A3A3;
  --text-muted:#6C6C6C;
  --border:#333333;
  --border-soft:#2A2A2A;
  --red:#FF7A7A;
  --red-bg:#3A2222;
  --amber:#FFC46B;
  --amber-bg:#3A2E15;
  --shift:#F5A623;
  --alpha:#E8574B;
  --del-bg:#3C7A52;
  --ac-bg:#A8433A;
  --lcd-bg:#C8D6C2;
  --lcd-bg-2:#BCCBB5;
  --lcd-text:#16220F;
  --lcd-text-dim:#4B5A46;
  --lcd-border:#8FA88A;
  --font-ui:'Inter', sans-serif;
  --font-mono:'IBM Plex Mono', monospace;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background: var(--bg-app) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stMain"] .block-container { padding-top: 2.5rem; max-width: 900px; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
  background: var(--bg-sidebar) !important;
  border-right: 1px solid var(--border-soft);
}
[data-testid="stSidebar"] * { color: var(--text-secondary); }
.sidebar-brand {
  display:flex; align-items:center; gap:10px; padding: 4px 2px 18px;
}
.sidebar-brand .mark {
  width:30px; height:30px; border-radius:8px; flex:none;
  background: var(--accent); color: var(--on-accent);
  display:flex; align-items:center; justify-content:center;
  font-family: var(--font-mono); font-weight:600; font-size:15px;
}
.sidebar-brand .name { font-size:15px; font-weight:600; color: var(--text-primary); margin:0; }
.sidebar-brand .tag { font-size:10.5px; color: var(--text-muted); font-family: var(--font-mono); margin:1px 0 0; }

[data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px; }
[data-testid="stSidebar"] div[role="radiogroup"] label {
  padding: 9px 10px; border-radius: 7px; margin: 0 !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background: var(--bg-panel);
}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: var(--accent-dim);
}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
  color: var(--accent) !important; font-weight: 600;
}

/* ---------- Page header ---------- */
.page-eyebrow { font-family: var(--font-mono); font-size:11px; color: var(--accent); margin:0 0 6px; letter-spacing:0.3px; }
.page-title { font-size:22px; font-weight:600; margin:0 0 6px; color: var(--text-primary); }
.page-desc { color: var(--text-secondary); font-size:13px; margin:0 0 20px; max-width:640px; }

/* ---------- Card containers (st.container(key=...)) ---------- */
div[class*="st-key-"][class*="-card"] {
  background: var(--bg-panel);
  border: 1px solid var(--border-soft) !important;
  border-radius: 12px;
  padding: 18px 20px;
  margin-bottom: 14px;
}

/* ---------- Buttons (keypad etc.) ---------- */
.stButton > button {
  background: var(--bg-key) !important;
  color: var(--text-primary) !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: var(--font-mono) !important;
  font-size: 14.5px !important;
  padding: 13px 0 !important;
  transition: background 0.1s ease;
}
.stButton > button:hover { background: var(--bg-key-hover) !important; color: var(--accent) !important; }
.stButton > button:focus:not(:active) { border-color: var(--accent) !important; color: var(--text-primary) !important; }

/* ---------- Inputs ---------- */
.stTextInput input, .stNumberInput input {
  background: var(--bg-app) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border) !important;
  border-radius: 9px !important;
  font-family: var(--font-mono) !important;
  font-size: 15px !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 1px var(--accent) !important;
}
.stTextInput label, .stNumberInput label, .stSelectbox label, .stRadio label {
  font-family: var(--font-mono) !important;
  font-size: 11.5px !important;
  color: var(--text-secondary) !important;
}

/* ---------- Selectbox ---------- */
[data-baseweb="select"] > div {
  background: var(--bg-app) !important;
  border-color: var(--border) !important;
  border-radius: 8px !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 18px; border-bottom: 1px solid var(--border-soft); }
.stTabs [data-baseweb="tab"] {
  font-family: var(--font-ui) !important; font-size:13px; color: var(--text-muted);
  background: transparent !important;
}
.stTabs [aria-selected="true"] {
  color: var(--text-primary) !important;
  border-bottom-color: var(--accent) !important;
}
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--accent) !important; }

/* ---------- Radio (area type etc.) as pill row, main content only ---------- */
[data-testid="stMain"] .stRadio div[role="radiogroup"] { flex-direction: row !important; flex-wrap: wrap; gap: 8px; }
[data-testid="stMain"] .stRadio div[role="radiogroup"] label {
  border: 1px solid var(--border); border-radius: 999px; padding: 6px 14px !important;
  background: var(--bg-panel-2);
}
[data-testid="stMain"] .stRadio div[role="radiogroup"] label:has(input:checked) {
  background: var(--accent); border-color: var(--accent);
}
[data-testid="stMain"] .stRadio div[role="radiogroup"] label:has(input:checked) p { color: var(--on-accent) !important; font-weight:600; }

/* ---------- Alerts ---------- */
[data-testid="stAlertContentError"] { font-family: var(--font-ui); }
[data-testid="stNotificationContentError"], [data-testid="stAlertContainer"] { border-radius: 8px !important; }

/* ---------- Result / display helpers ---------- */
.calc-display {
  background: var(--bg-app); border: 1px solid var(--border-soft); border-radius: 10px;
  padding: 22px 20px 18px; margin-bottom: 4px;
}
.calc-hist-line { font-family: var(--font-mono); font-size:13px; color: var(--text-muted); text-align:right; margin:0 0 6px; word-break:break-all; }
.calc-result { font-family: var(--font-mono); font-size:30px; font-weight:600; color: var(--text-primary); text-align:right; word-break:break-all; line-height:1.15; }
.card-label { font-size:10.5px; color: var(--text-muted); margin:0 0 10px; font-family: var(--font-mono); letter-spacing:0.2px; text-transform:uppercase; }
.chip { display:inline-block; font-family: var(--font-mono); font-size:10.5px; padding:3px 9px; border-radius:999px; background: var(--accent-dim); color: var(--accent); }
.note { border-left:2px solid var(--amber); background: var(--amber-bg); padding:12px 14px; font-size:12px; color: var(--text-secondary); margin-top:14px; border-radius:0 8px 8px 0; }
.note.err { border-color: var(--red); background: var(--red-bg); }
.note strong { color: var(--text-primary); font-weight:600; }

/* ---------- LCD screen (Casio-style display) ---------- */
.lcd {
  background: linear-gradient(180deg, var(--lcd-bg), var(--lcd-bg-2));
  border: 1px solid var(--lcd-border); border-radius: 6px;
  padding: 16px 18px 14px; margin-bottom: 4px;
  box-shadow: inset 0 1px 4px rgba(0,0,0,0.25);
}
.lcd-status { display:flex; justify-content:flex-end; gap:10px; margin-bottom:6px; }
.lcd-status .ind { font-family: var(--font-mono); font-size:9.5px; letter-spacing:0.5px; color: var(--lcd-text-dim); font-weight:600; }
.lcd-hist { font-family: var(--font-mono); font-size:13px; color: var(--lcd-text-dim); text-align:right; margin:0 0 4px; word-break:break-all; min-height:16px; }
.lcd-result { font-family: var(--font-mono); font-size:28px; font-weight:600; color: var(--lcd-text); text-align:right; word-break:break-all; line-height:1.2; min-height:34px; }

/* ---------- Keyed buttons (st.container(key=...)) ---------- */
div[class*="st-key-key-del"] .stButton > button {
  background: var(--del-bg) !important; color: #fff !important; font-family: var(--font-ui) !important; font-weight:600 !important;
}
div[class*="st-key-key-ac"] .stButton > button {
  background: var(--ac-bg) !important; color: #fff !important; font-family: var(--font-ui) !important; font-weight:600 !important;
}
div[class*="st-key-key-eq"] .stButton > button {
  background: var(--accent) !important; color: var(--on-accent) !important; font-weight:700 !important;
}
</style>
"""


def inject() -> None:
    st.html(_CSS)


def sidebar_brand(app_name: str, tag: str) -> None:
    with st.sidebar:
        st.html(
            f'<div class="sidebar-brand">'
            f'<div class="mark">&sum;</div>'
            f'<div><p class="name">{app_name}</p><p class="tag">{tag}</p></div>'
            f'</div>'
        )


def page_header(eyebrow: str, title: str, desc: str) -> None:
    st.html(
        f'<div class="page-head">'
        f'<p class="page-eyebrow">{eyebrow}</p>'
        f'<h2 class="page-title">{title}</h2>'
        f'<p class="page-desc">{desc}</p>'
        f'</div>'
    )


def card(key: str, border: bool = False):
    """A themed container. `key` becomes a CSS hook, so suffix it with '-card'."""
    return st.container(key=key, border=border)


def result_display(hist_line: str, result_html: str) -> None:
    st.html(
        f'<div class="calc-display">'
        f'<p class="calc-hist-line">{hist_line}</p>'
        f'<div class="calc-result">{result_html}</div>'
        f'</div>'
    )


def lcd_display(prev_line: str, curr_line: str) -> None:
    """A Casio-style LCD screen: light background, two-line right-aligned mono text."""
    st.html(
        f'<div class="lcd">'
        f'<div class="lcd-status"><span class="ind">MATH</span></div>'
        f'<p class="lcd-hist">{prev_line}</p>'
        f'<div class="lcd-result">{curr_line or "0"}</div>'
        f'</div>'
    )


def note(html: str, err: bool = False) -> None:
    cls = "note err" if err else "note"
    st.html(f'<div class="{cls}">{html}</div>')


def chip(text: str) -> str:
    return f'<span class="chip">{text}</span>'
