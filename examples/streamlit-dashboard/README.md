# Streamlit Dashboard

Interaktywny dashboard do analizy danych sprzedażowych.

## Uruchomienie

```bash
markpact examples/streamlit-dashboard/README.md
```

Dashboard będzie dostępny pod: http://localhost:8501

## Funkcje

- Wczytywanie danych CSV
- Wykresy interaktywne (Plotly)
- Filtry po dacie i kategorii
- Statystyki zbiorcze
- Eksport do CSV

---

```markpact:deps python
streamlit
pandas
plotly
```

```markpact:file python path=app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

# Generate sample data
@st.cache_data
def generate_sample_data():
    categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
    regions = ["North", "South", "East", "West"]
    
    data = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(1000):
        data.append({
            "date": base_date + timedelta(days=random.randint(0, 365)),
            "category": random.choice(categories),
            "region": random.choice(regions),
            "sales": random.randint(100, 10000),
            "quantity": random.randint(1, 50),
        })
    
    return pd.DataFrame(data)

df = generate_sample_data()

# Header
st.title("📊 Sales Dashboard")
st.markdown("---")

# Sidebar filters
st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    value=(df["date"].min(), df["date"].max()),
    min_value=df["date"].min(),
    max_value=df["date"].max()
)

categories = st.sidebar.multiselect(
    "Categories",
    options=df["category"].unique(),
    default=df["category"].unique()
)

regions = st.sidebar.multiselect(
    "Regions",
    options=df["region"].unique(),
    default=df["region"].unique()
)

# Filter data
mask = (
    (df["date"] >= pd.Timestamp(date_range[0])) &
    (df["date"] <= pd.Timestamp(date_range[1])) &
    (df["category"].isin(categories)) &
    (df["region"].isin(regions))
)
filtered_df = df[mask]

# KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Sales", f"${filtered_df['sales'].sum():,.0f}")
with col2:
    st.metric("Total Quantity", f"{filtered_df['quantity'].sum():,}")
with col3:
    st.metric("Avg Sale", f"${filtered_df['sales'].mean():,.0f}")
with col4:
    st.metric("Transactions", f"{len(filtered_df):,}")

st.markdown("---")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Sales by Category")
    fig = px.pie(
        filtered_df.groupby("category")["sales"].sum().reset_index(),
        values="sales",
        names="category",
        hole=0.4
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Sales by Region")
    fig = px.bar(
        filtered_df.groupby("region")["sales"].sum().reset_index(),
        x="region",
        y="sales",
        color="region"
    )
    st.plotly_chart(fig, use_container_width=True)

# Time series
st.subheader("Sales Over Time")
daily_sales = filtered_df.groupby(filtered_df["date"].dt.date)["sales"].sum().reset_index()
fig = px.line(daily_sales, x="date", y="sales")
st.plotly_chart(fig, use_container_width=True)

# Data table
st.subheader("Raw Data")
st.dataframe(filtered_df, use_container_width=True)

# Export
if st.button("Export to CSV"):
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="sales_export.csv",
        mime="text/csv"
    )
```

```markpact:run python
streamlit run app.py --server.port ${MARKPACT_PORT:-8501}
```
