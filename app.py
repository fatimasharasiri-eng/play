import html
import random
import re
import threading
import time

import streamlit as st

# ---------------- Settings ----------------
PHRASE, ENC_PHRASE, SHIFT = "YOU THE BEST", "BRX WKH EHVW", 3
WORD, ENC = PHRASE.replace(" ", ""), ENC_PHRASE.replace(" ", "")
HINT_PEN = 30  # hint penalty in seconds

Q = [
        {"q": "Which clustering algorithm can detect outliers and does not require specifying the number of clusters in advance?",
     "a": ["dbscan"], "n": 6, "h": "It starts with D and is based on density"},
   {"q": "Which clustering method uses a tree-like diagram to show how clusters are formed?",
    "a": ["dendrogram"], "n": 10, "h": "It starts with D and looks like a tree"},
    {"q": "Which unsupervised algorithm splits the data into K groups around centers called centroids?",
     "a": ["kmeans"], "n": 7, "h": "Starts with K and ends with “Means”"},
    {"q": "A supervised algorithm that classifies a new item by looking at its closest neighbors and taking a vote. What is its short name?",
     "a": ["knn", "knearestneighbors", "knearestneighbor"], "n": 3, "h": "Starts with K. It stands for “nearest neighbors”"},
    {"q": "A supervised algorithm that draws the best line (or plane) separating the classes with the widest possible margin from the nearest points. What is its short name (3 letters)?",
     "a": ["svm", "supportvectormachine", "supportvectormachines"], "n": 3, "h": "Short for Support Vector Machine"},
    {"q": "A supervised algorithm that decides through a chain of yes/no questions that branch out like a tree (e.g. “is age over 30?”). What is it called?",
     "a": ["decisiontree", "decisiontrees"], "n": 12, "h": "Two words. The first one is “Decision”"},
    {"q": "A large collection of decision trees where each tree gives its opinion and the final answer is decided by voting. What is this algorithm called?",
     "a": ["randomforest", "randomforests"], "n": 12, "h": "Starts with “Random”"},
    {"q": "A supervised algorithm that fits a straight line through the data to predict a number (e.g. house price from size). What is it called? (___ Regression)",
     "a": ["linearregression", "linear"], "n": 6, "h": "The missing word means “straight-line”"},
    {"q": "In K-Means, we plot the error against K and pick the K where the curve bends sharply, like an arm. What is this method called? (___ Method)",
     "a": ["elbow", "elbowmethod"], "n": 5, "h": "Think of the joint in the middle of your arm"},
    {"q": "Income ranges from 0 to 100000 while age ranges from 0 to 100, so income dominates the clustering. What should we apply to the features first? (Feature ___)",
     "a": ["scaling", "featurescaling", "scale", "normalization", "standardization", "normalize", "standardize"], "n": 7, "h": "Put all features on a similar range"},
]
N = len(Q)


def norm(s: str) -> str:
    return re.sub(r"[\s\-_.]", "", s.lower())


NA = [[norm(x) for x in q["a"]] for q in Q]


# ---------------- State shared by all devices ----------------
@st.cache_resource
def game():
    return {"lock": threading.Lock(), "status": "waiting", "start": None, "teams": {}}


G = game()


def fmt(sec):
    sec = int(sec)
    return f"{sec // 60:02d}:{sec % 60:02d}"


def elapsed(t):
    if t["finish"] is not None:
        return t["finish"]
    if G["start"] is None:
        return 0
    return time.time() - G["start"] + t["pen"]


def ranking():
    items = list(G["teams"].items())
    done = sorted([i for i in items if i[1]["finish"] is not None], key=lambda i: i[1]["finish"])
    rest = sorted([i for i in items if i[1]["finish"] is None], key=lambda i: (-i[1]["solved"], elapsed(i[1])))
    return done + rest


