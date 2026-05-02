import streamlit as st
import pandas as pd
from datetime import datetime
from main import run_fraud_agent_loop # Imports the loop from our main.py

st.set_page_config(page_title="Banking Fraud Dashboard", layout="wide", page_icon="💳")

# --- Helper: Load Account Data ---
@st.cache_data
def get_user_data(user_id="U001"):
    try:
        df = pd.read_csv("transactions.csv")
        user_df = df[df["user_id"] == user_id].copy()
        # Ensure latest transactions are at the top
        user_df["timestamp_dt"] = pd.to_datetime(user_df["timestamp"], format="%d/%m/%Y %H:%M", errors='coerce')
        user_df = user_df.sort_values(by="timestamp_dt", ascending=False)
        return df, user_df
    except FileNotFoundError:
        return pd.DataFrame(), pd.DataFrame()

current_user = "U001"
full_df, user_history = get_user_data(current_user)

# --- Helper: Save New Transaction ---
def append_transaction_to_csv(txn_payload, current_balance):
    """Formats the payload to match the CSV schema and safely saves it."""
    import os
    try:
        # Load the current file safely
        if os.path.exists("transactions.csv"):
            full_df = pd.read_csv("transactions.csv")
        else:
            full_df = pd.DataFrame()

        # Generate a new sequential Transaction ID (e.g., T024)
        if not full_df.empty and "transaction_id" in full_df.columns:
            last_id = full_df.iloc[-1]["transaction_id"]
            # Extract number, increment, and format back to TXXX
            new_num = int(str(last_id).replace("T", "")) + 1
            new_txn_id = f"T{new_num:03d}"
            
            # Calculate avg amount
            user_history = full_df[full_df["user_id"] == txn_payload["user_id"]]
            avg_amt = user_history["amount"].mean() if not user_history.empty else txn_payload["amount"]
        else:
            new_txn_id = "T001"
            avg_amt = txn_payload["amount"]

        # Create a new row matching your exact transactions.csv columns
        new_row = {
            "transaction_id": new_txn_id,
            "user_id": txn_payload["user_id"],
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "amount": txn_payload["amount"],
            "payment_type": txn_payload["payment_type"],
            "receiver_id": txn_payload["receiver_id"],
            "receiver_bank": "Local Bank",  
            "receiver_country": txn_payload["receiver_country"],
            "sender_country": txn_payload["sender_country"],
            "device_id": txn_payload["device_id"],
            "ip_address": "192.168.1.1", 
            "login_attempts": txn_payload["login_attempts"],
            "balance_before": current_balance,
            "time_since_last_txn": txn_payload["time_since_last_txn"],
            "avg_user_amount": int(avg_amt)
        }

        # Safer Save Method: Concat and overwrite 
        new_df = pd.DataFrame([new_row])
        if not full_df.empty:
            updated_df = pd.concat([full_df, new_df], ignore_index=True)
        else:
            updated_df = new_df
            
        # Overwrite the file completely to avoid newline corruption
        updated_df.to_csv("transactions.csv", index=False)
        
        # Clear Streamlit's cache so the UI re-reads the updated CSV
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving transaction: {e}")
        return False

# --- UI Setup ---
st.title("💳 Banking Portal & Fraud Detection")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    st.info("Transactions are now saved to `transactions.csv` upon submission.")

# --- Section 1: Account Info ---
st.header("👤 Account Dashboard")
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Account Details")
    st.write(f"**User ID:** `{current_user}`")
    
    # Calculate dynamic balance
    current_balance = 12500.00 # Fallback default
    if not user_history.empty and "balance_before" in user_history.columns:
         last_balance = float(user_history.iloc[0]["balance_before"])
         last_amt = float(user_history.iloc[0]["amount"])
         current_balance = last_balance - last_amt
         
    st.metric("Current Balance", f"${current_balance:,.2f}")

with col2:
    st.subheader("Recent Transactions")
    if not user_history.empty:
        # Display the newest 5 records
        display_df = user_history.head(5)[["timestamp", "receiver_id", "payment_type", "amount"]]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.write("No recent transactions found.")

st.divider()

# --- Section 2: Transaction Input Form ---
st.header("💸 Send Money")
with st.form("transfer_form"):
    t_col1, t_col2 = st.columns(2)
    
    with t_col1:
        receiver_id = st.text_input("Receiver Account ID / Name", placeholder="e.g., Alice")
        amount = st.number_input("Amount ($)", min_value=1.0, value=150.0, step=10.0)
        payment_type = st.selectbox("Payment Method", ["FPS", "CHATS", "SWIFT"])
        
    with t_col2:
        receiver_country = st.text_input("Receiver Country Code", value="HK")
        device_id = st.text_input("Current Device ID", value="iphone13")
        
    submit_btn = st.form_submit_button("Submit Transfer", type="primary")

# --- Section 3: Execution ---
if submit_btn:
    if amount > current_balance:
        st.error("❌ Insufficient Funds for this transfer.")
    elif not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
    else:
        # 1. Compile data to send to our main.py loop
        import os # ensure os is imported
        txn_payload = {
            "user_id": current_user,
            "amount": amount,
            "payment_type": payment_type,
            "receiver_id": receiver_id,
            "receiver_country": receiver_country,
            "sender_country": "HK",
            "device_id": device_id,
            "login_attempts": 1, 
            "time_since_last_txn": 120,
            "hour": datetime.now().hour
        }

        st.info("Processing transaction through Risk Agent...")
        
        with st.spinner("Agent is extracting features and calculating risk..."):
            try:
                # 2. Trigger AI Fraud Agent
                final_analysis = run_fraud_agent_loop(txn_payload, api_key)
                
                # Normalize text to safely parse response
                if isinstance(final_analysis, list):
                    full_text = " ".join([str(item) for item in final_analysis])
                else:
                    full_text = str(final_analysis)
                    
                clean_text = full_text.upper().replace("*", "")
                
                # 3. Dynamic UI feedback & Save Logic
                if "RECOMMENDATION: APPROVE" in clean_text:
                    st.success("Transaction Approved ✅")
                    
                    # SAVE TO CSV IF APPROVED
                    if append_transaction_to_csv(txn_payload, current_balance):
                        st.toast("Transaction successfully recorded in database!")
                        # Force a rerun to update the UI with new balance and history
                        # st.rerun() 
                        
                elif "RECOMMENDATION: REVIEW" in clean_text:
                    st.warning("Transaction Flagged for Review ⚠️")
                    st.info("Transaction placed on hold. Not deducted from balance yet.")
                    
                elif "RECOMMENDATION: BLOCK" in clean_text:
                    st.error("Transaction Blocked 🚨")
                else:
                    st.info("Analysis complete, but no clear recommendation found.")
                
                # 4. Show the final explanation directly from Gemini
                with st.expander("View Agent Output Log", expanded=True):
                    st.write(final_analysis)
                
            except Exception as e:
                st.error(f"Error executing agent loop: {e}")