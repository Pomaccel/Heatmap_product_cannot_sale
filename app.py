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
n_stores    = len(selected_stores)
n_weeks     = len(selected_weeks)
n_skus      = len(target_skus)

# FIX: เพิ่มความสูงต่อ row และเพิ่ม bottom margin สำหรับ X-axis label ที่หมุน
row_h       = max(220, n_stores * 24)
# bottom margin ใหญ่ขึ้นเพื่อรองรับ label ที่ถูก rotate 45°
bottom_margin = 120 + (n_weeks * 4)

subplot_titles = [
    f"SKU: {sid}  —  {sku_names.get(sid, 'Unknown')}"
    for sid in target_skus
]

fig = make_subplots(
    rows=n_skus,
    cols=1,
    subplot_titles=subplot_titles,
    vertical_spacing=0.06,   # FIX: เพิ่มช่องว่างระหว่าง subplot
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
            xgap=3,   # FIX: เพิ่ม gap ระหว่าง cell แนวนอน
            ygap=2,   # FIX: เพิ่ม gap ระหว่าง cell แนวตั้ง
        ),
        row=i + 1,
        col=1,
    )

    # FIX: หมุน X-axis label 45° + บังคับลำดับ + ขยาย tick font
    fig.update_xaxes(
        categoryorder="array",
        categoryarray=sorted_weeks,
        tickangle=45,            # หมุน label ไม่ซ้อนกัน
        tickfont=dict(size=12),  # ขนาด font ที่อ่านง่าย
        tickmode="array",
        tickvals=sorted_weeks,
        ticktext=sorted_weeks,
        showgrid=False,
        row=i + 1,
        col=1,
    )

    # FIX: ขยาย Y-axis font ให้อ่านง่ายขึ้น
    fig.update_yaxes(
        tickfont=dict(size=11),
        showgrid=False,
        row=i + 1,
        col=1,
    )

fig.update_layout(
    height=row_h * n_skus + bottom_margin,
    margin=dict(
        l=340,               # ซ้าย: เผื่อ store name ยาว
        t=80,
        r=40,
        b=bottom_margin,     # FIX: bottom ใหญ่ขึ้นรองรับ label ที่หมุน
    ),
    showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(size=12),
)

st.plotly_chart(fig, use_container_width=True)

# --- 8. Summary Metrics ---
st.markdown("---")
col1, col2, col3 = st.columns(3)
total_cells = n_skus * len(selected_stores) * len(selected_weeks)
sold_cells  = int(
    df_filtered[df_filtered["sku_id"].isin(target_skus)]["sales"]
    .gt(0).sum()
)
avail_rate  = sold_cells / total_cells * 100 if total_cells > 0 else 0

col1.metric("Total SKU-Store-Week Cells", f"{total_cells:,}")
col2.metric("Cells with Sales",           f"{sold_cells:,}")
col3.metric("Availability Rate",          f"{avail_rate:.1f}%")