# ---------------- Page + styling ----------------
st.set_page_config(page_title="Lock Escape", layout="centered")
st.markdown(
    """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
:root{color-scheme:light;--bg:#f4f6fb;--panel:#ffffff;--line:rgba(15,23,42,.12);--tx:#0f172a;--mu:#64748b;--ac:#0d9488;--am:#d97706;--bad:#dc2626;
--mono:'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace}
html,body,.stApp{background:var(--bg)!important;color:var(--tx)}
.stApp,.stApp button,.stApp input{font-family:'Inter',system-ui,sans-serif!important}
.stApp{background-image:radial-gradient(ellipse 70% 40% at 50% -5%,rgba(13,148,136,.12),transparent),
linear-gradient(rgba(15,23,42,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(15,23,42,.045) 1px,transparent 1px);
background-size:auto,40px 40px,40px 40px;background-color:var(--bg)!important}
[data-testid="stHeader"]{background:transparent!important}
#MainMenu,footer,header [data-testid="stToolbar"],[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
.block-container{max-width:740px;padding-top:2.6rem;padding-bottom:4rem}

/* tabs */
.stTabs [data-baseweb="tab-list"]{gap:4px;border-bottom:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{height:44px;padding:0 18px;font-weight:600;color:var(--mu);font-size:.9rem;letter-spacing:.5px}
.stTabs [aria-selected="true"]{color:var(--tx)!important}
.stTabs [data-baseweb="tab-highlight"]{background:var(--ac)!important;height:2px}

/* hero */
.hero{text-align:center;margin:6px 0 26px}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);font-size:.7rem;letter-spacing:3px;text-transform:uppercase;color:var(--ac)}
.eyebrow::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--ac)}
.hero h1{font-size:2.7rem;font-weight:800;letter-spacing:-1.2px;line-height:1.1;margin:.6rem 0 .5rem;padding:0;color:var(--tx)}
.hero p{color:var(--mu);margin:0;font-size:1rem}

/* text helpers */
.h{font-size:.72rem;letter-spacing:2.5px;text-transform:uppercase;color:var(--mu);font-weight:600;margin:22px 0 10px}
.tx{color:var(--tx);line-height:1.6}

/* lock cells */
.locks{display:grid;grid-template-columns:repeat(10,1fr);gap:6px;margin:20px 0 14px}
.cell{aspect-ratio:1;border:1px solid var(--line);border-radius:10px;background:var(--panel);display:flex;align-items:center;justify-content:center;
font-family:var(--mono);font-size:.85rem;color:#94a3b8}
.cell.on{border-color:rgba(13,148,136,.7);background:rgba(13,148,136,.1);color:var(--ac);font-size:clamp(1rem,3.4vw,1.5rem);font-weight:700;
box-shadow:0 6px 16px -6px rgba(13,148,136,.45);animation:glow .7s ease-out}
@keyframes glow{0%{opacity:0;transform:scale(.85)}100%{opacity:1;transform:scale(1)}}

/* progress */
.pbar{height:3px;background:var(--line);border-radius:3px;overflow:hidden}
.pbar i{display:block;height:100%;background:var(--ac);transition:width .5s}
.pcap{display:flex;justify-content:space-between;font-family:var(--mono);font-size:.74rem;color:var(--mu);margin:8px 1px 20px}

/* clock */
.clock{display:flex;justify-content:space-between;align-items:center;border:1px solid var(--line);background:var(--panel);
border-radius:14px;padding:14px 20px;margin-bottom:4px;box-shadow:0 6px 20px -12px rgba(15,23,42,.2)}
.clock .l{font-family:var(--mono);font-size:.64rem;letter-spacing:2px;text-transform:uppercase;color:var(--mu)}
.clock .nm{font-weight:600;font-size:1.05rem;color:var(--tx);margin-top:2px}
.clock .tm{font-family:var(--mono);font-size:2rem;font-weight:700;color:var(--tx);text-align:right;font-variant-numeric:tabular-nums}
.clock .pn{font-family:var(--mono);font-size:.72rem;color:var(--am);text-align:right}

/* cards */
div[data-testid="stVerticalBlockBorderWrapper"]{border:1px solid var(--line)!important;border-radius:16px!important;
background:#fff;box-shadow:0 10px 30px -14px rgba(15,23,42,.2)}
.lk{font-family:var(--mono);font-size:.72rem;letter-spacing:2.5px;text-transform:uppercase;color:var(--ac);margin-bottom:12px}
.qtext{font-size:1.28rem;line-height:1.55;font-weight:500;color:var(--tx);margin-bottom:10px}
.hint{border-left:2px solid var(--am);background:rgba(217,119,6,.09);color:#92400e;padding:10px 14px;border-radius:0 8px 8px 0;margin:10px 0;font-size:.93rem}
.hint b{color:var(--am)}
.steps{counter-reset:s;list-style:none;padding:0;margin:4px 0 2px}
.steps li{counter-increment:s;position:relative;padding:9px 0 9px 42px;color:var(--tx);line-height:1.5}
.steps li::before{content:"0" counter(s);position:absolute;left:0;top:9px;font-family:var(--mono);font-size:.8rem;color:var(--ac)}

/* messages */
.msg{border-radius:10px;padding:10px 14px;margin:10px 0;font-size:.93rem}
.msg.bad{background:rgba(220,38,38,.07);border:1px solid rgba(220,38,38,.3);color:#991b1b}

/* cipher + result */
.cipher{display:flex;justify-content:center;gap:8px;margin:18px 0 12px}
.cipher i{width:14px}
.cipher span{width:40px;height:52px;display:flex;align-items:center;justify-content:center;border:1px solid rgba(217,119,6,.5);border-radius:10px;
background:rgba(217,119,6,.08);color:var(--am);font-family:var(--mono);font-size:1.6rem;font-weight:700}
.result{text-align:center;padding:30px 10px 22px}
.result .lbl{font-family:var(--mono);color:var(--ac);font-size:.72rem;letter-spacing:3px;text-transform:uppercase}
.result .big{font-family:var(--mono);font-size:4.2rem;font-weight:700;color:var(--ac);line-height:1.15;margin-top:6px;
font-variant-numeric:tabular-nums}

/* waiting */
.wait{text-align:center;padding:46px 10px;color:var(--mu)}
.ring{width:54px;height:54px;border-radius:50%;margin:0 auto 18px;border:2px solid rgba(13,148,136,.2);border-top-color:var(--ac);animation:spin 1.1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

/* stat cells */
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:10px 0 16px}
.stat{border:1px solid var(--line);background:var(--panel);border-radius:14px;padding:14px 18px}
.stat .k{font-family:var(--mono);font-size:.66rem;letter-spacing:2px;text-transform:uppercase;color:var(--mu)}
.stat .v{font-size:1.9rem;font-weight:700;color:var(--tx);margin-top:4px}

/* leaderboard */
.lb{width:100%;border-collapse:collapse}
.lb th{font-family:var(--mono);font-size:.64rem;letter-spacing:2px;text-transform:uppercase;color:var(--mu);text-align:left;font-weight:500;padding:6px 10px;border-bottom:1px solid var(--line)}
.lb td{padding:13px 10px;border-bottom:1px solid var(--line);color:var(--tx)}
.lb .rk{font-family:var(--mono);color:var(--mu);width:36px}
.lb tr.top .rk{color:var(--ac);font-weight:700}
.lb .t{font-family:var(--mono);font-weight:700;color:var(--tx);font-variant-numeric:tabular-nums}
.st{font-family:var(--mono);font-size:.72rem;letter-spacing:1px;display:inline-flex;align-items:center;gap:7px}
.st::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor}
.st.fin{color:var(--ac)}.st.pl{color:var(--am)}.st.wt{color:var(--mu)}
.empty{color:var(--mu);text-align:center;padding:22px}
.key div{font-family:var(--mono);font-size:.86rem;color:var(--tx);padding:3px 0}

/* inputs + buttons */
[data-testid="stForm"]{border:none!important;padding:0!important;background:transparent!important}
[data-testid="stWidgetLabel"] p{color:var(--mu)!important;font-size:.85rem}
div[data-baseweb="input"],div[data-baseweb="base-input"]{background:#fff!important;border-radius:10px!important}
div[data-baseweb="input"]{border:1px solid var(--line)!important}
div[data-baseweb="input"]:focus-within{border-color:var(--ac)!important;box-shadow:0 0 0 3px rgba(13,148,136,.18)}
.stTextInput input{color:#000!important;font-family:var(--mono)!important;font-size:1.05rem;font-weight:600;padding:13px 14px;-webkit-text-fill-color:#000;caret-color:#000}
.stTextInput input::placeholder{color:#6b7280;-webkit-text-fill-color:#6b7280;font-weight:400}
.stButton>button,.stFormSubmitButton>button{border-radius:10px;font-weight:600;font-size:.95rem;padding:.6rem 1.1rem;
background:transparent;color:var(--tx);border:1px solid var(--line);transition:all .15s}
.stButton>button:hover,.stFormSubmitButton>button:hover{border-color:var(--ac);color:var(--ac)}
button[kind^="primary"]{background:var(--ac)!important;color:#fff!important;border:none!important;font-weight:700!important;
box-shadow:0 8px 18px -8px rgba(13,148,136,.7)}
button[kind^="primary"]:hover{filter:brightness(1.08);color:#fff!important}
button[kind^="primary"]:disabled{opacity:.35;box-shadow:none}
[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:12px!important;background:var(--panel)}
[data-testid="stExpander"] summary{color:var(--tx)}
/* illustrations */
.art{display:flex;justify-content:center;margin-bottom:6px}
.bot{animation:flt 3.4s ease-in-out infinite}
@keyframes flt{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
.eye{transform-box:fill-box;transform-origin:center;animation:blink 4.2s infinite}
@keyframes blink{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}
.tw{transform-box:fill-box;transform-origin:center;animation:tw 2.4s ease-in-out infinite}
@keyframes tw{0%,100%{opacity:.2;transform:scale(.55)}50%{opacity:1;transform:scale(1)}}
.qhead{display:flex;justify-content:space-between;align-items:flex-start}
.mini{margin:-4px 0 0 8px;flex:none}
.row2{display:flex;justify-content:center;align-items:flex-end;gap:6px;margin-bottom:10px}
.cell{position:relative}
.cell svg{width:42%;height:auto}
.cell.on::after{content:"";position:absolute;top:-7px;right:-6px;width:15px;height:15px;
background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='-10 -10 20 20'%3E%3Cpath d='M0,-8 L2.2,-2.2 L8,0 L2.2,2.2 L0,8 L-2.2,2.2 L-8,0 L-2.2,-2.2 Z' fill='%23f59e0b'/%3E%3C/svg%3E") center/contain no-repeat}
/* alphabet chart */
.alphas{margin:6px 0 14px}
.alpha{display:grid;grid-template-columns:repeat(13,1fr);gap:4px;margin-bottom:8px}
.ac{display:flex;flex-direction:column;align-items:center;border:1px solid var(--line);border-radius:8px;background:var(--panel);
padding:5px 0;font-family:var(--mono);font-weight:700;font-size:.95rem}
.ac .ca{color:var(--am)}
.ac .pa{color:var(--ac);border-top:1px solid var(--line);width:100%;text-align:center;margin-top:4px;padding-top:4px}
.alegend{display:flex;gap:16px;font-family:var(--mono);font-size:.74rem;margin:10px 0 8px}
.alegend .ca{color:var(--am)}.alegend .pa{color:var(--ac)}
</style>""",
    unsafe_allow_html=True,
)



