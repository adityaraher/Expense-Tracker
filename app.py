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
    raw_data = sh.get_all_values()
    
    if len(raw_data) > 1:
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        df = df.loc[:, ~df.columns.duplicated()]
        
        # FIX 1: Strip hidden spaces from categories to combine duplicates
        if "Category" in df.columns:
            df['Category'] = df['Category'].str.strip()
            
        # FIX 2: Convert text dates to actual Python dates to extract the month
        if "Date" in df.columns:
            # dayfirst=True handles Indian date formats like DD/MM/YY
            df['Parsed_Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            # Create a "Month Year" column (e.g., 'September 2026')
            df['Month'] = df['Parsed_Date'].dt.strftime('%B %Y').fillna('Unknown')
            
        if "Amount" in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
            
        # --- MONTHLY SEGREGATION FILTER ---
        if "Month" in df.columns:
            valid_months = df[df['Month'] != 'Unknown']['Month'].unique()
            if len(valid_months) > 0:
                # Add a dropdown menu to select the month
                selected_month = st.selectbox("Filter by Month", ["All Time"] + list(valid_months))
                
                # Filter the dataframe if a specific month is chosen
                if selected_month != "All Time":
                    df = df[df['Month'] == selected_month]
        
        if "Amount" in df.columns:
            total_spent = df['Amount'].sum()
            st.metric(label="Total Expenses", value=f"₹{total_spent:,.2f}")
        
        st.subheader("By Category")
        if "Category" in df.columns and "Amount" in df.columns:
            category_sums = df.groupby("Category")["Amount"].sum().reset_index()
            st.bar_chart(category_sums, x="Category", y="Amount")
        
        st.subheader("Recent Transactions")
        display_cols = [c for c in ["Date", "Description", "Amount", "Category"] if c in df.columns]
        if display_cols:
            st.dataframe(df[display_cols].tail(5), use_container_width=True)
        else:
            st.dataframe(df.tail(5), use_container_width=True)
            
    else:
        st.info("No expenses logged yet.")
