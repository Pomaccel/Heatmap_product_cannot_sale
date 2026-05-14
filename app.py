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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
[data-testid="stAppViewContainer"] {
    background: #0d0f14;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }

/* ── Login wrapper ── */
.login-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 88vh;
    font-family: 'DM Sans', sans-serif;
}

/* ── Card ── */
.login-card {
    background: #13161e;
    border: 1px solid #1f2535;
    border-radius: 16px;
    padding: 48px 44px 40px;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 32px 80px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.03);
}

/* ── Brand bar ── */
.login-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 32px;
}
.login-brand-icon {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    box-shadow: 0 4px 14px rgba(59,130,246,0.35);
}
.login-brand-name {
    font-size: 15px; font-weight: 600;
    color: #e2e8f0; letter-spacing: 0.01em;
}
.login-brand-sub {
    font-size: 11px; color: #4a5568;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.05em; text-transform: uppercase;
}

/* ── Headline ── */
.login-headline {
    font-size: 22px; font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 6px;
    letter-spacing: -0.02em;
}
.login-sub {
    font-size: 13.5px; color: #64748b;
    margin-bottom: 28px;
    line-height: 1.5;
}

/* ── Divider ── */
.login-divider {
    height: 1px; background: #1f2535;
    margin-bottom: 28px;
}

/* ── Error banner ── */
.login-error {
    background: rgba(239,68,68,0.1);
    border: 1px solid rgba(239,68,68,0.25);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px; color: #fca5a5;
    margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
}

/* ── Streamlit input overrides (inside card) ── */
.stTextInput > label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    color: #94a3b8 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
}
.stTextInput > div > div > input {
    background: #0d0f14 !important;
    border: 1px solid #1f2535 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    transition: border-color 0.15s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
}
.stTextInput > div > div > input::placeholder { color: #334155 !important; }

/* ── Login button ── */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    padding: 11px 0 !important;
    width: 100% !important;
    margin-top: 8px !important;
    cursor: pointer !important;
    transition: opacity 0.15s ease, transform 0.1s ease !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.4) !important;
}
.stButton > button:hover {
    opacity: 0.92 !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Footer note ── */
.login-footer {
    text-align: center;
    margin-top: 20px;
    font-size: 11.5px;
    color: #2d3748;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.03em;
}

/* ── Logout button (top-right inside app) ── */
.logout-btn {
    position: fixed; top: 14px; right: 16px; z-index: 9999;
}
</style>
"""


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _check_credentials(username: str, password: str) -> bool:
    """
    ตรวจสอบ credentials จาก st.secrets
    รูปแบบ secrets.toml:
        [credentials]
        admin   = "hashed_or_plain_password"
        analyst = "another_password"
    """
    try:
        stored = st.secrets["credentials"].get(username)
        if stored is None:
            return False
        # รองรับทั้ง plain text และ sha256 hash
        if stored == password:
            return True
        if stored == _hash_password(password):
            return True
        return False
    except Exception:
        # ถ้าไม่มี secrets ให้ fallback demo account
        return username == "admin" and password == "admin1234"


def show_login_page():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    # Center column
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
        st.markdown("""
        <div class="login-card">
            <div class="login-brand">
                <div class="login-brand-icon">📊</div>
                <div>
                    <div class="login-brand-name">SKU Monitor</div>
                    <div class="login-brand-sub">Nongshim · Samyang</div>
                </div>
            </div>
            <div class="login-headline">Sign in to your account</div>
            <div class="login-sub">Enter your credentials to access the dashboard.</div>
            <div class="login-divider"></div>
        </div>
        """, unsafe_allow_html=True)

        # Error message
        if st.session_state.get("login_failed"):
            st.markdown(
                '<div class="login-error">⚠️ &nbsp;Incorrect username or password. Please try again.</div>',
                unsafe_allow_html=True,
            )

        username = st.text_input("Username", placeholder="Enter your username", key="login_user")
        password = st.text_input("Password", placeholder="••••••••", type="password", key="login_pass")

        if st.button("Sign In →"):
            if _check_credentials(username.strip(), password):
                st.session_state["authenticated"] = True
                st.session_state["current_user"]  = username.strip()
                st.session_state["login_failed"]  = False
                st.rerun()
            else:
                st.session_state["login_failed"] = True
                st.rerun()

        st.markdown(
            '<div class="login-footer">🔒 &nbsp;Secured · Internal Use Only</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


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
# MAIN APP (เหมือนเดิมทุกอย่าง — เพิ่มแค่ logout button)
# ============================================================

# --- Logout button ที่ sidebar ---
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

available_weeks  = sorted(df_raw["week_id"].unique(), reverse=True)
default_weeks    = available_weeks[:8] if len(available_weeks) >= 8 else available_weeks
selected_weeks   = st.sidebar.multiselect(
    "Select Week ID:",
    options=available_weeks,
    default=default_weeks,
)

selected_group   = st.sidebar.selectbox("Select Store Group:", list(STORE_GROUPS.keys()))
selected_stores  = STORE_GROUPS[selected_group]

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
row_h    = max(200, n_stores * 22)

subplot_titles = [
    f"SKU: {sid}  —  {sku_names.get(sid, 'Unknown')}"
    for sid in target_skus
]

fig = make_subplots(
    rows=len(target_skus),
    cols=1,
    subplot_titles=subplot_titles,
    vertical_spacing=0.04,
)

df_filtered = df_raw[
    df_raw["week_id"].isin(selected_weeks) &
    df_raw["store_id"].isin(selected_stores)
].copy()

sorted_weeks = sorted(selected_weeks)

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
    grid["status"] = (grid["sales"].fillna(0) > 0).astype(int)

    h_df = (
        grid.pivot(index="store_display", columns="week_id", values="status")
        .fillna(0)
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
            z=h_df.values,
            x=h_df.columns.tolist(),
            y=h_df.index.tolist(),
            colorscale=[[0, "#e74c3c"], [1, "#27ae60"]],
            showscale=False,
            text=hover_text,
            hovertemplate="%{text}<extra></extra>",
            xgap=2,
            ygap=1,
        ),
        row=i + 1,
        col=1,
    )

fig.update_layout(
    height=row_h * len(target_skus) + 120,
    margin=dict(l=320, t=80, r=40, b=60),
    showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(size=11),
)

st.plotly_chart(fig, use_container_width=True)

# --- 8. Summary Metrics ---
st.markdown("---")
col1, col2, col3 = st.columns(3)
total_cells  = len(target_skus) * len(selected_stores) * len(selected_weeks)
sold_cells   = int(
    df_filtered[df_filtered["sku_id"].isin(target_skus)]["sales"]
    .gt(0).sum()
)
avail_rate   = sold_cells / total_cells * 100 if total_cells > 0 else 0

col1.metric("Total SKU-Store-Week Cells", f"{total_cells:,}")
col2.metric("Cells with Sales",           f"{sold_cells:,}")
col3.metric("Availability Rate",          f"{avail_rate:.1f}%")