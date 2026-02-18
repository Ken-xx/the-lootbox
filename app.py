import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIG & CONNECTION ---
st.set_page_config(page_title="The Lootbox", page_icon="📦", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_sheet(name):
    df = conn.read(worksheet=name, ttl=0)
    df.columns = [c.lower().strip() for c in df.columns]
    return df

# --- 2. CSS GLOW-UP ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14 !important; }
    h1, h2, h3 { color: #00ffcc !important; text-shadow: 0 0 10px rgba(0, 255, 204, 0.4); }
    [data-testid="stMetric"] { background-color: #161b22 !important; border: 1px solid #00ffcc !important; border-radius: 12px; }
    .stButton>button[kind="primary"] { background-color: #00ffcc !important; color: #0b0e14 !important; font-weight: bold; }
    button:disabled { background-color: #1f2329 !important; color: #5d646e !important; border: 1px solid #2d333b !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN GATE ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        st.title("📦 The Lootbox")
        key_input = st.text_input("Vault Key", type="password")
        if st.button("Unlock Vault", use_container_width=True, type="primary"):
            users = load_sheet("users")
            user_match = users[users['access_code'].astype(str) == key_input]
            if not user_match.empty:
                st.session_state.auth = True
                st.session_state.user = user_match.iloc[0].to_dict()
                st.rerun()
            else: st.error("Access Key Denied.")
    st.stop()

# --- 4. DATA REFRESH ---
user = st.session_state.user
pockets_df = load_sheet("pockets")
my_locks = pockets_df[pockets_df['user_id'].astype(str) == str(user['user_id'])]

# --- 5. DASHBOARD ---
with st.sidebar:
    st.markdown(f"## 👤 {user['display_name']}")
    if st.button("🔒 Close Vault", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

st.title(f"📦 {user['display_name']}'s Vault")
c1, c2 = st.columns(2)
c1.metric("Total Saved", f"₦{my_locks['balance'].sum():,.2f}")
c2.metric("Active Locks", len(my_locks))

tab1, tab2, tab3 = st.tabs(["➕ Create Lock", "📜 Vault Ledger", "🛡️ Security"])

with tab1:
    with st.form("new_lock"):
        st.subheader("Initialize New Physics-Lock")
        plan = st.selectbox("Duration", ["Weekly (7 Days)", "Monthly (30 Days)", "Quarterly (90 Days)"])
        goal = st.number_input("Target Goal (₦)", min_value=1000, step=500)
        
        if st.form_submit_button("Confirm & Seal Vault", use_container_width=True, type="primary"):
            days = 7 if "Weekly" in plan else (30 if "Monthly" in plan else 90)
            m_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Create new entry
            new_row = pd.DataFrame([{
                "pocket_id": len(pockets_df) + 1,
                "user_id": user['user_id'],
                "pocket_type": plan,
                "balance": 0.0,
                "maturity_date": m_date
            }])
            updated = pd.concat([pockets_df, new_row], ignore_index=True)
            conn.update(worksheet="pockets", data=updated)
            
            st.toast(f"Savings velocity needed: ₦{goal/days:,.2f}/day", icon="🚀")
            st.success("Lootbox Sealed!")
            st.rerun()

with tab2:
    if my_locks.empty:
        st.info("No active locks found in this vault.")
    else:
        for _, row in my_locks.iterrows():
            with st.container(border=True):
                # Date and Countdown Logic
                maturity = datetime.strptime(str(row['maturity_date']), '%Y-%m-%d').date()
                days_left = (maturity - datetime.now().date()).days
                unlocked = days_left <= 0
                
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.write(f"**{row['pocket_type']}**")
                    st.markdown(f"### ₦{row['balance']:,.2f}")
                    if not unlocked:
                        st.caption(f"⏳ {days_left} days until unlock ({maturity.strftime('%d %b')})")
                    else:
                        st.markdown("<span style='color:#00ffcc;'>🔓 READY FOR WITHDRAWAL</span>", unsafe_allow_html=True)
                
                with col_b:
                    if not unlocked:
                        st.button("Withdraw", key=f"l_{row['pocket_id']}", disabled=True, use_container_width=True)
                        if st.button("➕ Deposit", key=f"d_{row['pocket_id']}", type="primary", use_container_width=True):
                            st.info("Directing to Paystack...")
                    else:
                        if st.button("Claim Loot", key=f"w_{row['pocket_id']}", type="primary", use_container_width=True):
                            st.balloons()
                            # (Reset logic would go here later)

with tab3:
    st.markdown("### 🛡️ Protocol Info\n- **Vault ID:** " + str(user['user_id']) + "\n- **Security:** AES-Standard Ledger\n- **Constraint:** Zero early-access policy.")

# --- 6. ADMIN VIEW (HIDDEN) ---
if str(user['user_id']) == "1":
    st.divider()
    with st.expander("🛠️ ADMIN COMMAND CENTER"):
        st.write("All Active System Pockets")
        st.dataframe(pockets_df, use_container_width=True)
        st.metric("Total Liquidity", f"₦{pockets_df['balance'].sum():,.2f}")




