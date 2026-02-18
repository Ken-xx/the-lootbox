import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIG & DATABASE ---
st.set_page_config(page_title="The Lootbox", page_icon="📦", layout="wide")

def init_db():
    conn = sqlite3.connect('savings_system.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY, 
                        access_code TEXT UNIQUE, 
                        display_name TEXT)''')
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Default keys for you and your friends
        sample_users = [('key-01', 'User Alpha'), ('key-02', 'User Bravo')]
        cursor.executemany("INSERT INTO users (access_code, display_name) VALUES (?, ?)", sample_users)
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS pockets (
                        pocket_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        user_id INTEGER, 
                        pocket_type TEXT, 
                        balance REAL DEFAULT 0.0, 
                        maturity_date DATE)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. STEALTH DARK THEME (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; }
    
    h1, h2, h3 { 
        color: #00ffcc !important; 
        text-shadow: 0 0 8px rgba(0, 255, 204, 0.4);
        font-family: 'Courier New', monospace;
    }

    /* Metric Card Styling */
    [data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #00ffcc;
        border-radius: 12px;
        padding: 15px;
    }

    /* Primary Buttons (Green) */
    .stButton>button[kind="primary"] {
        background-color: #00ffcc !important;
        color: #0b0e14 !important;
        font-weight: bold;
        border: none;
    }

    /* Disabled Buttons (Grey-out Logic) */
    button:disabled {
        background-color: #1f2329 !important;
        color: #5d646e !important;
        border: 1px solid #2d333b !important;
        text-shadow: none !important;
        box-shadow: none !important;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        color: white;
        border-radius: 4px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00ffcc !important;
        color: #0b0e14 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION GATE ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        st.markdown("<h1 style='text-align: center;'>📦 The Lootbox</h1>", unsafe_allow_html=True)
        key = st.text_input("Vault Key", placeholder="Enter Access Key...", label_visibility="collapsed").strip()
        if st.button("Unlock Vault", use_container_width=True, type="primary"):
            conn = sqlite3.connect('savings_system.db')
            user = pd.read_sql_query("SELECT * FROM users WHERE access_code = ?", conn, params=(key,))
            conn.close()
            if not user.empty:
                st.session_state.auth = True
                st.session_state.user = user.iloc[0]
                st.rerun()
            else:
                st.error("Access Key Denied.")
    st.stop()

# --- 4. DASHBOARD LAYOUT ---
user = st.session_state.user

# Sidebar Identity
with st.sidebar:
    st.markdown(f"## 👤 {user['display_name']}")
    st.caption("Status: 🟢 Secure")
    st.divider()
    if st.button("🔒 Close Vault", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# Hero Metrics
st.title("📦 Your Vault")
col1, col2, col3 = st.columns(3)

conn = sqlite3.connect('savings_system.db')
res = pd.read_sql_query("SELECT SUM(balance) as total FROM pockets WHERE user_id = ?", conn, params=(int(user['user_id']),))
count_res = pd.read_sql_query("SELECT COUNT(*) as count FROM pockets WHERE user_id = ?", conn, params=(int(user['user_id']),))
conn.close()

with col1:
    st.metric("Total Balance", f"₦{res['total'].iloc[0] or 0.0:,.2f}")
with col2:
    st.metric("Active Locks", f"{count_res['count'].iloc[0]}")
with col3:
    st.metric("Trust Score", "100%")

st.divider()

# --- 5. INTERACTIVE TABS ---
tab1, tab2, tab3 = st.tabs(["➕ Create Lock", "📜 Vault Ledger", "🛡️ Security Info"])

with tab1:
    with st.container(border=True):
        st.subheader("Initialize a New Lock")
        plan = st.selectbox("Select Duration:", ["Weekly (7 Days)", "Monthly (30 Days)", "Long-term (90 Days)"], key="plan_final")
        goal_amt = st.number_input("Target Amount (₦)", min_value=1000, step=500, key="goal_final")
        
        days = 7 if "Weekly" in plan else (30 if "Monthly" in plan else 90)
        unlock_date = datetime.now() + timedelta(days=days)
        
        if "Weekly" in plan:
            st.progress(25, text="Light Lock 🟢")
        elif "Monthly" in plan:
            st.progress(60, text="Medium Lock 🟡")
        else:
            st.progress(100, text="Maximum Security Lock 🔴")

        st.info(f"Locked until: **{unlock_date.strftime('%d %b %Y')}**")
        
        if st.button("🔐 Finalize and Lock", use_container_width=True, type="primary"):
            conn = sqlite3.connect('savings_system.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO pockets (user_id, pocket_type, balance, maturity_date) VALUES (?, ?, ?, ?)', 
                           (int(user['user_id']), plan, 0.0, unlock_date.date()))
            conn.commit()
            conn.close()
            st.success("Lootbox initialized!")
            st.rerun()

with tab2:
    st.subheader("Vault History")
    conn = sqlite3.connect('savings_system.db')
    df = pd.read_sql_query("SELECT * FROM pockets WHERE user_id = ?", conn, params=(int(user['user_id']),))
    conn.close()
    
    if not df.empty:
        for index, row in df.iterrows():
            with st.container(border=True):
                maturity_dt = datetime.strptime(row['maturity_date'], '%Y-%m-%d').date()
                is_unlocked = datetime.now().date() >= maturity_dt
                
                c_info, c_bal, c_btn = st.columns([2, 1, 1.2])
                
                with c_info:
                    st.markdown(f"**{row['pocket_type']}**")
                    if is_unlocked:
                        st.markdown("<span style='color:#00ffcc;'>🔓 READY</span>", unsafe_allow_html=True)
                    else:
                        st.caption(f"Unlocks: {maturity_dt.strftime('%d %b %Y')}")
                
                with c_bal:
                    st.write("Value")
                    st.markdown(f"**₦{row['balance']:,.2f}**")
                
                with c_btn:
                    if not is_unlocked:
                        # Greyed out Withdraw
                        st.button("Withdraw", key=f"lock_{row['pocket_id']}", disabled=True, use_container_width=True)
                        # Active Deposit
                        if st.button("➕ Deposit", key=f"dep_btn_{row['pocket_id']}", use_container_width=True, type="primary"):
                            st.session_state.target_pocket = row['pocket_id']
                            st.session_state.show_deposit = True
                    else:
                        # Green Withdraw
                        if st.button("Withdraw", key=f"claim_{row['pocket_id']}", type="primary", use_container_width=True):
                            conn = sqlite3.connect('savings_system.db')
                            cursor = conn.cursor()
                            cursor.execute("UPDATE pockets SET balance = 0 WHERE pocket_id = ?", (row['pocket_id'],))
                            conn.commit()
                            conn.close()
                            st.success("Loot Released!")
                            st.rerun()

        # Deposit Form
        if st.session_state.get('show_deposit'):
            with st.form("deposit_action"):
                st.write(f"Feeding Vault ID: {st.session_state.target_pocket}")
                dep_amt = st.number_input("Amount (₦)", min_value=500, step=500)
                if st.form_submit_button("Confirm Transfer", use_container_width=True):
                    conn = sqlite3.connect('savings_system.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE pockets SET balance = balance + ? WHERE pocket_id = ?", (dep_amt, st.session_state.target_pocket))
                    conn.commit()
                    conn.close()
                    st.session_state.show_deposit = False
                    st.rerun()
    else:
        st.info("Vault is currently empty.")
    
with tab3:
    st.markdown("### 🛡️ Security Protocol\n- **Immutable:** No early release.\n- **Encrypted:** Key-locked ledger.")