# ---------------- Illustrations (inline SVG) ----------------
STAR = "M0,-8 L2.2,-2.2 L8,0 L2.2,2.2 L0,8 L-2.2,2.2 L-8,0 L-2.2,-2.2 Z"
LOCK = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.9' stroke-linecap='round'>"
        "<rect x='5' y='11' width='14' height='10' rx='3'/><path d='M8 11V8a4 4 0 0 1 8 0v3'/></svg>")
KEY = ("<svg viewBox='0 0 64 64' width='46' fill='none' stroke='#d97706' stroke-width='5' stroke-linecap='round'>"
       "<circle cx='20' cy='32' r='11'/><circle cx='20' cy='32' r='2.5' fill='#d97706' stroke='none'/>"
       "<path d='M31 32H57M47 32V42M55 32V40'/></svg>")
TROPHY = ("<svg viewBox='0 0 64 64' width='84'>"
          "<path d='M20 10H44V26C44 35 38 40 32 40C26 40 20 35 20 26Z' fill='#f59e0b'/>"
          "<path d='M20 14H12C12 24 16 28 22 29M44 14H52C52 24 48 28 42 29' fill='none' stroke='#f59e0b' stroke-width='4' stroke-linecap='round'/>"
          "<rect x='29' y='40' width='6' height='9' fill='#d97706'/><rect x='20' y='49' width='24' height='7' rx='2.5' fill='#d97706'/>"
          "<g transform='translate(32,23) scale(1.1)'><path d='" + STAR + "' fill='#fff'/></g></svg>")


