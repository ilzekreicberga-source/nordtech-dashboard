import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Datu ielāde
df = pd.read_csv('enriched_data.csv')
df['Date'] = pd.to_datetime(df['Date'])
# Noņemam liekās atstarpes un dublikātus kategorijām
df['Product_Category'] = df['Product_Category'].str.strip()

tickets = pd.read_csv('tickets_cleaned.csv')
tickets['Date_Logged'] = pd.to_datetime(tickets['Date_Logged'])

# Sasaistām sūdzības ar kategorijām
customer_map = df[['Customer_ID', 'Product_Category']].drop_duplicates()
tickets_with_cat = tickets.merge(customer_map, on='Customer_ID', how='left')
tickets_with_cat['Product_Category'] = tickets_with_cat['Product_Category'].str.strip()

st.set_page_config(page_title="NordTech Analītika", layout="wide")
st.title("🛡️ NordTech Biznesa Operāciju Panelis")

# 2. SĀNJOSLAS FILTRI
st.sidebar.header("Iestatījumi")

# Tīrs kategoriju saraksts
available_cats = sorted(df['Product_Category'].unique().tolist())
selected_cat = st.sidebar.multiselect("Produktu kategorija:", options=available_cats, default=available_cats)

# --- LABOTS KALENDĀRS ---
min_d = df['Date'].min().date()
max_d = df['Date'].max().date()

# Pievienojam min/max robežas, lai kalendārā varētu viegli pārslēgties starp mēnešiem
date_range = st.sidebar.date_input(
    "Periods (no - līdz):", 
    value=(min_d, max_d),
    min_value=min_d,
    max_value=max_d
)

# Drošības pārbaude datumu diapazonam
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_d, max_d

# --- FILTRĒŠANA ---
f_df = df[(df['Product_Category'].isin(selected_cat)) & 
         (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)]

f_tickets = tickets_with_cat[(tickets_with_cat['Product_Category'].isin(selected_cat)) & 
                            (tickets_with_cat['Date_Logged'].dt.date >= start_date) & 
                            (tickets_with_cat['Date_Logged'].dt.date <= end_date)]

# 3. KPI Rinda
c1, c2, c3 = st.columns(3)
c1.metric("Kopējie Ieņēmumi", f"${f_df['Revenue'].sum():,.2f}")
c2.metric("Atgriezumu Summa", f"${f_df['Refund_Amount'].sum():,.2f}")
c3.metric("Sūdzību Skaits", len(f_tickets))

st.markdown("---")

# 4. GRAFIKI
left, right = st.columns(2)

with left:
    st.subheader("Ieņēmumu un atgriezumu dinamika")
    l_data = f_df.groupby('Date')[['Revenue', 'Refund_Amount']].sum().reset_index()
    fig_l = px.line(l_data, x='Date', y=['Revenue', 'Refund_Amount'],
                    color_discrete_map={'Revenue': '#2ca02c', 'Refund_Amount': '#d62728'},
                    template="plotly_dark")
    st.plotly_chart(fig_l, use_container_width=True)

with right:
    st.subheader("Sūdzību iemesli (filtrēti)")
    if not f_tickets.empty:
        t_counts = f_tickets['Complaint_Category'].value_counts().reset_index()
        fig_p = px.pie(t_counts, values='count', names='Complaint_Category',
                       color_discrete_sequence=px.colors.qualitative.Pastel)
        # Uzstādām, lai pīrāgs rādītu tos pašus % ko Colab
        fig_p.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_p, use_container_width=True)
    else:
        st.info("Šajā atlasē sūdzību nav.")

# 5. TABULA
st.subheader("⚠️ Top problemātiskie darījumi")
st.dataframe(f_df[f_df['Refund_Amount'] > 0].sort_values('Refund_Amount', ascending=False).head(10)[['Transaction_ID', 'Product_Name', 'Refund_Amount']], use_container_width=True)
