"""
app.py - UPI Digital Payments Growth and Opportunity Dashboard
Interactive Streamlit analytics dashboard powered by PhonePe Pulse data.
Reads from portable SQLite database (phonepe_pulse.db) for zero-config local/cloud deployment.
All metrics reflect data recorded strictly on the PhonePe platform.
"""

import os
import json
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PhonePe Platform Analytics | UPI Payments Growth",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #5f259f;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #555;
        margin-bottom: 1.3rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 4px solid #5f259f;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .metric-val {
        font-size: 1.55rem;
        font-weight: 700;
        color: #222;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. DATABASE & GEOJSON CACHE
# -----------------------------------------------------------------------------
DB_PATH = "phonepe_pulse.db"
GEOJSON_PATH = "india_states.geojson"


@st.cache_resource
def get_db_connection():
    """Returns a thread-safe connection to the portable SQLite database."""
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at '{DB_PATH}'. Please run `python load.py` first.")
        st.stop()
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def load_geojson():
    """Loads and caches the simplified India states GeoJSON (152 KB, 36/36 states)."""
    if os.path.exists(GEOJSON_PATH):
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


conn = get_db_connection()
india_geojson = load_geojson()


# -----------------------------------------------------------------------------
# 3. CACHED QUERY HELPERS
# -----------------------------------------------------------------------------
@st.cache_data
def get_filter_options():
    years = sorted([r[0] for r in conn.execute("SELECT DISTINCT year FROM agg_transaction").fetchall()])
    categories = [r[0] for r in conn.execute("SELECT DISTINCT category FROM agg_transaction").fetchall()]
    states = ["All India"] + sorted([r[0] for r in conn.execute("SELECT DISTINCT state FROM agg_transaction").fetchall()])
    return years, categories, states


@st.cache_data
def get_kpi_metrics(period, categories_tuple, state_focus):
    cat_str = ",".join([f"'{c}'" for c in categories_tuple])
    state_clause = f"AND state = '{state_focus}'" if state_focus != "All India" else ""
    
    # Financial metrics for period
    q_tx = f"""
        SELECT SUM(amount) AS total_amount, SUM(count) AS total_count
        FROM agg_transaction
        WHERE period = '{period}'
          AND category IN ({cat_str})
          {state_clause};
    """
    tx_res = conn.execute(q_tx).fetchone()
    amount = tx_res[0] or 0
    count = tx_res[1] or 0
    
    # Registered users for this exact quarter (running cumulative total)
    user_state = f"AND state = '{state_focus}'" if state_focus != "All India" else ""
    q_u = f"SELECT SUM(registered_users), SUM(app_opens) FROM agg_user WHERE period = '{period}' {user_state};"
    u_res = conn.execute(q_u).fetchone()
    reg_users = u_res[0] or 0
    app_opens = u_res[1] or 0
    
    return amount, count, reg_users, app_opens


@st.cache_data
def get_state_map_data(period, categories_tuple):
    cat_str = ",".join([f"'{c}'" for c in categories_tuple])
    return pd.read_sql_query(f"""
        SELECT 
            state,
            ROUND(SUM(amount) / 1e9, 2) AS amount_billion_inr,
            SUM(count) AS total_transactions,
            ROUND(SUM(amount) / SUM(count), 2) AS avg_ticket_size_inr
        FROM agg_transaction
        WHERE period = '{period}'
          AND category IN ({cat_str})
        GROUP BY state;
    """, conn)


@st.cache_data
def get_district_rankings(period, state_focus):
    state_filter = f"AND state = '{state_focus}'" if state_focus != "All India" else ""
    return pd.read_sql_query(f"""
        SELECT 
            state || ' - ' || district AS district_label,
            ROUND(amount / 1e9, 2) AS amount_billion_inr,
            count AS transactions
        FROM map_transaction
        WHERE period = '{period}'
          {state_filter}
        ORDER BY amount DESC
        LIMIT 10;
    """, conn)