def robot(mood="idle", size=110, sparkle=False):
    teal, ink = "#0d9488", "#0f172a"
    top = (f"<line x1='60' y1='14' x2='60' y2='27' stroke='{teal}' stroke-width='3' stroke-linecap='round'/>"
           "<circle cx='60' cy='11' r='5' fill='#f59e0b'/>")
    if mood == "party":
        top = ("<polygon points='60,-3 46,27 74,27' fill='#f59e0b'/><polygon points='60,-3 54,12 66,12' fill='#fde68a'/>"
               f"<circle cx='60' cy='-4' r='4.5' fill='{teal}'/>")
    if mood == "party":
        eyes = (f"<path d='M44 53Q50 45 56 53M64 53Q70 45 76 53' stroke='{ink}' stroke-width='3' fill='none' stroke-linecap='round'/>")
        mouth = f"<path d='M51 58Q60 72 69 58Z' fill='{ink}'/>"
        arms = (f"<path d='M40 90Q20 92 15 74M80 90Q100 92 105 74' stroke='{teal}' stroke-width='6' fill='none' stroke-linecap='round'/>")
    else:
        dy = -2 if mood == "think" else 0
        eyes = (f"<circle class='eye' cx='50' cy='{50 + dy}' r='4.2' fill='{ink}'/><circle class='eye' cx='70' cy='{50 + dy}' r='4.2' fill='{ink}'/>")
        mouth = {"idle": f"<path d='M52 59Q60 66 68 59' stroke='{ink}' stroke-width='2.8' fill='none' stroke-linecap='round'/>",
                 "think": f"<path d='M54 61H66' stroke='{ink}' stroke-width='2.8' stroke-linecap='round'/>",
                 "wait": f"<circle cx='60' cy='61' r='3.2' fill='{ink}'/>"}[mood]
        arms = (f"<path d='M40 89Q29 93 27 104M80 89Q91 93 93 104' stroke='{teal}' stroke-width='6' fill='none' stroke-linecap='round'/>")
    sp = ""
    if sparkle:
        for x, y, sc, d in [(-12, 24, 1.0, 0), (134, 16, 0.85, .7), (138, 74, 0.6, 1.3), (-6, 80, 0.7, 1.9)]:
            sp += (f"<g transform='translate({x},{y}) scale({sc})'><path class='tw' style='animation-delay:{d}s' d='{STAR}' fill='#f59e0b'/></g>")
    body = (f"{arms}"
            f"<rect x='40' y='80' width='40' height='28' rx='11' fill='{teal}'/><circle cx='60' cy='94' r='5.5' fill='#fff'/><circle cx='60' cy='94' r='2.4' fill='#f59e0b'/>"
            f"<rect x='17' y='42' width='9' height='18' rx='4.5' fill='{teal}'/><rect x='94' y='42' width='9' height='18' rx='4.5' fill='{teal}'/>"
            f"<rect x='26' y='26' width='68' height='52' rx='19' fill='#fff' stroke='{teal}' stroke-width='3.5'/>"
            f"<rect x='34' y='36' width='52' height='32' rx='13' fill='#ccfbf1'/>"
            f"<circle cx='41' cy='60' r='3.4' fill='#fda4af' opacity='.7'/><circle cx='79' cy='60' r='3.4' fill='#fda4af' opacity='.7'/>")
    return (f"<svg viewBox='-26 -10 172 130' style='width:{int(size * 1.32)}px;height:auto'>{sp}{top}{body}{eyes}{mouth}</svg>")


