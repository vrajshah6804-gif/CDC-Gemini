import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# PAGE CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="2025 CDC Provisional Natality Explorer",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# CONSTANTS & MAPPINGS
# ==========================================
STATE_TO_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

# ==========================================
# DATA LOADING & PREPROCESSING
# ==========================================
@st.cache_data
def load_and_preprocess_data(file_name: str = "Provisional_Natality_2025_CDC1.csv") -> pd.DataFrame:
    """Loads, validates, and prepares CDC natality dataset."""
    base_path = Path(__file__).resolve().parent
    data_path = base_path / file_name
    
    if not data_path.exists():
        data_path = Path(file_name)
        if not data_path.exists():
            st.error(f"Data file '{file_name}' not found. Please place it in the same directory as app.py.")
            st.stop()

    df = pd.read_csv(data_path)

    # Data Validation Checks
    required_cols = {"state_of_residence", "month", "month_code", "sex_of_infant", "births"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        st.error(f"Dataset is missing required columns: {missing}")
        st.stop()

    if df["births"].isnull().any() or (df["births"] < 0).any():
        st.error("Data validation failed: Invalid or missing birth counts detected.")
        st.stop()

    # Enforce chronological ordering on months
    month_order = (
        df[["month", "month_code"]]
        .drop_duplicates()
        .sort_values("month_code")["month"]
        .tolist()
    )
    df["month"] = pd.Categorical(df["month"], categories=month_order, ordered=True)
    df["state_abbr"] = df["state_of_residence"].map(STATE_TO_ABBR)

    return df

# Load Data
raw_df = load_and_preprocess_data()

# ==========================================
# HEADER SECTION
# ==========================================
st.title("📊 2025 CDC Provisional Natality Dashboard")
st.markdown("Interactive analytical dashboard for exploring U.S. birth patterns across geographies, time, and demographic dimensions.")

st.info("""
**Data Notice:** Figures represent **provisional birth counts** (not birth rates) sourced from the **CDC National Center for Health Statistics**. Data are subject to revision.
""")

# ==========================================
# SIDEBAR FILTERS & CONTROLS
# ==========================================
st.sidebar.header("Filter Controls")

all_states = sorted(raw_df["state_of_residence"].unique().tolist())
all_months = raw_df["month"].cat.categories.tolist()
all_sexes = sorted(raw_df["sex_of_infant"].unique().tolist())

if "selected_states" not in st.session_state:
    st.session_state.selected_states = all_states
if "selected_months" not in st.session_state:
    st.session_state.selected_months = all_months
if "selected_sexes" not in st.session_state:
    st.session_state.selected_sexes = all_sexes

col_btn1, col_btn2 = st.sidebar.columns(2)
if col_btn1.button("Select All"):
    st.session_state.selected_states = all_states
    st.session_state.selected_months = all_months
    st.session_state.selected_sexes = all_sexes
    st.rerun()

if col_btn2.button("Reset Filters"):
    st.session_state.selected_states = all_states
    st.session_state.selected_months = all_months
    st.session_state.selected_sexes = all_sexes
    st.rerun()

selected_states = st.sidebar.multiselect(
    "Select Geographies:",
    options=all_states,
    default=st.session_state.selected_states
)

selected_months = st.sidebar.multiselect(
    "Select Months:",
    options=all_months,
    default=st.session_state.selected_months
)

selected_sexes = st.sidebar.multiselect(
    "Select Infant Sex:",
    options=all_sexes,
    default=st.session_state.selected_sexes
)

st.session_state.selected_states = selected_states
st.session_state.selected_months = selected_months
st.session_state.selected_sexes = selected_sexes

# Active Filter Summary Panel
st.sidebar.markdown("---")
st.sidebar.markdown("### Active Filters Summary")
st.sidebar.caption(f"**States Selected:** {len(selected_states)} of {len(all_states)}")
st.sidebar.caption(f"**Months Selected:** {len(selected_months)} of {len(all_months)}")
st.sidebar.caption(f"**Sex Categories:** {', '.join(selected_sexes) if selected_sexes else 'None'}")

# Filter Execution
filtered_df = raw_df[
    (raw_df["state_of_residence"].isin(selected_states)) &
    (raw_df["month"].isin(selected_months)) &
    (raw_df["sex_of_infant"].isin(selected_sexes))
]

# ==========================================
# MAIN DASHBOARD CONTENT
# ==========================================
if filtered_df.empty:
    st.warning("⚠️ No observations match your current filter selection. Please broaden your sidebar criteria.")
else:
    # --- KPI CARDS ---
    total_births = filtered_df["births"].sum()
    selected_states_count = filtered_df["state_of_residence"].nunique()
    
    monthly_agg = filtered_df.groupby("month", observed=True)["births"].sum()
    avg_births_per_month = monthly_agg.mean() if not monthly_agg.empty else 0

    state_agg = filtered_df.groupby("state_of_residence")["births"].sum()
    top_state = state_agg.idxmax() if not state_agg.empty else "N/A"
    top_state_val = state_agg.max() if not state_agg.empty else 0

    top_month = monthly_agg.idxmax() if not monthly_agg.empty else "N/A"
    top_month_val = monthly_agg.max() if not monthly_agg.empty else 0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total Births", f"{total_births:,.0f}")
    kpi2.metric("Selected States", f"{selected_states_count} / {len(all_states)}")
    kpi3.metric("Avg Births / Month", f"{avg_births_per_month:,.0f}")
    kpi4.metric("Top Geography", f"{top_state}", help=f"{top_state_val:,.0f} births")
    kpi5.metric("Peak Month", f"{top_month}", help=f"{top_month_val:,.0f} births")

    st.markdown("---")

    # --- TABS LAYOUT ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview",
        "Geographic Analysis",
        "Monthly & Sex Analysis",
        "Data Table & Download",
        "About the Data"
    ])

    # ------------------------------------------
    # TAB 1: OVERVIEW
    # ------------------------------------------
    with tab1:
        st.subheader("Executive Overview")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Top & Bottom Geographies by Total Births")
            state_totals = filtered_df.groupby("state_of_residence")["births"].sum().reset_index()
            sorted_states = state_totals.sort_values(by="births", ascending=False)
            
            if len(sorted_states) >= 10:
                top_bottom = pd.concat([sorted_states.head(5), sorted_states.tail(5)])
            else:
                top_bottom = sorted_states

            fig_bar = px.bar(
                top_bottom,
                x="births",
                y="state_of_residence",
                orientation="h",
                color="births",
                color_continuous_scale="Viridis",
                labels={"births": "Total Births", "state_of_residence": "State"},
                title="Comparison of Highest and Lowest Birth Count Regions"
            )
            fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, range_x=[0, None])
            fig_bar.update_traces(hovertemplate="%{y}: %{x:,d} births")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.markdown("##### Monthly Trend Trajectory")
            monthly_totals = filtered_df.groupby("month", observed=True)["births"].sum().reset_index()
            
            fig_line = px.line(
                monthly_totals,
                x="month",
                y="births",
                markers=True,
                labels={"month": "Month", "births": "Total Births"},
                title="Aggregate Monthly Birth Sequence"
            )
            fig_line.update_layout(yaxis_range=[0, monthly_totals["births"].max() * 1.1 if not monthly_totals.empty else 100])
            fig_line.update_traces(hovertemplate="%{x}: %{y:,d} births")
            st.plotly_chart(fig_line, use_container_width=True)

    # ------------------------------------------
    # TAB 2: GEOGRAPHIC ANALYSIS
    # ------------------------------------------
    with tab2:
        st.subheader("Geographic Analysis")
        state_df = filtered_df.groupby(["state_of_residence", "state_abbr"])["births"].sum().reset_index()

        st.markdown("##### U.S. Geographic Birth Distribution")
        fig_map = px.choropleth(
            state_df,
            locations="state_abbr",
            locationmode="USA-states",
            color="births",
            scope="usa",
            color_continuous_scale="Viridis",
            labels={"births": "Total Births", "state_abbr": "State Code"},
            hover_name="state_of_residence"
        )
        fig_map.update_traces(hovertemplate="%{hovertext}: %{z:,d} births")
        fig_map.update_layout(margin={"r":0, "t":30, "l":0, "b":0})
        st.plotly_chart(fig_map, use_container_width=True)

        g_col1, g_col2 = st.columns(2)

        with g_col1:
            st.markdown("##### State Ranking")
            sorted_states_rank = state_df.sort_values(by="births", ascending=True)
            fig_rank = px.bar(
                sorted_states_rank,
                x="births",
                y="state_of_residence",
                orientation="h",
                color="births",
                color_continuous_scale="Cividis",
                labels={"births": "Births", "state_of_residence": "State"}
            )
            fig_rank.update_layout(range_x=[0, None], height=600)
            fig_rank.update_traces(hovertemplate="%{y}: %{x:,d} births")
            st.plotly_chart(fig_rank, use_container_width=True)

        with g_col2:
            st.markdown("##### State-by-Month Matrix Heatmap")
            heatmap_data = filtered_df.pivot_table(
                index="state_of_residence", 
                columns="month", 
                values="births", 
                aggfunc="sum",
                observed=True
            ).fillna(0)

            fig_heat = px.imshow(
                heatmap_data,
                labels=dict(x="Month", y="State", color="Births"),
                color_continuous_scale="Blues",
                aspect="auto"
            )
            fig_heat.update_layout(height=600)
            fig_heat.update_traces(hovertemplate="State: %{y}<br>Month: %{x}<br>Births: %{z:,d}")
            st.plotly_chart(fig_heat, use_container_width=True)

    # ------------------------------------------
    # TAB 3: MONTHLY & SEX ANALYSIS
    # ------------------------------------------
    with tab3:
        st.subheader("Monthly and Sex Differences")
        s_col1, s_col2 = st.columns(2)

        sex_monthly = filtered_df.groupby(["month", "sex_of_infant"], observed=True)["births"].sum().reset_index()

        with s_col1:
            st.markdown("##### Temporal Trend by Infant Sex")
            fig_sex_line = px.line(
                sex_monthly,
                x="month",
                y="births",
                color="sex_of_infant",
                markers=True,
                labels={"month": "Month", "births": "Births", "sex_of_infant": "Infant Sex"},
                color_discrete_map={"Female": "#2B5C8F", "Male": "#D95F02"}
            )
            fig_sex_line.update_layout(yaxis_range=[0, sex_monthly["births"].max() * 1.1 if not sex_monthly.empty else 100])
            fig_sex_line.update_traces(hovertemplate="%{x} (%{fullData.name}): %{y:,d} births")
            st.plotly_chart(fig_sex_line, use_container_width=True)

        with s_col2:
            st.markdown("##### Sex Ratio Comparison Across Months")
            fig_sex_bar = px.bar(
                sex_monthly,
                x="month",
                y="births",
                color="sex_of_infant",
                barmode="group",
                labels={"month": "Month", "births": "Births", "sex_of_infant": "Infant Sex"},
                color_discrete_map={"Female": "#2B5C8F", "Male": "#D95F02"}
            )
            fig_sex_bar.update_layout(yaxis_range=[0, None])
            fig_sex_bar.update_traces(hovertemplate="%{x} (%{fullData.name}): %{y:,d} births")
            st.plotly_chart(fig_sex_bar, use_container_width=True)

    # ------------------------------------------
    # TAB 4: DATA TABLE & DOWNLOAD
    # ------------------------------------------
    with tab4:
        st.subheader("Filtered Dataset Explorer")
        search_term = st.text_input("🔍 Search within active state records:", "")
        
        display_df = filtered_df.drop(columns=["state_abbr"], errors="ignore")
        
        if search_term:
            display_df = display_df[
                display_df["state_of_residence"].str.contains(search_term, case=False, na=False)
            ]

        st.write(f"Showing **{len(display_df):,d}** records")

        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "births": st.column_config.NumberColumn("Birth Count", format="%d"),
                "state_of_residence": "State",
                "month": "Month",
                "month_code": "Month Code",
                "year_code": "Year",
                "sex_of_infant": "Infant Sex"
            }
        )

        csv_data = display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv_data,
            file_name="filtered_cdc_natality_2025.csv",
            mime="text/csv"
        )

    # ------------------------------------------
    # TAB 5: ABOUT THE DATA
    # ------------------------------------------
    with tab5:
        st.subheader("About the CDC Natality Dataset")
        st.markdown("""
        #### **Data Overview & Source**
        * **Source:** Centers for Disease Control and Prevention (CDC) National Center for Health Statistics (NCHS).
        * **Period Covered:** Provisional 2025 Natality Statistics.
        
        ---

        #### **Methodological Guidelines for Business Analytics Students**
        1. **Absolute Counts vs. Rates:** 
           * All metrics presented in this application represent **absolute count of live births**, not crude or standardized birth rates.
           * Comparing populous states (e.g., California or Texas) directly with smaller states (e.g., Wyoming) highlights scale rather than fertility propensity.
        
        2. **Provisional Status:**
           * These counts are derived from preliminary birth certificates received and processed by NCHS. They are subject to revisions before final statistics are finalized.
        
        3. **Analytical Recommendations:**
           * Use sex-stratified visuals to examine biological constancy in human sex ratios at birth (~105 male births per 100 female births).
           * Evaluate seasonality patterns across months to identify peak healthcare operational demand windows.
        """)
