import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from itertools import product
import io

# --- 0. Page Configuration ---
st.set_page_config(
    page_title="Nongshim & Samyang SKU Monitoring",
    page_icon="📊",
    layout="wide"
)

# --- 1. Data Loading & Processing ---
# FIX: ใช้ bytes เป็น cache key แทน file object โดยตรง
#      เพราะ Streamlit Cloud hash UploadedFile ไม่ได้ระหว่าง session rerun
@st.cache_data(show_spinner="🔄 Processing data...")
def process_data(file_bytes: bytes, file_name: str) -> pd.DataFrame | None:
    try:
        if file_name.endswith(".parquet"):
            df = pd.read_parquet(io.BytesIO(file_bytes))
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))

        # Validate required columns
        required_cols = {"sku_id", "store_id", "sales", "week_id"}
        missing = required_cols - set(df.columns)
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing)}")
            return None

        df["sku_id"]   = df["sku_id"].astype(str).str.strip()
        df["store_id"] = df["store_id"].astype(str).str.strip()
        df["sales"]    = pd.to_numeric(df["sales"], errors="coerce").fillna(0)
        df["week_id"]  = df["week_id"].astype(str).str.strip()

        # Optional: store_name column
        if "store_name" not in df.columns:
            df["store_name"] = df["store_id"]

        # Optional: upc_dsc column
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

# FIX: อ่าน bytes ครั้งเดียวแล้วส่งเข้า cache แทน file object
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
# FIX: ตั้ง row_heights แบบ explicit แทน height * n เพื่อหลีกเลี่ยง layout พัง
n_stores = len(selected_stores)
row_h    = max(200, n_stores * 22)   # ปรับความสูงต่อ row ตามจำนวน Store

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

# FIX: กรอง df ทั้งก้อนก่อน loop เพื่อลด overhead
df_filtered = df_raw[
    df_raw["week_id"].isin(selected_weeks) &
    df_raw["store_id"].isin(selected_stores)
].copy()

sorted_weeks = sorted(selected_weeks)

for i, sku in enumerate(target_skus):
    sku_df = df_filtered[df_filtered["sku_id"] == sku][["week_id", "store_id", "sales"]]

    # Cartesian grid: ทุก (week, store) ต้องมีแถว
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

    # Hover text: แสดง actual sales value
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

# FIX: ใช้ use_container_width=True เสมอ เพื่อ responsive บน Cloud
st.plotly_chart(fig, use_container_width=True)

# --- 8. Summary Metrics (Bonus) ---
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