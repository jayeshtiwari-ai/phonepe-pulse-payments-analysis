# UPI Digital Payments Growth and Opportunity Analysis using PhonePe Pulse Data

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-1.45.1-FF4B4B.svg)](https://streamlit.io/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20MySQL%208.0-00758F.svg)](https://www.mysql.com/)
[![License: CDLA-Permissive-2.0](https://img.shields.io/badge/Data%20License-CDLA--Permissive--2.0-green.svg)](https://cdla.dev/permissive-2-0/)

An end-to-end data analytics and business intelligence project exploring the rapid growth, structural payment shifts, consumer engagement, and regional market opportunities across India using PhonePe Pulse data (2018–2024).

---

## 📌 Problem Statement

The Indian digital payments revolution has transformed how hundreds of millions of consumers and merchants transact daily. However, digital payment penetration remains unevenly distributed across states, districts, and merchant categories. 

This project analyzes the official PhonePe Pulse dataset to address critical business and policy questions:
1. **Structural Transition:** How has payment mix shifted between Peer-to-Peer (P2P) transfers and Merchant commerce (P2M) from 2018 to 2024?
2. **Untapped Regional Pockets:** Which districts demonstrate high user adoption (>500,000 registered users) yet lag in transaction velocity?
3. **Seasonality:** How pronounced is the annual Q4 holiday/festive payment surge over the baseline?
4. **Financial Inclusion:** How rapidly is digital insurance penetrating non-metro markets?
5. **Hardware Landscape:** How do smartphone OEM market shares correlate with high-value digital transaction density?

---

## 📂 Data Source & Attribution

- **Primary Source:** [PhonePe Pulse Official Dataset](https://github.com/PhonePe/pulse)
- **Data License:** Licensed under the [Community Data License Agreement – Permissive – Version 2.0 (CDLA-Permissive-2.0)](https://cdla.dev/permissive-2-0/).
- **Scope:** 2018-Q1 through 2024-Q4 on the canonical `master` repository branch.
- **Administrative GeoJSON:** Open-source India administrative boundaries adapted from DataMeet / GADM (`geohacker/india`) under ODbL / CC-BY 4.0.
- **Disclaimer:** *This analytics project is an independent study conducted for educational and portfolio demonstration purposes. It is not affiliated with, endorsed by, or sponsored by PhonePe Private Limited.*

---

## 🏗️ Architecture & Pipeline

```text
[PhonePe Pulse GitHub Repository]
               │
               ▼ (Git Clone / Subtree)
┌────────────────────────────────────────────────────────┐
│  ETL Pipeline (Modular Architecture)                   │
├────────────────────────────────────────────────────────┤
│  1. extract.py                                         │
│     - Traverses 10,000+ hierarchical JSON files        │
│     - Standardises State & District naming             │
│     - Splits aggregated user & hardware device cuts    │
│     - Normalises missing entities (Unknown pincodes)   │
│                                                        │
│  2. clean.py                                           │
│     - Generates standard period format (YYYY-QN)       │
│     - Imputes missing categories & verifies 0 nulls    │
│     - Verifies composite primary keys & completeness   │
│     - Emits 10 validated CSVs to data_clean/           │
│                                                        │
│  3. load.py                                            │
│     - Reads credentials from .env via SQLAlchemy       │
│     - Auto-provisions schema.sql tables & indexes      │
│     - Loads 119,661 rows into MySQL 8.0                │
│     - Generates portable SQLite replica (14.1 MB)      │
└────────────────────────────────────────────────────────┘
               │
               ├──► queries.sql (14 Production Analytical Queries)
               ├──► insights.md (Executive Findings & Strategy)
               │
               ▼
┌────────────────────────────────────────────────────────┐
│  Interactive Business Intelligence Dashboard           │
│  (app.py - Streamlit + Plotly + SQLite)                │
├────────────────────────────────────────────────────────┤
│  * Dynamic KPI Badges (Value, Volume, ATS, Users)      │
│  * Plotly India State Choropleth Map (36 States/UTs)   │
│  * P2P vs Merchant Payments Mix (2018–2024)            │
│  * Engagement vs Value Bubble Analysis                 │
│  * Insurance Growth & Hardware OEM Intelligence        │
└────────────────────────────────────────────────────────┘
```

---

## 🗄️ Relational Schema Summary

All 10 tables enforce **Composite Primary Keys** and **Composite Indexes on `(state, year, quarter)`** to guarantee data integrity and low query latency:

| Table Name | Grain / Entity | Key Columns | Row Count |
| :--- | :--- | :--- | :--- |
| **`agg_transaction`** | State $\times$ Year $\times$ Qtr $\times$ Category | `state`, `year`, `quarter`, `period`, `category`, `count`, `amount` | **5,034** |
| **`agg_user`** | State $\times$ Year $\times$ Qtr | `state`, `year`, `quarter`, `period`, `registered_users`, `app_opens` | **1,008** |
| **`agg_user_device`** | State $\times$ Year $\times$ Qtr $\times$ Brand | `state`, `year`, `quarter`, `period`, `brand`, `count`, `percentage` | **6,732** |
| **`agg_insurance`** | State $\times$ Year $\times$ Qtr $\times$ Category | `state`, `year`, `quarter`, `period`, `category`, `count`, `amount` | **682** |
| **`map_transaction`** | State $\times$ District $\times$ Year $\times$ Qtr | `state`, `district`, `year`, `quarter`, `period`, `count`, `amount` | **20,604** |
| **`map_user`** | State $\times$ District $\times$ Year $\times$ Qtr | `state`, `district`, `year`, `quarter`, `period`, `registered_users`, `app_opens` | **20,608** |
| **`map_insurance`** | State $\times$ District $\times$ Year $\times$ Qtr | `state`, `district`, `year`, `quarter`, `period`, `count`, `amount` | **13,876** |
| **`top_transaction`** | Level $\times$ State $\times$ Entity $\times$ Year $\times$ Qtr | `level`, `state`, `entity_type`, `entity_name`, `year`, `quarter`, `count`, `amount` | **19,135** |
| **`top_user`** | Level $\times$ State $\times$ Entity $\times$ Year $\times$ Qtr | `level`, `state`, `entity_type`, `entity_name`, `year`, `quarter`, `registered_users` | **19,136** |
| **`top_insurance`** | Level $\times$ State $\times$ Entity $\times$ Year $\times$ Qtr | `level`, `state`, `entity_type`, `entity_name`, `year`, `quarter`, `count`, `amount` | **12,846** |
| **TOTAL** | — | — | **119,661** |

---

## 🚀 How to Run the Project

### Option A: Zero-Config Quick Start (SQLite)
The repository includes the self-contained, validated database (`phonepe_pulse.db`, 14.1 MB). No database server installation is required.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/phonepe-pulse-analytics.git
   cd phonepe-pulse-analytics
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the dashboard:**
   ```bash
   streamlit run app.py
   ```
   The dashboard will automatically open in your default browser at `http://localhost:8501`.

---

### Option B: Full Pipeline Reproduction (MySQL + Python ETL)

1. **Copy the environment configuration:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your local MySQL credentials:
   ```ini
   DB_TYPE=mysql
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=phonepe_pulse
   ```

2. **Clone the PhonePe Pulse raw dataset:**
   ```bash
   git clone https://github.com/PhonePe/pulse.git pulse
   git -C pulse checkout master
   ```

3. **Execute ETL pipeline:**
   ```bash
   # Step 1: Extract JSON files into clean DataFrames
   python extract.py

   # Step 2: Validate data quality and add period column
   python clean.py

   # Step 3: Provision schema and load MySQL database
   python load.py
   ```

---

## 💡 Key Analytical Findings

1. **Merchant Commerce Surge:** Merchant payments (P2M) expanded from **17.70%** (2018) to **64.53%** (2024) of total $(P2P + Merchant)$ volume, showing PhonePe's transition into an everyday retail cash replacement (ATS ~₹463 vs P2P ATS ~₹2,914).
2. **Untapped High-Adoption Districts:** Analysis of mature districts ($\ge 500,000$ registered users) shows significant regional variation: Palakkad (14.07 tx/user) and Thrissur (14.10 tx/user) in Kerala, and Anand (14.24 tx/user) in Gujarat operate at less than half the national district median (**36.62 tx/user** in 2024-Q4).
3. **Festive Seasonality:** Across 2019–2024, sequential Q4 QoQ growth averaged **22.89%**, outpacing the Q1–Q3 average QoQ growth of **17.39%** by **+5.50 percentage points**, driven by Diwali/Dussehra shopping.
4. **Digital Insurance Growth:** Non-metro states saw policy counts jump 45–51% YoY in 2024-Q4 (Bihar +51.19%, Rajasthan +47.83%), though state insurance density remains low (<40 policies per 10k users).
5. **Hardware Landscape:** In 2022-Q1, budget-to-midrange Android OEMs captured **84.01%** of platform devices (Xiaomi 23.71%, Vivo 20.71%, Samsung 17.67%). Apple iOS represented 2.89% nationally, but concentrated in Punjab (7.41%), Kerala (6.14%), and Delhi (5.62%).
6. **Value Concentration:** In 2024, Karnataka (₹15.33T), Maharashtra (₹14.78T), and Telangana (₹14.08T) generated **34.10%** of all platform payment value.

---

## 📸 Screenshots

*(Replace with dashboard screenshots upon deployment)*

| Geographic Distribution & Choropleth Map | Growth & Payments Mix (P2P vs Merchant) |
| :---: | :---: |
| ![Choropleth Map Placeholder](screenshots/map_overview.png) | ![Growth Trend Placeholder](screenshots/growth_trends.png) |

| Engagement vs Transaction Value Bubble Plot | Insurance & Device Hardware Intelligence |
| :---: | :---: |
| ![Bubble Plot Placeholder](screenshots/engagement_scatter.png) | ![Insurance Placeholder](screenshots/insurance_devices.png) |

---

## ⚠️ Limitations

- **Aggregated & Anonymised Data:** Data is aggregated at state, district, and top pincode levels; no individual user records, income brackets, or merchant-item level data are available.
- **Platform Boundary:** Metrics reflect payment transactions executed strictly on the **PhonePe platform**, not the entire NPCI UPI network.
- **Hardware Deprecation:** Device manufacturer data was discontinued by PhonePe after **2022-Q1**.
- **Top Rankings Scope:** Top district and pincode tables capture the top 10 entities per cut rather than a full census.

---

## ☁️ Streamlit Community Cloud Deployment Guide

Deploy this application to the web for free in under 3 minutes:

1. Push your repository to **GitHub** (ensure `phonepe_pulse.db`, `india_states.geojson`, `app.py`, and `requirements.txt` are included).
2. Visit [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
3. Click **"New app"**.
4. Select your repository: `<your-username>/phonepe-pulse-analytics`.
5. Set **Main file path:** `app.py`.
6. Click **"Deploy!"**. The app will automatically build using `phonepe_pulse.db` without any database configuration needed.

---

## 📁 Project Structure

```text
├── .gitignore               # Excludes .env, virtual envs, pulse raw data
├── .env.example             # Database configuration template with placeholders
├── requirements.txt         # Pinned production Python dependencies
├── extract.py               # Modular ETL extractor for PhonePe Pulse JSONs
├── clean.py                 # Data cleaner, quality validator & period formatter
├── load.py                  # Dual database loader (MySQL 8.0 & SQLite fallback)
├── schema.sql               # Relational DDL with Composite PKs & Indexes
├── queries.sql              # 14 Production SQL business analytics queries
├── insights.md              # Executive findings, strategic recommendations & limitations
├── india_states.geojson     # Optimized India administrative boundaries (152 KB)
├── phonepe_pulse.db         # Self-contained SQLite database (14.1 MB, 119k rows)
├── app.py                   # Interactive Streamlit + Plotly web dashboard
└── README.md                # Project documentation & execution guide
```
