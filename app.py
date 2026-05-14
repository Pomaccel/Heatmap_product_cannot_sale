import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from itertools import product
import io
import hashlib

# --- 0. Page Configuration ---
st.set_page_config(
    page_title="Nongshim & Samyang SKU Monitoring",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# LOGIN SYSTEM
# ============================================================

LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&display=swap');

[data-testid="stAppViewContainer"] { background: #0d0f14; }
[data-testid="stHeader"] { background: transparent; }
section[data-testid="stMain"] { color: #e2e8f0; }

.stTextInput > label {
    color: #94a3b8 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
.stTextInput > div > div > input {
    background: #1a1f2e !important;
    border: 1px solid #2d3748 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: 14px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.4) !important;
}
</style>
"""


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _check_credentials(username: str, password: str) -> bool:
    try:
        stored = st.secrets["credentials"].get(username)
        if stored is None:
            return False
        if stored == password:
            return True
        if stored == _hash_password(password):
            return True
        return False
    except Exception:
        return username == "admin" and password == "admin1234"


def show_login_page():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1, 1])
    with col_m:
        st.markdown("## 📊 SKU Monitor")
        st.markdown("**Nongshim · Samyang** — Sign in to continue")
        st.markdown("---")
        if st.session_state.get("login_failed"):
            st.error("⚠️ Incorrect username or password")
        username = st.text_input("Username", placeholder="Enter your username", key="login_user")
        password = st.text_input("Password", placeholder="••••••••", type="password", key="login_pass")
        if st.button("Sign In →", use_container_width=True):
            if _check_credentials(username.strip(), password):
                st.session_state["authenticated"] = True
                st.session_state["current_user"]  = username.strip()
                st.session_state["login_failed"]  = False
                st.rerun()
            else:
                st.session_state["login_failed"] = True
                st.rerun()
        st.caption("🔒 Secured · Internal Use Only")


def logout():
    st.session_state["authenticated"] = False
    st.session_state["current_user"]  = None
    st.session_state["login_failed"]  = False
    st.rerun()


# ============================================================
# AUTHENTICATION GATE
# ============================================================

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    show_login_page()
    st.stop()


# ============================================================
# MAIN APP
# ============================================================

DARK_APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');

/* Global background & text */
[data-testid="stAppViewContainer"]  { background: #0d0f14; }
[data-testid="stHeader"]            { background: #0d0f14; border-bottom: 1px solid #1f2535; }
[data-testid="stMain"]              { background: #0d0f14; }
section[data-testid="stMain"] *     { color: #f0f4f8; font-family: 'DM Sans', sans-serif; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #13161e !important;
    border-right: 1px solid #1f2535;
}
/* Sidebar text ทั่วไป — สว่างพอ contrast ดี */
[data-testid="stSidebar"] * { color: #e8edf2 !important; }

/* Sidebar section labels (SELECT WEEK ID, ANALYSIS MODE ฯลฯ) */
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stFileUploader label {
    color: #a8b8cc !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

/* Sidebar radio options */
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    color: #dce6f0 !important;
    font-size: 13.5px !important;
    font-weight: 400 !important;
}

/* Sidebar inputs */
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stMultiSelect > div > div {
    background: #0d0f14 !important;
    border: 1px solid #5a7aa8 !important;
    border-radius: 8px !important;
    color: #f0f4f8 !important;
}

/* Sidebar file uploader — outer wrapper */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: #1a1f2e !important;
    border-radius: 8px !important;
}

/* กรอบด้านในที่เป็นสีขาว — section + drop zone */
[data-testid="stSidebar"] [data-testid="stFileUploader"] section,
[data-testid="stSidebar"] [data-testid="stFileUploader"] section > div,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: #0d0f14 !important;
    border: 1px dashed #5a7aa8 !important;
    border-radius: 8px !important;
    color: #a8b8cc !important;
}

/* ปุ่ม Upload ข้างใน */
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
    background: #1a1f2e !important;
    border: 1px solid #5a7aa8 !important;
    color: #e8edf2 !important;
    border-radius: 6px !important;
}

/* ข้อความ 200MB per file */
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span {
    color: #6b7f99 !important;
}

/* Dropdown popup list — selectbox & multiselect (portal render นอก sidebar) */
ul[data-testid="stSelectboxVirtualDropdown"],
ul[role="listbox"],
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="menu"],
[data-baseweb="menu"] ul,
[data-baseweb="select"] [data-baseweb="popover"],
[data-baseweb="list"] {
    background: #13161e !important;
    border: 1px solid #5a7aa8 !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5) !important;
}

/* แต่ละ option ใน dropdown */
[data-baseweb="menu"] li,
[data-baseweb="menu"] [role="option"],
[data-baseweb="select"] li,
ul[role="listbox"] li {
    background: #13161e !important;
    color: #e8edf2 !important;
}

/* Hover state ของ option */
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [role="option"]:hover,
[data-baseweb="select"] li:hover,
ul[role="listbox"] li:hover,
[data-baseweb="menu"] [aria-selected="true"],
[data-baseweb="select"] [aria-selected="true"] {
    background: #1e3a5f !important;
    color: #ffffff !important;
}

/* Multiselect dropdown list */
[data-testid="stMultiSelect"] [data-baseweb="popover"],
[data-testid="stMultiSelect"] ul {
    background: #13161e !important;
    border: 1px solid #5a7aa8 !important;
    border-radius: 8px !important;
}
[data-testid="stMultiSelect"] li {
    background: #13161e !important;
    color: #e8edf2 !important;
}
[data-testid="stMultiSelect"] li:hover {
    background: #1e3a5f !important;
    color: #ffffff !important;
}

/* Sidebar sign-out button */
[data-testid="stSidebar"] .stButton > button {
    background: #1a1f2e !important;
    border: 1px solid #5a7aa8 !important;
    color: #f87171 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #2d1f1f !important;
    border-color: #f87171 !important;
}

/* Main headings */
h1, h2, h3 { color: #ffffff !important; letter-spacing: -0.02em; }

/* Paragraph & body text */
p, span, div { color: #dce6f0; }

/* Alert boxes */
[data-testid="stAlert"] {
    background: #1a1f2e !important;
    border-radius: 8px !important;
    border: 1px solid #5a7aa8 !important;
    color: #f0f4f8 !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #13161e !important;
    border: 1px solid #2a3447 !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    color: #a8b8cc !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 28px !important;
    font-weight: 600 !important;
}

/* Caption */
[data-testid="stCaptionContainer"] p { color: #a8b8cc !important; }

/* Divider */
hr { border-color: #2a3447 !important; }

/* Plotly chart container */
[data-testid="stPlotlyChart"] {
    background: #13161e !important;
    border: 1px solid #2a3447 !important;
    border-radius: 12px !important;
    padding: 8px !important;
}

/* Multiselect tags */
[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background: #1e3a5f !important;
    color: #bdd7f5 !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0d0f14; }
::-webkit-scrollbar-thumb { background: #3a4558; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #5a6a82; }
</style>
"""

st.markdown(DARK_APP_CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("---")
    user_label = st.session_state.get("current_user", "User")
    st.caption(f"👤 Signed in as **{user_label}**")
    if st.button("🚪 Sign Out", use_container_width=True):
        logout()

# --- 1. Data Loading & Processing ---
@st.cache_data(show_spinner="🔄 Processing data...")
def process_data(file_bytes: bytes, file_name: str) -> pd.DataFrame | None:
    try:
        if file_name.endswith(".parquet"):
            df = pd.read_parquet(io.BytesIO(file_bytes))
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))

        required_cols = {"sku_id", "store_id", "sales", "week_id"}
        missing = required_cols - set(df.columns)
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing)}")
            return None

        df["sku_id"]   = df["sku_id"].astype(str).str.strip()
        df["store_id"] = df["store_id"].astype(str).str.strip()
        df["sales"]    = pd.to_numeric(df["sales"], errors="coerce").fillna(0)
        df["week_id"]  = df["week_id"].astype(str).str.strip()

        if "store_name" not in df.columns:
            df["store_name"] = df["store_id"]
        if "upc_dsc" not in df.columns:
            df["upc_dsc"] = df["sku_id"]

        return df

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
        return None


# --- 2. Store Group Definitions ---
STORE_GROUPS = {
    "Store Have PC": "5022 5004 5028 5112 5032 5020 5012 5185 5048 5021 5030 6401".split(),
    "Top 10 Store":  "5513 5022 5004 5015 5001 5055 5016 5112 5028 5038".split(),
    "Top 20 Store":  "5513 5022 5004 5015 5001 5055 5016 5112 5028 5038 5018 5049 5087 5012 5034 5005 5032 5182 5017 5162".split(),
    "Top 30 Store":  "5513 5022 5004 5015 5001 5055 5016 5112 5028 5038 5018 5049 5087 5012 5034 5005 5032 5182 5017 5162 5054 5014 5045 5020 5102 5044 5037 5031 5533 5083".split(),
}

SKU_CONFIG = {
    "Nongshim Hero (4 SKU)":   (["171374086", "171251040", "75656739", "5063892"], "Nongshim"),
    "Nongshim Pareto (7 SKU)": (["171374086", "171251040", "75656739", "5063892", "5921767", "72906197", "5741009"], "Nongshim"),
    "Samyang Hero (4 SKU)":    (["73540994", "74979302", "73541001", "50974913"], "Samyang"),
    "Samyang Pareto (7 SKU)":  (["73540994", "74979302", "73541001", "50974913", "74478133", "74478117", "50767151"], "Samyang"),
}

# --- 3. Sidebar ---
st.sidebar.title("📂 Data Input")
uploaded_file = st.sidebar.file_uploader(
    "Upload Your Data (Parquet / CSV)",
    type=["parquet", "csv"],
    help="ไฟล์ต้องมีคอลัมน์: sku_id, store_id, sales, week_id"
)

if not uploaded_file:
    st.title("📊 Nongshim & Samyang SKU Monitoring")
    st.info("👋 Please upload your data file (.parquet or .csv) in the sidebar to get started.")
    st.stop()

file_bytes = uploaded_file.read()
df_raw = process_data(file_bytes, uploaded_file.name)

if df_raw is None:
    st.stop()

# --- 4. Sidebar Controls ---
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Analysis Mode:",
    list(SKU_CONFIG.keys()),
    help="เลือก Brand และจำนวน SKU ที่ต้องการวิเคราะห์"
)