@st.cache_data
def get_quarterly_trend(state_focus):
    state_clause = f"AND state = '{state_focus}'" if state_focus != "All India" else ""
    return pd.read_sql_query(f"""
        SELECT 
            period,
            year,
            quarter,
            ROUND(SUM(amount) / 1e9, 2) AS amount_billion_inr,
            ROUND(SUM(count) / 1e6, 2) AS count_million,
            ROUND(SUM(amount) / SUM(count), 2) AS avg_ticket_size_inr
        FROM agg_transaction
        WHERE 1=1 {state_clause}
        GROUP BY period, year, quarter
        ORDER BY year, quarter;
    """, conn)


@st.cache_data
def get_payments_mix():
    return pd.read_sql_query("""
        SELECT 
            year,
            SUM(CASE WHEN category = 'Peer-to-peer payments' THEN count ELSE 0 END) AS p2p_count,
            SUM(CASE WHEN category = 'Merchant payments' THEN count ELSE 0 END) AS merchant_count,
            ROUND(SUM(CASE WHEN category = 'Merchant payments' THEN count ELSE 0 END) * 100.0 / 
                  SUM(CASE WHEN category IN ('Peer-to-peer payments', 'Merchant payments') THEN count ELSE 0 END), 2) AS merchant_vol_share_pct,
            ROUND(SUM(CASE WHEN category = 'Merchant payments' THEN amount ELSE 0 END) * 100.0 / 
                  SUM(CASE WHEN category IN ('Peer-to-peer payments', 'Merchant payments') THEN amount ELSE 0 END), 2) AS merchant_val_share_pct
        FROM agg_transaction
        GROUP BY year
        ORDER BY year;
    """, conn)


@st.cache_data
def get_scatter_data(period):
    return pd.read_sql_query(f"""
        SELECT 
            u.state,
            u.district,
            u.registered_users,
            u.app_opens,
            ROUND(CAST(u.app_opens AS FLOAT) / u.registered_users, 1) AS app_opens_per_user,
            ROUND(t.amount / 1e9, 2) AS amount_billion_inr,
            t.count AS transaction_count,
            ROUND(CAST(t.count AS FLOAT) / u.registered_users, 2) AS tx_per_user
        FROM map_user u
        JOIN map_transaction t 
          ON u.state = t.state AND u.district = t.district AND u.period = t.period
        WHERE u.period = '{period}'
          AND u.registered_users > 20000;
    """, conn)


@st.cache_data
def get_untapped_districts(period):
    return pd.read_sql_query(f"""
        SELECT 
            u.state,
            u.district,
            u.registered_users,
            t.count AS total_transactions,
            ROUND(CAST(t.count AS FLOAT) / u.registered_users, 2) AS tx_per_user,
            ROUND(t.amount / 1e7, 2) AS amount_crore_inr
        FROM map_user u
        JOIN map_transaction t 
          ON u.state = t.state AND u.district = t.district AND u.period = t.period
        WHERE u.period = '{period}' 
          AND u.registered_users >= 500000
        ORDER BY tx_per_user ASC
        LIMIT 10;
    """, conn)


@st.cache_data
def get_insurance_data():
    return pd.read_sql_query("""
        SELECT 
            period,
            year,
            quarter,
            SUM(count) AS policies_issued,
            ROUND(SUM(amount) / 1e7, 2) AS premium_crore_inr
        FROM agg_insurance
        GROUP BY period, year, quarter
        ORDER BY year, quarter;
    """, conn)


@st.cache_data
def get_device_data(period):
    # Check if period has device data
    check = conn.execute(f"SELECT COUNT(*) FROM agg_user_device WHERE period = '{period}'").fetchone()[0]
    if check == 0:
        return None
    return pd.read_sql_query(f"""
        SELECT 
            brand,
            SUM(count) AS device_count,
            ROUND(SUM(count) * 100.0 / (SELECT SUM(count) FROM agg_user_device WHERE period = '{period}'), 2) AS share_pct
        FROM agg_user_device
        WHERE period = '{period}'
        GROUP BY brand
        ORDER BY device_count DESC
        LIMIT 8;
    """, conn)


# -----------------------------------------------------------------------------
# 4. SIDEBAR CONTROLS & FILTERS
# -----------------------------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/7/71/PhonePe_Logo.svg", width=160)
st.sidebar.title("Dashboard Controls")

years, all_categories, all_states = get_filter_options()

