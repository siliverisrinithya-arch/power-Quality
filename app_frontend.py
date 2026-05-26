import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Power Quality AI Dashboard", layout="wide")
st.title("⚡ Power Quality Compliance Dashboard")
st.markdown("Substation Grid Audit Logging Engine")
st.markdown("---")

API_URL = "http://127.0.0.1:8000/api/metrics/check"

try:
    response = requests.get(API_URL).json()
    records = response if isinstance(response, list) else response.get("report", [])
    
    parsed_data = []
    for r in records:
        m = r.get("metrics", {})
        parsed_data.append({
            "Timestamp": r.get("timestamp", "N/A"),
            "Voltage (V)": m.get("voltage_LL", 0),
            "Frequency (Hz)": m.get("frequency", 0),
            "Unbalance (%)": m.get("voltage_unbalance", 0),
            "THD (%)": m.get("voltage_THD", 0),
            "Status": r.get("status", "Unknown"),
            "Violations Report": ", ".join(r.get("violations", [])) if r.get("violations") else "None"
        })
    
    df = pd.DataFrame(parsed_data)
    st.metric("Total System Records", len(records))
    st.subheader("📊 Metric Progression Trends")
    if not df.empty:
        st.line_chart(df, x="Timestamp", y="THD (%)")
    st.subheader("📋 Comprehensive Log Audit Trail")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Dashboard Processing Error: {e}")