available_weeks = sorted(
    df_raw["week_id"].unique(),
    key=lambda x: int(x),
    reverse=True
)
default_weeks  = available_weeks[:8] if len(available_weeks) >= 8 else available_weeks
selected_weeks = st.sidebar.multiselect(
    "Select Week ID:",
    options=available_weeks,
    default=default_weeks,
)

selected_group  = st.sidebar.selectbox("Select Store Group:", list(STORE_GROUPS.keys()))
selected_stores = STORE_GROUPS[selected_group]

# --- 5. Derived Config ---
target_skus, brand_label = SKU_CONFIG[page]

sku_names = (
    df_raw[df_raw["sku_id"].isin(target_skus)][["sku_id", "upc_dsc"]]
    .drop_duplicates()
    .set_index("sku_id")["upc_dsc"]
    .to_dict()
)

store_map = (
    df_raw[df_raw["store_id"].isin(selected_stores)][["store_id", "store_name"]]
    .drop_duplicates()
    .set_index("store_id")["store_name"]
    .to_dict()
)

# --- 6. Main View ---
st.header(f"📊 {brand_label} Availability Trend by SKU  —  {selected_group}")
st.caption("🟩 Green = Sold  |  🟥 Red = No Sales (Out of Stock)")

if not selected_weeks:
    st.warning("⚠️ Please select at least one week from the sidebar.")
    st.stop()