def alpha_chart():
    def block(r):
        cells = "".join(
            f"<div class='ac'><span class='ca'>{chr((i + SHIFT) % 26 + 65)}</span><span class='pa'>{chr(i + 65)}</span></div>"
            for i in r
        )
        return f"<div class='alpha'>{cells}</div>"

    return (
        f"<div class='tx'>Caesar key <b style='color:var(--am)'>{SHIFT}</b>. "
        "Find each coded letter in the top row and read the real letter below it.</div>"
        "<div class='alegend'><span class='ca'>coded letter</span><span class='pa'>real letter</span></div>"
        "<div class='alphas'>" + block(range(0, 13)) + block(range(13, 26)) + "</div>"
    )


def hero(title, sub, eyebrow="ML Challenge", art=""):
    art_html = f"<div class='art bot'>{art}</div>" if art else ""
    st.markdown(
        f"<div class='hero'>{art_html}<div class='eyebrow'>{html.escape(eyebrow)}</div>"
        f"<h1>{html.escape(title)}</h1><p>{html.escape(sub)}</p></div>",
        unsafe_allow_html=True,
    )


def msg(text):
    st.markdown(f"<div class='msg bad'>{html.escape(text)}</div>", unsafe_allow_html=True)


def locks_row(n):
    cells = "".join(
        f"<div class='cell on'>{ENC[i]}</div>" if i < n else f"<div class='cell'>{LOCK}</div>" for i in range(N)
    )
    pct = n / N * 100
    st.markdown(
        f"<div class='locks'>{cells}</div>"
        f"<div class='pbar'><i style='width:{pct:.0f}%'></i></div>"
        f"<div class='pcap'><span>{n:02d} / {N:02d} UNLOCKED</span><span>{N - n} REMAINING</span></div>",
        unsafe_allow_html=True,
    )


