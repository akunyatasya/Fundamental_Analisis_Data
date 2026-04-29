import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ======================
# LOAD DATA
# ======================
# Gunakan main_data.csv sebagai data utama
df = pd.read_csv("dashboard/main_data.csv")

# Cari kolom customer_id
customer_col = [col for col in df.columns if 'customer_id' in col][0]

# Cari kolom timestamp
timestamp_col = [col for col in df.columns if 'order_purchase_timestamp' in col][0]

# Convert to datetime
df[timestamp_col] = pd.to_datetime(df[timestamp_col])

# Reference date (hari terakhir dalam data + 1)
reference_date = df[timestamp_col].max() + pd.Timedelta(days=1)

# Hitung RFM per customer
rfm = df.groupby(customer_col).agg({
    timestamp_col: lambda x: (reference_date - x.max()).days,  # Recency
    'order_id': 'count',  # Frequency
    'payment_value': 'sum'  # Monetary
}).reset_index()

rfm.columns = ['customer_id', 'recency', 'frequency', 'monetary']

st.title("Dashboard Analisis RFM Customer")

# ======================
# PREVIEW DATA
# ======================
st.subheader("Data Customer (RFM)")
st.dataframe(rfm)

# ======================
# KPI SEDERHANA
# ======================
st.subheader("Ringkasan Data")

st.metric("Total Customer", len(rfm))
st.metric("Rata-rata Frequency", round(rfm["frequency"].mean(), 2))
st.metric("Rata-rata Monetary", round(rfm["monetary"].mean(), 2))

# ======================
# VISUALISASI DISTRIBUSI
# ======================
st.subheader("Distribusi Frequency vs Monetary")

fig, ax = plt.subplots()
ax.scatter(rfm["frequency"], rfm["monetary"], alpha=0.5)
ax.set_title("Frequency vs Monetary")
ax.set_xlabel("Frequency")
ax.set_ylabel("Monetary")

st.pyplot(fig)

# ======================
# RFM SCORING & GROUPING
# ======================
st.subheader("RFM Scoring (Binning Manual)")

# Recency: semakin kecil semakin baik (beli lagi baru2)
rfm['R_Score'] = pd.qcut(rfm['recency'], q=4, labels=[4, 3, 2, 1])

# Frequency: semakin besar semakin baik
rfm['F_Score'] = pd.qcut(rfm['frequency'].rank(method='first'), q=4, labels=[1, 2, 3, 4])

# Monetary: semakin besar semakin baik
rfm['M_Score'] = pd.qcut(rfm['monetary'], q=4, labels=[1, 2, 3, 4])

# Combined RFM Score
rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)

st.dataframe(rfm[['customer_id', 'recency', 'frequency', 'monetary', 'R_Score', 'F_Score', 'M_Score', 'RFM_Score']])

# ======================
# SEGMENTASI CUSTOMER
# ======================
st.subheader("Segmentasi Customer")

def segment_customer(row):
    r, f, m = int(row['R_Score']), int(row['F_Score']), int(row['M_Score'])
    score = r + f + m
    
    if score >= 10:
        return "Champions"
    elif score >= 8:
        return "Loyal Customers"
    elif score >= 6:
        return "Potential Loyal"
    elif score >= 5:
        return "At Risk"
    else:
        return "Lost/Hibernating"

rfm['Segment'] = rfm.apply(segment_customer, axis=1)

# Tampilkan segmentasi
segment_counts = rfm['Segment'].value_counts()
st.write("Jumlah Customer per Segment:")
st.dataframe(segment_counts)

# Visualisasi segment
fig2, ax2 = plt.subplots()
segment_counts.plot(kind='bar', ax=ax2, color=['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#95a5a6'])
ax2.set_title("Distribusi Segment Customer")
ax2.set_xlabel("Segment")
ax2.set_ylabel("Jumlah Customer")
ax2.tick_params(axis='x', rotation=45)
st.pyplot(fig2)

# ======================
# INSIGHT & REKOMENDASI
# ======================
st.subheader("Insight & Rekomendasi")

# Hitung metrics untuk insight
total_customer = len(rfm)
champions = len(rfm[rfm['Segment'] == 'Champions'])
loyal = len(rfm[rfm['Segment'] == 'Loyal Customers'])
at_risk = len(rfm[rfm['Segment'] == 'At Risk'])
lost = len(rfm[rfm['Segment'] == 'Lost/Hibernating'])

avg_monetary = rfm['monetary'].mean()
total_revenue = rfm['monetary'].sum()

st.write(f"""
### Ringkasan Data:
- **Total Customer:** {total_customer:,} customer
- **Total Revenue:** ${total_revenue:,.2f}
- **Rata-rata Monetary per Customer:** ${avg_monetary:,.2f}

### Segmentasi:
- **Champions:** {champions} customer ({champions/total_customer*100:.1f}%) - Paling berharga!
- **Loyal Customers:** {loyal} customer ({loyal/total_customer*100:.1f}%)
- **At Risk:** {at_risk} customer ({at_risk/total_customer*100:.1f}%)
- **Lost/Hibernating:** {lost} customer ({lost/total_customer*100:.1f}%)

### Rekomendasi Strategi:
1. **Champions:** Berikan reward eksklusif & early access produk baru
2. **Loyal Customers:** Tingkatkan engagement dengan program loyalty
3. **At Risk:** Kirim reminder & offer khusus untuk mengembalikan aktivitas
4. **Lost/Hibernating:** Kampanye re-activation dengan diskon besar
""")
