import streamlit as st
from sqlalchemy import select
from database import engine, inventory_table
from invoices import process_booker_invoice

st.title("Invoice Price Updater")

# 1. File Uploader
uploaded_file = st.file_uploader("Upload Booker PDF Invoice", type=["pdf"])

if uploaded_file is not None:
    if st.button("Process Invoice"):
        logs = process_booker_invoice(uploaded_file)
        st.success(f"Processed {len(logs)} items from invoice.")
        st.markdown(logs)

# 2. View Current Database
st.subheader("Current Inventory Database")
with engine.connect() as conn:
    rows = conn.execute(select(inventory_table)).mappings().all()
    st.markdown(rows)