@st.fragment(run_every=2)
def board():
    rows = ""
    for i, (name, t) in enumerate(ranking(), 1):
        if t["finish"] is not None:
            tag = "<span class='st fin'>FINISHED</span>"
        elif G["status"] == "running":
            tag = "<span class='st pl'>PLAYING</span>"
        else:
            tag = "<span class='st wt'>WAITING</span>"
        top = " class='top'" if (i == 1 and t["finish"] is not None) else ""
        rows += (
            f"<tr{top}><td class='rk'>{i:02d}</td><td><b>{html.escape(name)}</b></td><td>{t['solved']}/{N}</td>"
            f"<td>{len(t['hints'])}</td><td class='t'>{fmt(elapsed(t))}</td><td>{tag}</td></tr>"
        )
    if rows:
        st.markdown(
            "<table class='lb'><thead><tr><th>#</th><th>Team</th><th>Locks</th><th>Hints</th><th>Time</th><th>Status</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<div class='empty'>No teams have joined yet.</div>", unsafe_allow_html=True)


@st.fragment(run_every=1)
def clock(team):
    t = G["teams"].get(team)
    if t:
        pen = f"<div class='pn'>+{fmt(t['pen'])} PENALTY</div>" if t["pen"] else ""
        st.markdown(
            f"<div class='clock'><div><div class='l'>Team</div><div class='nm'>{html.escape(team)}</div></div>"
            f"<div><div class='l' style='text-align:right'>Elapsed</div><div class='tm'>{fmt(elapsed(t))}</div>{pen}</div></div>",
            unsafe_allow_html=True,
        )


