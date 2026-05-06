import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from itertools import product

# --- 0. Page Configuration ---
st.set_page_config(page_title="Nongshim & Samyang SKU Monitoring", layout="wide")

# --- 1. Data Loading & Processing ---
@st.cache_data
def process_data(uploaded_file):
    try:
        if uploaded_file.name.endswith('.parquet'):
            df = pd.read_parquet(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
        
        df['sku_id'] = df['sku_id'].astype(str).str.strip()
        df['store_id'] = df['store_id'].astype(str).str.strip()
        df['sales'] = pd.to_numeric(df['sales'], errors='coerce').fillna(0)
        df['week_id'] = df['week_id'].astype(str)
        return df
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

# --- 2. Store Group Definitions ---
STORE_GROUPS = {
    "Store Have PC": "5022 5004 5028 5112 5032 5020 5012 5185 5048 5021 5030 6401".split(),
    "Top 10 Store": "5513 5022 5004 5015 5001 5055 5016 5112 5028 5038".split(),
    "Top 20 Store": "5513 5022 5004 5015 5001 5055 5016 5112 5028 5038 5018 5049 5087 5012 5034 5005 5032 5182 5017 5162".split(),
    "Top 30 Store": "5513 5022 5004 5015 5001 5055 5016 5112 5028 5038 5018 5049 5087 5012 5034 5005 5032 5182 5017 5162 5054 5014 5045 5020 5102 5044 5037 5031 5533 5083".split()
}

# --- 3. Main Dashboard ---
st.sidebar.title("📂 Data Input")
uploaded_file = st.sidebar.file_uploader("Upload Your Data (Parquet/CSV)", type=["parquet", "csv"])

if uploaded_file:
    df_raw = process_data(uploaded_file)
    
    if df_raw is not None:
        st.sidebar.markdown("---")
        page = st.sidebar.radio(
            "Analysis Mode:", 
            ["Nongshim Hero (4 SKU)", "Nongshim Pareto (7 SKU)", "Samyang Hero (4 SKU)", "Samyang Pareto (7 SKU)"]
        )

        # Filters
        available_weeks = sorted(df_raw['week_id'].unique(), reverse=True)
        selected_weeks = st.sidebar.multiselect(
            "Select Week ID:", 
            options=available_weeks,
            default=available_weeks[:8] if len(available_weeks) >= 8 else available_weeks
        )
        
        selected_group_name = st.sidebar.selectbox("Select Store Group:", list(STORE_GROUPS.keys()))
        selected_stores = STORE_GROUPS[selected_group_name]

        # SKU Targets
        sku_config = {
            "Nongshim Hero (4 SKU)": (['171374086', '171251040', '75656739', '5063892'], "Nongshim"),
            "Nongshim Pareto (7 SKU)": (['171374086', '171251040', '75656739', '5063892', '5921767', '72906197', '5741009'], "Nongshim"),
            "Samyang Hero (4 SKU)": (['73540994', '74979302', '73541001', '50974913'], "Samyang"),
            "Samyang Pareto (7 SKU)": (['73540994', '74979302', '73541001', '50974913', '74478133', '74478117', '50767151'], "Samyang")
        }
        target_skus, brand_label = sku_config[page]
        
        # Get SKU Mapping for Titles
        sku_names = df_raw[df_raw['sku_id'].isin(target_skus)][['sku_id', 'upc_dsc']].drop_duplicates().set_index('sku_id')['upc_dsc'].to_dict()

        st.header(f"📊 {brand_label} Availability Trend by SKU")
        st.info("🟩 Green = Sold | 🟥 Red = No Sales (Out of Stock)")

        if not selected_weeks:
            st.warning("Please select at least one week.")
        else:
            # สร้าง Subplots ตามจำนวน SKU (1 Column หลาย Rows)
            fig = make_subplots(
                rows=len(target_skus), cols=1,
                subplot_titles=[f"SKU: {sid} - {sku_names.get(sid, 'Unknown')}" for sid in target_skus],
                vertical_spacing=0.05
            )

            for i, sku in enumerate(target_skus):
                # กรองข้อมูลเฉพาะ SKU นั้นๆ
                sku_df = df_raw[(df_raw['sku_id'] == sku) & (df_raw['week_id'].isin(selected_weeks)) & (df_raw['store_id'].isin(selected_stores))]
                
                # สร้าง Cartesian product เพื่อให้ครบทุก Week/Store
                grid = pd.DataFrame(list(product(selected_weeks, selected_stores)), columns=['week_id', 'store_id'])
                
                # ดึงชื่อร้านค้า
                store_map = df_raw[df_raw['store_id'].isin(selected_stores)][['store_id', 'store_name']].drop_duplicates()
                grid = grid.merge(store_map, on='store_id', how='left')
                grid['store_display'] = grid['store_id'] + " - " + grid['store_name'].fillna("Unknown")
                
                # รวมข้อมูลขาย
                grid = grid.merge(sku_df[['week_id', 'store_id', 'sales']], on=['week_id', 'store_id'], how='left')
                grid['status'] = grid['sales'].apply(lambda x: 1 if x > 0 else 0)

                # Pivot สำหรับ Heatmap
                h_df = grid.pivot(index='store_display', columns='week_id', values='status').fillna(0)
                # เรียง Week จากเก่าไปใหม่ (ซ้ายไปขวา)
                h_df = h_df.reindex(columns=sorted(selected_weeks))

                # เพิ่ม Heatmap ลงใน Subplot
                fig.add_trace(
                    go.Heatmap(
                        z=h_df.values,
                        x=h_df.columns,
                        y=h_df.index,
                        colorscale=[[0, '#e74c3c'], [1, '#27ae60']],
                        showscale=False,
                        hovertemplate="Week: %{x}<br>Store: %{y}<br>Status: %{z}<extra></extra>"
                    ),
                    row=i+1, col=1
                )

            # ปรับแต่ง Layout
            fig.update_layout(
                height=400 * len(target_skus), # ปรับความสูงตามจำนวน SKU
                margin=dict(l=350, t=100, r=50, b=50),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👋 Please upload your data file in the sidebar.")