selected_year = st.sidebar.selectbox("Select Year", years, index=len(years) - 1)
selected_quarter = st.sidebar.radio("Select Quarter", [1, 2, 3, 4], index=3, horizontal=True)
selected_period = f"{selected_year}-Q{selected_quarter}"

selected_categories = st.sidebar.multiselect("Payment Categories", all_categories, default=all_categories)
if not selected_categories:
    selected_categories = all_categories

selected_state = st.sidebar.selectbox("State / UT Focus", all_states, index=0)

st.sidebar.markdown("---")
st.sidebar.caption("Data Source: [PhonePe Pulse](https://github.com/PhonePe/pulse) (2018–2024)")
st.sidebar.caption("Map Boundary: ODbL / CC-BY (36 States & UTs aligned)")
st.sidebar.caption("Engine: SQLite (`phonepe_pulse.db` 14.1 MB)")


# -----------------------------------------------------------------------------
# 5. HEADER & KPI METRICS
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">PhonePe Platform: UPI Digital Payments Analytics</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">Quarterly transaction dynamics, user registration, and commercial expansion on the <b>PhonePe platform</b> | Period: <b>{selected_period}</b> | Focus: <b>{selected_state}</b></div>', unsafe_allow_html=True)

# Query cached KPI metrics
total_amount, total_count, reg_users, app_opens = get_kpi_metrics(
    selected_period, tuple(selected_categories), selected_state
)
avg_ticket = (total_amount / total_count) if total_count > 0 else 0

# KPI Metric Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    val_str = f"₹{total_amount / 1e12:.2f} T" if total_amount >= 1e12 else f"₹{total_amount / 1e9:.2f} B"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Transaction Value ({selected_period})</div>
        <div class="metric-val">{val_str}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    cnt_str = f"{total_count / 1e9:.2f} B" if total_count >= 1e9 else f"{total_count / 1e6:.2f} M"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Transaction Volume ({selected_period})</div>
        <div class="metric-val">{cnt_str}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Average Ticket Size (Amount/Count)</div>
        <div class="metric-val">₹{avg_ticket:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    u_str = f"{reg_users / 1e6:.2f} M" if reg_users >= 1e6 else f"{reg_users:,}"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Registered Users (Latest Quarter)</div>
        <div class="metric-val">{u_str}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 6. TAB NAVIGATION
# -----------------------------------------------------------------------------
tab_geo, tab_growth, tab_eng, tab_extra = st.tabs([
    "🗺️ Geographic Distribution",
    "📈 Growth & Mix Trajectory",
    "🎯 User Engagement & Untapped Districts",
    "🛡️ Insurance & Hardware Intelligence"
])


# =============================================================================
# TAB 1: GEOGRAPHIC DISTRIBUTION
# =============================================================================
with tab_geo:
    st.subheader(f"State-Level Payment Density on PhonePe ({selected_period})")
    
    col_map, col_rank = st.columns([1.1, 0.9])
    
    with col_map:
        state_map_df = get_state_map_data(selected_period, tuple(selected_categories))
        
        if india_geojson and not state_map_df.empty:
            fig_map = px.choropleth(
                state_map_df,
                geojson=india_geojson,
                featureidkey="properties.NAME_1",
                locations="state",
                color="amount_billion_inr",
                color_continuous_scale="Purples",
                hover_name="state",
                hover_data={
                    "amount_billion_inr": ":,.2f",
                    "total_transactions": ":,",
                    "avg_ticket_size_inr": ":,.2f",
                    "state": False
                },
                labels={
                    "amount_billion_inr": "Value (₹ Billion)",
                    "total_transactions": "Transactions",
                    "avg_ticket_size_inr": "ATS (₹)"
                }
            )
            fig_map.update_geos(fitbounds="locations", visible=False)
            fig_map.update_layout(
                margin={"r": 0, "t": 20, "l": 0, "b": 0},
                height=480,
                coloraxis_colorbar=dict(title="Value (₹ B)", thickness=14, len=0.8)
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Loading map visualization...")

    with col_rank:
        rank_mode = st.radio("Rank By Entity", ["Top 10 States", "Top 10 Districts"], horizontal=True)
        
        if rank_mode == "Top 10 States":
            top_state_df = state_map_df.sort_values(by="amount_billion_inr", ascending=False).head(10)
            fig_rank = px.bar(
                top_state_df,
                x="amount_billion_inr",
                y="state",
                orientation="h",
                text="amount_billion_inr",
                color="amount_billion_inr",
                color_continuous_scale="Purples",
                labels={"amount_billion_inr": "Value (₹ Billion)", "state": "State"}
            )
            fig_rank.update_traces(texttemplate='₹%{text:.1f}B', textposition='outside')
            fig_rank.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=480,
                showlegend=False,
                margin={"r": 35, "t": 20, "l": 0, "b": 0}
            )
            st.plotly_chart(fig_rank, use_container_width=True)
            
        else:
            top_dist_df = get_district_rankings(selected_period, selected_state)
            fig_dist = px.bar(
                top_dist_df,
                x="amount_billion_inr",
                y="district_label",
                orientation="h",
                text="amount_billion_inr",
                color="amount_billion_inr",
                color_continuous_scale="Viridis",
                labels={"amount_billion_inr": "Value (₹ Billion)", "district_label": "District"}
            )
            fig_dist.update_traces(texttemplate='₹%{text:.1f}B', textposition='outside')
            fig_dist.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=480,
                showlegend=False,
                margin={"r": 35, "t": 20, "l": 0, "b": 0}
            )
            st.plotly_chart(fig_dist, use_container_width=True)