# ---------------- Host ----------------
def host_view():
    hero("Host Dashboard", "Start the game and watch every team live", "Control panel", art=robot("idle", 84))
    running = G["status"] == "running"
    finished = sum(1 for t in G["teams"].values() if t["finish"] is not None)
    st.markdown(
        f"<div class='stats'><div class='stat'><div class='k'>Status</div><div class='v'>{'Running' if running else 'Waiting'}</div></div>"
        f"<div class='stat'><div class='k'>Teams</div><div class='v'>{len(G['teams'])}</div></div>"
        f"<div class='stat'><div class='k'>Finished</div><div class='v'>{finished}</div></div></div>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    if c1.button("Start game", disabled=running, use_container_width=True, type="primary"):
        with G["lock"]:
            G["status"], G["start"] = "running", time.time()
        st.rerun()
    if c2.button("New game", use_container_width=True):
        with G["lock"]:
            G["status"], G["start"] = "waiting", None
            G["teams"].clear()
        st.rerun()

    st.markdown("<div class='h'>Live leaderboard</div>", unsafe_allow_html=True)
    board()
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    with st.expander("Answer key (host only)"):
        key = "".join(f"<div>{i:02d} &nbsp; {html.escape(q['a'][0])}</div>" for i, q in enumerate(Q, 1))
        st.markdown(
            f"<div class='key'>{key}<div style='margin-top:10px;color:var(--mu)'>CIPHER {ENC_PHRASE} &nbsp;|&nbsp; SHIFT {SHIFT} &nbsp;|&nbsp; SOLUTION {PHRASE}</div></div>",
            unsafe_allow_html=True,
        )


# ---------------- Team ----------------
def team_view():
    team = st.session_state.get("team")

    if team is None or team not in G["teams"]:
        st.session_state.pop("team", None)
        hero("Lock Escape", "Solve the questions, crack the code, win on time", art=robot("idle", 118, True))
        with st.container(border=True):
            st.markdown("<div class='lk'>How it works</div>", unsafe_allow_html=True)
            st.markdown(
                f"<ol class='steps'>"
                f"<li>Answer {N} questions. Each correct answer opens a lock and reveals one letter of a coded word.</li>"
                f"<li>Decode the word with a Caesar cipher.</li>"
                f"<li>Each hint adds {HINT_PEN} seconds to your time. The fastest team wins.</li></ol>",
                unsafe_allow_html=True,
            )
        with st.form("join"):
            name = st.text_input("Team name", placeholder="e.g. The Neurons")
            joined = st.form_submit_button("Join game", type="primary", use_container_width=True)
        if joined:
            name = name.strip()
            if not name:
                msg("Enter a team name.")
            elif name in G["teams"]:
                msg("That name is taken, pick another one.")
            else:
                order = random.Random(name).sample(range(N), N)  # each team gets its own shuffled order
                with G["lock"]:
                    G["teams"][name] = {"order": order, "solved": 0, "pen": 0, "hints": set(), "finish": None}
                st.session_state.team = name
                st.rerun()
        return

    t = G["teams"][team]

    if G["status"] != "running":
        hero(f"Welcome, {team}", "You are in. Hang tight until the host starts the game", "Lobby", art=robot("wait", 108, True))
        st.markdown("<div class='wait'><div class='ring'></div>Waiting for the host to start</div>", unsafe_allow_html=True)

        @st.fragment(run_every=2)
        def wait():
            if G["status"] == "running":
                st.rerun(scope="app")

        wait()
        return

    clock(team)
    locks_row(t["solved"])

    if t["solved"] < N:
        qi = t["order"][t["solved"]]
        q = Q[qi]
        with st.container(border=True):
            st.markdown(
                f"<div class='qhead'><div class='lk'>Lock {t['solved'] + 1:02d} / {N:02d}</div><div class='mini bot'>{robot('think', 40)}</div></div><div class='qtext'>{html.escape(q['q'])}</div>",
                unsafe_allow_html=True,
            )
            if qi in t["hints"]:
                st.markdown(f"<div class='hint'><b>Hint</b> &nbsp; {html.escape(q['h'])} ({q['n']} letters)</div>", unsafe_allow_html=True)
            with st.form(key=f"f{t['solved']}", clear_on_submit=True):
                ans = st.text_input("Your answer", placeholder="Type your answer", label_visibility="collapsed")
                go = st.form_submit_button("Unlock", type="primary", use_container_width=True)
            if go and ans.strip():
                if norm(ans) in NA[qi]:
                    with G["lock"]:
                        t["solved"] += 1
                    st.rerun()
                else:
                    msg("Incorrect. Try again.")
            if qi not in t["hints"]:
                if st.button(f"Reveal hint  (+{HINT_PEN}s)"):
                    with G["lock"]:
                        t["hints"].add(qi)
                        t["pen"] += HINT_PEN
                    st.rerun()
        return

    # All locks open: decode the word
    if t["finish"] is None:
        with st.container(border=True):
            st.markdown(f"<div class='qhead'><div class='lk'>Final step / Decode</div><div class='mini bot'>{KEY}</div></div>", unsafe_allow_html=True)
            st.markdown("<div class='qtext'>All locks open. Decode the word.</div>", unsafe_allow_html=True)
            st.markdown("<div class='cipher'>" + "".join("<i></i>" if c == " " else f"<span>{c}</span>" for c in ENC_PHRASE) + "</div>", unsafe_allow_html=True)
            if "chart" in t["hints"]:
                st.markdown(alpha_chart(), unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div class='tx'>Caesar key <b style='color:var(--am)'>{SHIFT}</b>. Decode the word.</div>",
                    unsafe_allow_html=True,
                )
                if st.button(f"Show alphabet chart  (+{HINT_PEN}s)"):
                    with G["lock"]:
                        t["hints"].add("chart")
                        t["pen"] += HINT_PEN
                    st.rerun()
            with st.form("dec"):
                d = st.text_input("Decoded word", placeholder="Type the decoded word", label_visibility="collapsed")
                go = st.form_submit_button("Check answer", type="primary", use_container_width=True)
            if go:
                if re.sub(r"\s", "", d).upper() == WORD:
                    with G["lock"]:
                        t["finish"] = time.time() - G["start"] + t["pen"]
                    st.rerun()
                else:
                    msg("Incorrect. Check the shift.")
    else:
        with st.container(border=True):
            st.markdown(
                f"<div class='result'><div class='row2 bot'>{robot('party', 108, True)}{TROPHY}</div><div class='lbl'>Code cracked / Final time</div><div class='big'>{fmt(t['finish'])}</div></div>",
                unsafe_allow_html=True,
            )
        st.markdown("<div class='h'>Leaderboard</div>", unsafe_allow_html=True)
        board()


# Players open the normal link and see only the game.
# You open the same link with ?host=1 at the end: you get both tabs (Play + Host) on one page.
if st.query_params.get("host") == "1":
    tab_play, tab_host = st.tabs(["Play", "Host"])
    with tab_play:
        team_view()
    with tab_host:
        host_view()
else:
    team_view()