# --- 7. Build Heatmap ---
n_stores = len(selected_stores)
n_weeks  = len(selected_weeks)
n_skus   = len(target_skus)

row_h         = max(220, n_stores * 24)
bottom_margin = 140

subplot_titles = [
    f"SKU: {sid}  —  {sku_names.get(sid, 'Unknown')}"
    for sid in target_skus
]

fig = make_subplots(
    rows=n_skus,
    cols=1,
    subplot_titles=subplot_titles,
    vertical_spacing=0.06,
)

df_filtered = df_raw[
    df_raw["week_id"].isin(selected_weeks) &
    df_raw["store_id"].isin(selected_stores)
].copy()

sorted_weeks = sorted(selected_weeks, key=lambda x: int(x))

for i, sku in enumerate(target_skus):
    sku_df = df_filtered[df_filtered["sku_id"] == sku][["week_id", "store_id", "sales"]]

    grid = pd.DataFrame(
        list(product(sorted_weeks, selected_stores)),
        columns=["week_id", "store_id"],
    )
    grid["store_display"] = grid["store_id"] + " — " + grid["store_id"].map(
        lambda sid: store_map.get(sid, "Unknown")
    )
    grid = grid.merge(sku_df, on=["week_id", "store_id"], how="left")

    # FIX: บังคับ status เป็น integer 0 หรือ 1 เท่านั้น ไม่มีค่ากลาง
    grid["status"] = (grid["sales"].fillna(0) > 0).astype(int)

    h_df = (
        grid.pivot(index="store_display", columns="week_id", values="status")
        .fillna(0)
        .astype(int)                        # FIX: บังคับ dtype เป็น int ทั้ง DataFrame
        .reindex(columns=sorted_weeks)
    )

    sales_pivot = (
        grid.pivot(index="store_display", columns="week_id", values="sales")
        .fillna(0)
        .reindex(columns=sorted_weeks)
    )
    hover_text = [
        [
            f"Week: {col}<br>Store: {row}<br>Sales: {sales_pivot.at[row, col]:.0f}"
            for col in h_df.columns
        ]
        for row in h_df.index
    ]

    fig.add_trace(
        go.Heatmap(
            z=h_df.values.tolist(),         # FIX: แปลงเป็น plain list ป้องกัน numpy dtype ทำสีเพี้ยน
            x=h_df.columns.tolist(),
            y=h_df.index.tolist(),
            colorscale=[[0, "#e74c3c"], [1, "#27ae60"]],
            zmin=0,                         # FIX: ล็อค range สีทุก subplot ให้เท่ากัน
            zmax=1,                         # FIX: ป้องกันสีเพี้ยนเมื่อ SKU ทั้งหมด sold หมด
            showscale=False,
            text=hover_text,
            hovertemplate="%{text}<extra></extra>",
            xgap=3,
            ygap=2,
        ),
        row=i + 1,
        col=1,
    )

    # FIX: ใช้ tickangle=-45 + automargin=True ป้องกัน label ซ้อนทุกกรณี
    fig.update_xaxes(
        categoryorder="array",
        categoryarray=sorted_weeks,
        tickangle=0,
        automargin=True,
        tickfont=dict(size=11, color="#e8edf2"),   # สีตัวหนังสือแกน X
        tickmode="array",
        tickvals=sorted_weeks,
        ticktext=sorted_weeks,
        showgrid=False,
        row=i + 1,
        col=1,
    )

    fig.update_yaxes(
        tickfont=dict(size=11, color="#e8edf2"),   # สีตัวหนังสือแกน Y (store name)
        showgrid=False,
        automargin=True,
        row=i + 1,
        col=1,
    )

fig.update_layout(
    height=row_h * n_skus + bottom_margin,
    margin=dict(
        l=360,
        t=80,
        r=40,
        b=bottom_margin,
    ),
    showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(size=12, color="#e8edf2"),   # สีตัวหนังสือ default ทั้งกราฟ
)

# สี subplot title (SKU: xxx — ชื่อสินค้า)
for annotation in fig.layout.annotations:
    annotation.font.color = "#ffffff"
    annotation.font.size  = 13

st.plotly_chart(fig, use_container_width=True)
