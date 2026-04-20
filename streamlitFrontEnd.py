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
        user_df = user_df.sort_values(by="timestamp", ascending=False)
        return user_df
    except:
        return pd.DataFrame()

current_user = "U001"
user_history = get_user_data(current_user)

# --- UI Setup ---
st.title("💳 Banking Portal & Fraud Detection")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    st.info("The agent loop is now powered natively via bind_tools() exactly like your IPYNB assignment.")

# --- Section 1: Account Info ---
st.header("👤 Account Dashboard")
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Account Details")
    st.write(f"**User ID:** `{current_user}`")
    
    # Calculate mock balance based on the CSV data
    balance = 12500.00 # fallback default
    if not user_history.empty and "balance_before" in user_history.columns:
         last_balance = float(user_history.iloc[0]["balance_before"])
         last_amt = float(user_history.iloc[0]["amount"])
         balance = last_balance - last_amt
         
    st.metric("Current Balance", f"${balance:,.2f}")

with col2:
    st.subheader("Recent Transactions (Last 5)")
    if not user_history.empty:
        # Display the newest 5 records
        display_df = user_history.head(5)[["timestamp", "receiver_id", "payment_type", "amount"]]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.write("No recent transactions found. Ensure transactions.csv is loaded.")

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
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
    else:
        # Compile data to send to our main.py loop
        txn_payload = {
            "user_id": current_user,
            "amount": amount,
            "payment_type": payment_type,
            "receiver_id": receiver_id,
            "receiver_country": receiver_country,
            "sender_country": "HK",
            "device_id": device_id,
            "login_attempts": 1, 
            "time_since_last_txn": 120, # Simulated typical value
            "hour": datetime.now().hour
        }

        st.info("Processing transaction through Risk Agent...")
        
        with st.spinner("Agent is extracting features and calculating risk..."):
            try:
                # Trigger manual tool execution loop
                final_analysis = run_fraud_agent_loop(txn_payload, api_key)
                
                if isinstance(final_analysis, list):
                    # Join list elements into one string, ensuring everything is a string type
                    full_text = " ".join([str(item) for item in final_analysis])
                else:
                    full_text = str(final_analysis)

                clean_text = full_text.upper().replace("*", "")

                # Dynamic UI feedback based on the recommendation rule
                if "RECOMMENDATION: APPROVE" in clean_text:
                    st.success("Transaction Approved ✅")
                elif "RECOMMENDATION: REVIEW" in clean_text:
                    st.warning("Transaction Flagged for Review ⚠️")
                elif "RECOMMENDATION: BLOCK" in clean_text:
                    st.error("Transaction Blocked 🚨")
                else:
                    # This acts as a safety net in case the LLM ignored the prompt format
                    st.info("Agent Analysis Complete (Manual Review Recommended)")
                
                # Show the final explanation directly from Gemini
                st.markdown("### 🤖 Agent Output")
                st.write(final_analysis)
                
            except Exception as e:
                st.error(f"Error executing agent loop: {e}")