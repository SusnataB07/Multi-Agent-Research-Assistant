import html
import importlib
import os
import re
import sys
from urllib.parse import urlparse

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

STEPS = {
    1: ("🔎", "Search", "Finding reliable sources"),
    2: ("📖", "Read", "Scraping the best source"),
    3: ("✍️", "Write", "Drafting the report"),
    4: ("🧐", "Critique", "Reviewing the report"),
}

EXAMPLES = [
    "Latest trends in generative AI for data analysts",
    "How does retrieval-augmented generation work?",
    "Impact of AI on supply chain management",
]

PROVIDERS = {
    "gemini": {
        "label": "Google Gemini",
        "model": "gemini-3.5-flash",
        "env_keys": ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        "hint": "aistudio.google.com/apikey",
    },
    "groq": {
        "label": "Groq",
        "model": "llama-3.3-70b-versatile",
        "env_keys": ("GROQ_API_KEY",),
        "hint": "console.groq.com/keys",
    },
    "mistral": {
        "label": "Mistral",
        "model": "mistral-small-2506",
        "env_keys": ("MISTRAL_API_KEY",),
        "hint": "console.mistral.ai",
    },
}

# ---------- Styling ----------
# Neutral surfaces use translucent greys so the design holds up in both
# Streamlit's light and dark themes. Two accents carry meaning:
# teal = progress / completion, amber = review.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap');

    :root {
        --signal: #0f9d9a;
        --signal-soft: rgba(15, 157, 154, .13);
        --amber: #d9a000;
        --line: rgba(127, 127, 127, .28);
        --surface: rgba(127, 127, 127, .06);
        --muted: rgba(127, 127, 127, .95);
    }

    /* Typography */
    .stApp, .stMarkdown, button, input, textarea, label, [data-testid="stSidebar"] {
        font-family: 'Bricolage Grotesque', system-ui, sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Bricolage Grotesque', system-ui, sans-serif !important;
        letter-spacing: -0.02em;
    }
    [data-baseweb="tab-panel"] .stMarkdown p,
    [data-baseweb="tab-panel"] .stMarkdown li {
        font-family: 'Source Serif 4', Georgia, serif;
        font-size: 1.06rem; line-height: 1.7;
        max-width: 74ch;
    }
    [data-baseweb="tab-panel"] .stMarkdown h1,
    [data-baseweb="tab-panel"] .stMarkdown h2,
    [data-baseweb="tab-panel"] .stMarkdown h3 { margin-top: 1.6rem; }

    /* Chrome */
    #MainMenu, footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}
    .block-container {padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1120px;}
    [data-testid="stSidebar"] {border-right: 1px solid var(--line);}
    [data-testid="stSidebar"] .block-container {padding-top: 1.6rem;}

    /* Masthead */
    .masthead {margin: 0 0 1.6rem;}
    .masthead .brand {
        display: inline-flex; align-items: center; gap: .5rem;
        font-weight: 700; font-size: 1.35rem; color: var(--signal);
        padding: .5rem 1.2rem; border: 1.5px solid var(--signal);
        border-radius: 999px; background: var(--signal-soft);
    }
    .masthead h1 {
        font-size: clamp(1.4rem, 2.2vw, 1.9rem); line-height: 1.25; font-weight: 600;
        margin: 1rem 0 .5rem; padding: 0; max-width: 36ch;
    }
    .masthead p {font-size: .95rem; line-height: 1.55; max-width: 64ch; color: var(--muted); margin: 0;}

    /* Input */
    .stTextInput input {
        font-size: 1.08rem; padding: .85rem 1rem; border-radius: 12px;
    }
    div[data-baseweb="input"] {border-radius: 12px; border-color: var(--line);}
    div[data-baseweb="input"]:focus-within {border-color: var(--signal); box-shadow: 0 0 0 3px var(--signal-soft);}
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: var(--signal); border: 1px solid var(--signal); color: #fff;
        font-weight: 600; height: 3.1rem; border-radius: 12px; transition: filter .15s;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {filter: brightness(1.08); color: #fff; border-color: var(--signal);}
    .stButton > button[kind="primary"]:disabled,
    .stButton > button[data-testid="stBaseButton-primary"]:disabled {opacity: .45;}
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"] {
        border-radius: 12px; border: 1px solid var(--line); background: var(--surface);
        text-align: left; font-weight: 500;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {border-color: var(--signal); color: var(--signal);}
    button:focus-visible {outline: 2px solid var(--signal) !important; outline-offset: 2px;}

    /* Pipeline tracker: the one memorable element */
    .pipe {display: grid; grid-template-columns: repeat(4, 1fr); margin: 1.6rem 0 .6rem;}
    .node {position: relative; padding-right: .8rem;}
    .node:not(:last-child)::before {
        content: ""; position: absolute; top: 17px; left: 46px; right: 10px; height: 2px;
        background: var(--line); border-radius: 2px;
    }
    .node.done:not(:last-child)::before {background: var(--signal);}
    .node.active:not(:last-child)::before {background: linear-gradient(90deg, var(--signal), var(--line));}
    .node .dot {
        width: 36px; height: 36px; border-radius: 50%; display: grid; place-items: center;
        border: 2px solid var(--line); font-size: .95rem; position: relative; z-index: 1;
        filter: grayscale(1); opacity: .65;
    }
    .node.active .dot {
        border-color: var(--signal); filter: none; opacity: 1;
        animation: ping 1.5s infinite;
    }
    .node.done .dot {
        background: var(--signal); border-color: var(--signal); color: #fff;
        font-weight: 700; filter: none; opacity: 1;
    }
    .node .t {font-weight: 600; font-size: 1rem; margin-top: .6rem;}
    .node .s {font-size: .82rem; color: var(--muted); margin-top: .1rem; line-height: 1.35;}
    .node.pending .t {opacity: .65;}
    @keyframes ping {
        0% {box-shadow: 0 0 0 0 rgba(15, 157, 154, .45);}
        70%, 100% {box-shadow: 0 0 0 10px rgba(15, 157, 154, 0);}
    }
    @media (prefers-reduced-motion: reduce) {.node.active .dot {animation: none;}}
    @media (max-width: 760px) {
        .pipe {grid-template-columns: repeat(2, 1fr); row-gap: 1.2rem;}
        .node::before {display: none;}
    }

    /* Results header + summary strip */
    .result-head {margin: 2.2rem 0 1rem; padding-top: 1.6rem; border-top: 1px solid var(--line);}
    .result-head h2 {font-size: 1.7rem; margin: 0; padding: 0; line-height: 1.2; max-width: 40ch;}
    .result-head .meta {color: var(--muted); font-size: .9rem; margin-top: .45rem;}
    .summary {
        display: grid; grid-template-columns: auto repeat(3, 1fr);
        border: 1px solid var(--line); border-radius: 16px; background: var(--surface);
        margin-bottom: 1.4rem; overflow: hidden;
    }
    .summary .cell {padding: 1.1rem 1.4rem; border-left: 1px solid var(--line); display: flex; flex-direction: column; justify-content: center;}
    .summary .cell:first-child {border-left: none; flex-direction: row; align-items: center; gap: 1rem;}
    .summary .v {font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1;}
    .summary .l {font-size: .85rem; color: var(--muted); margin-top: .25rem;}
    .summary .verdict {font-weight: 600; font-size: 1rem;}
    .ring {position: relative; width: 84px; height: 84px; display: grid; place-items: center; flex: none;}
    .ring .arc {
        position: absolute; inset: 0; border-radius: 50%;
        background: conic-gradient(var(--c) calc(var(--p) * 1%), rgba(127, 127, 127, .22) 0);
        -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 8px), #000 calc(100% - 7px));
        mask: radial-gradient(farthest-side, transparent calc(100% - 8px), #000 calc(100% - 7px));
    }
    .ring .n {font-size: 1.25rem; font-weight: 700; position: relative;}
    @media (max-width: 760px) {
        .summary {grid-template-columns: 1fr 1fr;}
        .summary .cell:first-child {grid-column: 1 / -1; border-bottom: 1px solid var(--line);}
        .summary .cell:nth-child(2) {border-left: none;}
    }

    /* Tabs */
    [data-baseweb="tab-list"] {gap: .4rem; border-bottom: 1px solid var(--line);}
    [data-baseweb="tab"] {font-weight: 600; padding: .6rem 1rem; height: auto;}
    [data-baseweb="tab-highlight"] {background: var(--signal) !important; height: 3px;}

    /* Sources */
    .src {
        display: block; padding: .8rem 1rem; margin-bottom: .5rem; text-decoration: none !important;
        border: 1px solid var(--line); border-radius: 12px; background: var(--surface);
        color: inherit !important; transition: border-color .15s;
    }
    .src:hover {border-color: var(--signal);}
    .src .d {display: block; font-weight: 600; font-size: .98rem;}
    .src .u {display: block; font-size: .8rem; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;}

    /* Sidebar */
    .side-title {font-weight: 700; font-size: 1.2rem; letter-spacing: -0.01em; margin-bottom: 1.2rem;}
    .side-label {font-size: .85rem; font-weight: 600; color: var(--muted); margin: 1rem 0 .35rem;}
    .side-note {font-size: .85rem; color: var(--muted); line-height: 1.45;}
    .status {display: flex; align-items: center; gap: .55rem; font-size: .88rem; padding: .3rem 0;}
    .status .dot {width: 9px; height: 9px; border-radius: 50%; background: #d1495b; flex: none;}
    .status.ok .dot {background: #2e9e6b;}
    .status-box {
        border: 1px solid var(--line); border-radius: 12px; background: var(--surface);
        padding: .5rem .9rem; margin-top: .9rem;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] details {border-radius: 12px; border-color: var(--line);}

    /* Empty state */
    .empty {
        border: 1.5px dashed var(--line); border-radius: 16px; padding: 1.3rem 1.5rem; margin: 1.2rem 0 .8rem;
    }
    .empty b {font-size: 1.05rem;}
    .empty p {margin: .3rem 0 0; color: var(--muted); font-size: .95rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="masthead">
        <span class="brand">🔎 Multi-Agent Research Assistant</span>
        <h1>Four agents turn a question into a sourced report.</h1>
        <p>One agent searches, one reads the best source, one writes the report,
        and one reviews it. You get the draft, a quality score, and every link used.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------- Helpers ----------
def set_topic(t: str):
    st.session_state["topic"] = t


def render_tracker(placeholder, states: dict, timings: dict):
    nodes = []
    for i, (icon, name, desc) in STEPS.items():
        state = states[i]
        mark = "✓" if state == "done" else icon
        sub = f"Done in {timings[i]:.1f}s" if i in timings else desc
        nodes.append(
            f'<div class="node {state}"><div class="dot">{mark}</div>'
            f'<div class="t">{name}</div><div class="s">{html.escape(sub)}</div></div>'
        )
    placeholder.markdown(f'<div class="pipe">{"".join(nodes)}</div>', unsafe_allow_html=True)


def parse_score(feedback: str):
    m = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", feedback)
    return float(m.group(1)) if m else None


def extract_sources(*texts: str):
    seen, out = set(), []
    for text in texts:
        for url in re.findall(r"https?://[^\s)\]>\"']+", text):
            url = url.rstrip(".,;")
            if url not in seen:
                seen.add(url)
                out.append(url)
    return out


def score_style(score):
    if score is None:
        return "#7f7f7f", "No score found"
    if score >= 8:
        return "#2e9e6b", "Ready to use"
    if score >= 6:
        return "#0f9d9a", "Solid draft"
    if score >= 4:
        return "#d9a000", "Needs revision"
    return "#d1495b", "Major gaps"


def render_summary(result: dict, score, sources: list):
    color, verdict = score_style(score)
    pct = min(score / 10, 1.0) * 100 if score is not None else 0
    num = f"{score:g}" if score is not None else "N/A"
    words = len(result["report"].split())
    st.markdown(
        f"""
        <div class="summary">
            <div class="cell">
                <div class="ring" style="--p:{pct:.0f}; --c:{color};">
                    <div class="arc"></div><div class="n">{num}</div>
                </div>
                <div><div class="verdict">{verdict}</div><div class="l">Critic score out of 10</div></div>
            </div>
            <div class="cell"><div class="v">{result['elapsed']:.1f}s</div><div class="l">Total time</div></div>
            <div class="cell"><div class="v">{words:,}</div><div class="l">Words in report</div></div>
            <div class="cell"><div class="v">{len(sources)}</div><div class="l">Sources found</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sources(sources: list):
    for url in sources:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "") or url
        safe_url = html.escape(url, quote=True)
        st.markdown(
            f'<a class="src" href="{safe_url}" target="_blank" rel="noopener noreferrer">'
            f'<span class="d">{html.escape(domain)}</span>'
            f'<span class="u">{html.escape(url)}</span></a>',
            unsafe_allow_html=True,
        )


def status_row(ok: bool, text: str) -> str:
    return f'<div class="status {"ok" if ok else ""}"><span class="dot"></span>{html.escape(text)}</div>'


def load_pipeline(provider: str, model: str, user_key: str):
    """Apply the sidebar choices, then (re)load agents.py so the new model is used."""
    cfg = PROVIDERS[provider]
    os.environ["LLM_PROVIDER"] = provider
    os.environ["LLM_MODEL"] = model
    if user_key:
        os.environ[cfg["env_keys"][0]] = user_key
    signature = (provider, model, user_key)

    fresh = "agents" not in sys.modules
    agents = importlib.import_module("agents")
    pipeline = importlib.import_module("pipeline")
    if not fresh and getattr(agents, "_app_signature", None) != signature:
        agents = importlib.reload(agents)
        pipeline = importlib.reload(pipeline)
    agents._app_signature = signature
    return pipeline.research_pipeline_stream


# ---------- Sidebar ----------
if "history" not in st.session_state:
    st.session_state["history"] = []
if "env_defaults" not in st.session_state:
    _p = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    st.session_state["env_defaults"] = {
        "provider": _p if _p in PROVIDERS else "gemini",
        "model": os.getenv("LLM_MODEL", ""),
    }
env_defaults = st.session_state["env_defaults"]
if "provider" not in st.session_state:
    st.session_state["provider"] = env_defaults["provider"]

with st.sidebar:
    st.markdown('<div class="side-title">🔎 Research Assistant</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-label">Model provider</div>', unsafe_allow_html=True)
    provider = st.selectbox(
        "Model provider", list(PROVIDERS), key="provider",
        format_func=lambda p: PROVIDERS[p]["label"], label_visibility="collapsed",
    )
    cfg = PROVIDERS[provider]

    st.markdown('<div class="side-label">Model</div>', unsafe_allow_html=True)
    model_key = f"model_{provider}"
    if model_key not in st.session_state:
        st.session_state[model_key] = (
            env_defaults["model"] if provider == env_defaults["provider"] else ""
        )
    model = st.text_input(
        "Model", key=model_key, placeholder=cfg["model"], label_visibility="collapsed",
        help="Type any model name your provider supports. Leave empty to use the default.",
    ).strip() or cfg["model"]

    with st.expander("API key (optional)"):
        user_key = st.text_input(
            f"{cfg['label']} API key", type="password", key=f"apikey_{provider}",
            placeholder="Leave empty to use your .env file",
        ).strip()
        st.caption(f"Get a key at {cfg['hint']}. It is not saved to disk.")

    llm_ready = bool(user_key) or any(os.getenv(k) for k in cfg["env_keys"])
    search_ready = bool(os.getenv("TAVILY_API_KEY"))
    st.markdown(
        '<div class="status-box">'
        + status_row(llm_ready, f"{cfg['label']} key " + ("ready" if llm_ready else "missing"))
        + status_row(search_ready, "Tavily search key " + ("ready" if search_ready else "missing"))
        + "</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown('<div class="side-label" style="margin-top:0">Past runs</div>', unsafe_allow_html=True)
    history = st.session_state["history"]
    if history:
        labels = [f"{i + 1}. {h['topic'][:38]}" for i, h in enumerate(history)]
        pick = st.selectbox(
            "Open a past run", range(len(history)), format_func=lambda i: labels[i],
            label_visibility="collapsed",
        )
        c1, c2 = st.columns(2)
        if c1.button("Open", use_container_width=True):
            st.session_state["result"] = history[pick]
            st.rerun()
        if c2.button("Clear all", use_container_width=True):
            st.session_state["history"] = []
            st.session_state.pop("result", None)
            st.rerun()
    else:
        st.markdown(
            '<p class="side-note">Finished runs are saved here for this session.</p>',
            unsafe_allow_html=True,
        )

# ---------- Input ----------
in_col, btn_col = st.columns([5, 1.25], vertical_alignment="bottom")
with in_col:
    topic = st.text_input(
        "Research topic",
        key="topic",
        placeholder="e.g. Future of electric vehicles in India",
    )
with btn_col:
    run = st.button(
        "Run research", type="primary", disabled=not topic.strip(), use_container_width=True
    )

# ---------- Pipeline tracker ----------
tracker = st.empty()
note = st.empty()
existing = st.session_state.get("result")
if existing:
    render_tracker(
        tracker,
        {i: "done" for i in STEPS},
        {int(k): v for k, v in existing.get("timings", {}).items()},
    )
else:
    render_tracker(tracker, {i: "pending" for i in STEPS}, {})

# ---------- Run pipeline ----------
if run:
    try:
        research_pipeline_stream = load_pipeline(provider, model, user_key)
    except Exception as e:
        st.error(f"Could not load the pipeline or agents: {e}")
        st.stop()

    states = {i: "pending" for i in STEPS}
    timings = {}
    render_tracker(tracker, states, timings)

    try:
        final = None
        for ev in research_pipeline_stream(topic.strip()):
            if ev["status"] == "start":
                states[ev["step"]] = "active"
                note.info(f"{STEPS[ev['step']][0]} {STEPS[ev['step']][2]}...")
            elif ev["status"] == "done":
                states[ev["step"]] = "done"
                timings[ev["step"]] = ev["seconds"]
            elif ev["status"] == "complete":
                final = ev["state"]
            render_tracker(tracker, states, timings)
        note.empty()
        if final:
            final["llm"] = f"{cfg['label']} · {model}"
            st.session_state["result"] = final
            st.session_state["history"].append(final)
            st.toast("Research complete", icon="✅")
    except Exception as e:
        note.empty()
        st.error(f"Pipeline failed: {e}")
        msg = str(e).lower()
        if "429" in msg or "rate" in msg or "quota" in msg:
            st.warning(
                "Rate limit or quota hit. Wait a minute and try again, "
                "or pick another model provider in the sidebar."
            )
        elif "api key" in msg or "api_key" in msg or "401" in msg:
            st.warning("Check your API key in the sidebar or in the .env file.")

# ---------- Results ----------
result = st.session_state.get("result")
if result:
    score = parse_score(result["feedback"])
    sources = extract_sources(result["search_result"], result["report"])

    llm_note = result.get("llm")
    meta = f'<div class="meta">Generated with {html.escape(llm_note)}</div>' if llm_note else ""
    st.markdown(
        f'<div class="result-head"><h2>{html.escape(result["topic"])}</h2>{meta}</div>',
        unsafe_allow_html=True,
    )
    render_summary(result, score, sources)

    tab_report, tab_critic, tab_sources, tab_raw = st.tabs(
        ["📄 Report", "🧐 Critic feedback", f"🔗 Sources ({len(sources)})", "🛠️ Agent output"]
    )

    with tab_report:
        st.markdown(result["report"])
        st.write("")
        d1, d2, _ = st.columns([1, 1, 2])
        d1.download_button(
            "Download .md", result["report"], "research_report.md",
            "text/markdown", use_container_width=True,
        )
        d2.download_button(
            "Download .txt", result["report"], "research_report.txt",
            "text/plain", use_container_width=True,
        )

    with tab_critic:
        st.markdown(result["feedback"])

    with tab_sources:
        if sources:
            render_sources(sources)
        else:
            st.caption("No URLs were found in the agent output.")

    with tab_raw:
        with st.expander("Search agent output"):
            st.markdown(result["search_result"])
        with st.expander("Reader agent output"):
            st.markdown(result["scraped_content"])
        with st.expander("Step timings"):
            for i, secs in result["timings"].items():
                st.write(f"{STEPS[int(i)][0]} {STEPS[int(i)][1]}: {secs:.1f}s")
else:
    st.markdown(
        '<div class="empty"><b>Start with a topic</b>'
        "<p>Type a question above, or pick one of these to see how a run looks.</p></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(len(EXAMPLES))
    for col, example in zip(cols, EXAMPLES):
        col.button(example, on_click=set_topic, args=(example,), use_container_width=True, key=f"ex_{example}")