# =============================================================================
# TAB 2: GROWTH & MIX TRAJECTORY
# =============================================================================
with tab_growth:
    st.subheader("Platform Growth Trajectory (2018 – 2024)")
    
    trend_df = get_quarterly_trend(selected_state)
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend_df['period'],
        y=trend_df['amount_billion_inr'],
        name="Transaction Value (₹ Billion)",
        mode="lines+markers",
        line=dict(color="#5f259f", width=3),
        marker=dict(size=6)
    ))
    fig_trend.add_trace(go.Scatter(
        x=trend_df['period'],
        y=trend_df['count_million'],
        name="Transaction Volume (Million)",
        mode="lines+markers",
        line=dict(color="#00c853", width=2, dash="dot"),
        yaxis="y2"
    ))
    fig_trend.update_layout(
        title="Quarterly Growth Trend: Payment Value vs Volume",
        xaxis_title="Quarterly Period",
        yaxis=dict(title="Value (₹ Billion)"),
        yaxis2=dict(title="Volume (Million Transactions)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
        margin={"r": 20, "t": 50, "l": 20, "b": 20}
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    col_p2m, col_cat = st.columns(2)
    
    with col_p2m:
        st.subheader("Shift: P2P vs Merchant Payments")
        st.caption("Shares computed over (P2P + Merchant) payments only.")
        mix_df = get_payments_mix()
        
        fig_mix = go.Figure()
        fig_mix.add_trace(go.Bar(x=mix_df['year'], y=mix_df['merchant_vol_share_pct'], name="Merchant Volume Share (%)", marker_color="#5f259f"))
        fig_mix.add_trace(go.Bar(x=mix_df['year'], y=mix_df['merchant_val_share_pct'], name="Merchant Value Share (%)", marker_color="#ff9800"))
        fig_mix.update_layout(
            barmode="group",
            title="Merchant Payments Share of (P2P + Merchant) Over Time",
            xaxis_title="Year",
            yaxis_title="Share (%)",
            height=360,
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_mix, use_container_width=True)

    with col_cat:
        st.subheader(f"Payment Category Mix ({selected_period})")
        cat_df = pd.read_sql_query(f"""
            SELECT category, SUM(amount) AS amount
            FROM agg_transaction
            WHERE period = '{selected_period}'
              {"AND state = '" + selected_state + "'" if selected_state != 'All India' else ''}
            GROUP BY category
            ORDER BY amount DESC;
        """, conn)
        fig_cat = px.pie(
            cat_df,
            names="category",
            values="amount",
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.Purples_r
        )
        fig_cat.update_layout(height=360, margin={"r": 0, "t": 30, "l": 0, "b": 0})
        st.plotly_chart(fig_cat, use_container_width=True)


# =============================================================================
# TAB 3: USER ENGAGEMENT & UNTAPPED DISTRICTS
# =============================================================================
with tab_eng:
    st.subheader(f"District Engagement vs Transaction Value ({selected_period})")
    st.caption("Coloured by transaction intensity (Transactions per Registered User). High registered users with lower transaction velocity highlight untapped expansion pockets.")
    
    scatter_df = get_scatter_data(selected_period)
    
    if not scatter_df.empty:
        fig_scatter = px.scatter(
            scatter_df,
            x="registered_users",
            y="amount_billion_inr",
            size="transaction_count",
            color="tx_per_user",
            color_continuous_scale="Plasma",
            hover_name="district",
            hover_data={
                "state": True,
                "registered_users": ":,",
                "amount_billion_inr": ":,.2f",
                "tx_per_user": ":,.2f",
                "app_opens_per_user": ":,.1f"
            },
            log_x=True,
            labels={
                "registered_users": "Registered Users (Log Scale)",
                "amount_billion_inr": "Transaction Value (₹ Billion)",
                "tx_per_user": "Tx / User",
                "app_opens_per_user": "App Opens / User"
            },
            height=480
        )
        fig_scatter.update_layout(
            margin={"r": 20, "t": 20, "l": 20, "b": 20},
            coloraxis_colorbar=dict(title="Tx / User")
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No district user data available for the selected period.")
        
    st.markdown("---")
    st.subheader("Untapped Growth Opportunities: High Users, Low Velocity")
    st.markdown(r"""
    > **Selection Rule:** Districts with **$\ge$ 500,000 registered users** in the selected period, ranked by lowest quarterly transactions per user.  
    > *Note:* PhonePe Pulse records cumulative registered users, not monthly active users.
    """)
    
    untapped_df = get_untapped_districts(selected_period)
    if not untapped_df.empty:
        st.dataframe(untapped_df, use_container_width=True, hide_index=True)
    else:
        st.info(r"No districts met the $\ge 500,000$ registered users criterion for this period.")


# =============================================================================
# TAB 4: INSURANCE & HARDWARE INTELLIGENCE
# =============================================================================
with tab_extra:
    col_ins, col_dev = st.columns(2)
    
    with col_ins:
        st.subheader("PhonePe Insurance Adoption (2020 – 2024)")
        
        # Check if selected period has insurance data
        is_pre_insurance = (selected_year < 2020) or (selected_year == 2020 and selected_quarter < 2)
        if is_pre_insurance:
            st.info(f"ℹ️ Insurance reporting on the PhonePe platform began in **2020-Q2**. No insurance data is available for **{selected_period}**.")
        
        ins_df = get_insurance_data()
        fig_ins = px.line(
            ins_df,
            x="period",
            y="policies_issued",
            markers=True,
            title="Quarterly Insurance Policies Issued on PhonePe",
            labels={"policies_issued": "Policies Issued", "period": "Quarter"},
            color_discrete_sequence=["#e91e63"]
        )
        fig_ins.update_layout(height=380)
        st.plotly_chart(fig_ins, use_container_width=True)

    with col_dev:
        st.subheader("Hardware OEM Market Share")
        
        is_post_device = (selected_year > 2022) or (selected_year == 2022 and selected_quarter > 1)
        if is_post_device:
            st.info(f"ℹ️ PhonePe discontinued reporting user device brands after **2022-Q1**. Showing benchmark hardware market share from **2022-Q1**.")
            dev_df = get_device_data("2022-Q1")
        else:
            dev_df = get_device_data(selected_period)
            
        if dev_df is not None and not dev_df.empty:
            fig_dev = px.bar(
                dev_df,
                x="share_pct",
                y="brand",
                orientation="h",
                text="share_pct",
                color="share_pct",
                color_continuous_scale="Teal",
                labels={"share_pct": "Market Share (%)", "brand": "Brand"}
            )
            fig_dev.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_dev.update_layout(
                title=f"Device Brand Share ({'2022-Q1 Benchmark' if is_post_device else selected_period})",
                height=380,
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False
            )
            st.plotly_chart(fig_dev, use_container_width=True)
        else:
            st.info("No device data available.")
