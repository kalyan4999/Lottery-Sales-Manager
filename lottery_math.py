import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('lottery_pro.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventory 
                 (game_name TEXT PRIMARY KEY, last_end_no INTEGER, price REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales_history 
                 (date TEXT, game_name TEXT, sold INTEGER, revenue REAL)''')
    conn.commit()
    return conn

def get_last_number(game_name):
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT last_end_no, price FROM inventory WHERE game_name = ?", (game_name,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (0, 0.0)

# --- STREAMLIT UI ---
st.set_page_config(page_title="Lottery Store Manager", layout="wide")

st.title("🎰 Lottery Store Sales Manager")
st.markdown("Automate your end-of-day math and reporting.")

# Sidebar for adding new games to your system
with st.sidebar:
    st.header("Add New Game to System")
    new_game = st.text_input("Game Name")
    new_price = st.number_input("Ticket Price ($)", min_value=1.0, step=1.0)
    new_start = st.number_input("Starting Ticket #", min_value=0)
    if st.button("Add to Inventory"):
        conn = init_db()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO inventory VALUES (?, ?, ?)", (new_game, new_start, new_price))
        conn.commit()
        st.success(f"Added {new_game}!")

# Main Area: Daily Entry
st.header("📝 Daily Sales Entry")
conn = init_db()
inventory_df = pd.read_sql_query("SELECT * FROM inventory", conn)

if not inventory_df.empty:
    cols = st.columns([3, 2, 2, 2])
    cols[0].write("**Game Name**")
    cols[1].write("**Yesterday's End (Start)**")
    cols[2].write("**Today's End**")
    cols[3].write("**Revenue**")

    total_daily_rev = 0
    payout_data = []

    for index, row in inventory_df.iterrows():
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        c1.write(row['game_name'])
        c2.write(row['last_end_no'])
        
        # Input for today's ending number
        end_no = c3.number_input(f"End # for {row['game_name']}", min_value=int(row['last_end_no']), key=row['game_name'])
        
        # Real-time Math
        sold = end_no - row['last_end_no']
        rev = sold * row['price']
        total_daily_rev += rev
        c4.write(f"${rev:.2f}")
        
        payout_data.append((row['game_name'], end_no, sold, rev))

    st.divider()
    
    # Summary Section
    col_sum1, col_sum2 = st.columns(2)
    with col_sum1:
        st.metric("Total Ticket Sales", f"${total_daily_rev:.2f}")
        payouts = st.number_input("Total Winning Payouts Today ($)", min_value=0.0)
        st.metric("Net Cash Deposit", f"${total_daily_rev - payouts:.2f}")

    if st.button("💾 Save & Close Day"):
        today_str = datetime.now().strftime("%Y-%m-%d")
        c = conn.cursor()
        for name, end, sold, rev in payout_data:
            # Update Inventory Memory
            c.execute("UPDATE inventory SET last_end_no = ? WHERE game_name = ?", (end, name))
            # Record History
            c.execute("INSERT INTO sales_history VALUES (?, ?, ?, ?)", (today_str, name, sold, rev))
        conn.commit()
        st.balloons()
        st.success("Day saved! Tomorrow's starting numbers have been updated.")
else:
    st.info("Start by adding games in the sidebar on the left.")

conn.close()