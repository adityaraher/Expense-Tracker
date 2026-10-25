import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# Set up the page for a mobile-first feel
st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="centered")

# Authenticate and connect
import json
credentials = json.loads(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)
sh = gc.open("Expense Tracker").sheet1

st.title("💸 Expense Tracker")

# Use tabs to keep the mobile interface clean
tab1, tab2 = st.tabs(["📝 Log Expense", "📊 Dashboard"])

with tab1:
    with st.form("expense_form", clear_on_submit=True):
        date = st.date_input("Date", datetime.today())
        description = st.text_input("Description")
        amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
        category = st.selectbox("Category", ["Food", "Travel", "Accessories", "Stationary", "Medical"])
        
        if st.form_submit_button("Log Expense"):
            formatted_date = date.strftime("%d/%m/%y")
            sh.append_row([formatted_date, description, amount, category])
            st.success(f"Logged ₹{amount} for {description}!")

with tab2:
    # Fetch all raw data as a simple list of lists
    raw_data = sh.get_all_values()
    
    if len(raw_data) > 1:
        # Use the first row as column headers, and the rest as data
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        
        # --- THE FIX: Drop any duplicate or empty ghost columns ---
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Clean the data: convert Amount to numbers safely
        if "Amount" in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
            
            # Calculate total spending
            total_spent = df['Amount'].sum()
            st.metric(label="Total Expenses", value=f"₹{total_spent:,.2f}")
        
        # Calculate and chart spending by category
        st.subheader("By Category")
        if "Category" in df.columns and "Amount" in df.columns:
            category_sums = df.groupby("Category")["Amount"].sum().reset_index()
            st.bar_chart(category_sums, x="Category", y="Amount")
        
        # Show the 5 most recent transactions
        st.subheader("Recent Transactions")
        
        # Only show the main 4 columns so the table stays clean on mobile
        display_cols = [c for c in ["Date", "Description", "Amount", "Category"] if c in df.columns]
        if display_cols:
            st.dataframe(df[display_cols].tail(5), use_container_width=True)
        else:
            st.dataframe(df.tail(5), use_container_width=True)
            
    else:
        st.info("No expenses logged yet.")