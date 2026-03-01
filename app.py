import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3

# --- 1. STYLE & THEME ---
st.set_page_config(page_title="369 ELITE V26", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Orbitron'; color: #00ffcc; text-align: center; text-shadow: 0 0 15px #00ffcc; padding: 15px; }
    div[data-testid="stMetric"] { background: rgba(22, 27, 34, 0.6) !important; border: 1px solid #30363d !important; border-radius: 12px !important; }
    
    /* TradeZella Calendar Styling */
    .zella-day { border: 1px solid #262626; min-height: 120px; padding: 8px; background: #0d1117; border-radius: 4px; }
    .zella-header { color: #8b949e; font-size: 0.75rem; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #21262d; }
    .zella-trade { font-size: 0.7rem; padding: 4px; border-radius: 3px; margin-bottom: 4px; font-weight: bold; }
    .zella-win { background: rgba(45, 101, 74, 0.4); border-left: 3px solid #34d399; color: #34d399; }
    .zella-loss { background: rgba(127, 45, 45, 0.4); border-left: 3px solid #ef4444; color: #ef4444; }
    .zella-be { background: rgba(120, 120, 45, 0.4); border-left: 3px solid #fbbf24; color: #fbbf24; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
conn = sqlite3.connect('elite_final_v26.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pair TEXT, type TEXT, 
              outcome TEXT, pnl REAL, setup TEXT, mindset TEXT, rr REAL, balance REAL)''')
conn.commit()

# --- 3. DATA LOADING ---
df = pd.read_sql_query("SELECT * FROM trades", conn)
now = datetime.now()
if not df.empty:
    df['date_dt'] = pd.to_datetime(df['date'])
    m_df = df[(df['date_dt'].dt.month == now.month) & (df['date_dt'].dt.year == now.year)]

# --- 4. HEADER ---
st.markdown('<h1 class="main-title">369 TRACKER PRO V26</h1>', unsafe_allow_html=True)
tabs = st.tabs(["🎮 TERMINAL", "📆 DAILY LOG (Zella)", "📊 PERFORMANCE", "🧬 DISCIPLINE & CONSISTENCY", "📜 JOURNAL", "📓 NOTION"])

# --- TAB 1: TERMINAL ---
with tabs[0]:
    col1, col2 = st.columns([1.2, 2])
    with col1:
        with st.form("entry_v26", clear_on_submit=True):
            balance = st.number_input("Account Amount ($)", value=1000.0, format="%.2f")
            d_in = st.date_input("Date", datetime.now())
            asset = st.text_input("Asset", "NAS100").upper()
            side = st.selectbox("Action", ["LONG", "SHORT"])
            res = st.selectbox("Outcome", ["WIN", "LOSS", "BE"])
            p_val = st.number_input("P&L ($)", value=0.0, format="%.2f")
            r_val = st.number_input("R:R Ratio", value=1.0, format="%.2f")
            setups = list(df['setup'].unique()) if not df.empty else []
            setup = st.text_input("New Setup").upper() if st.checkbox("New?") or not setups else st.selectbox("Select Setup", setups)
            mind = st.select_slider("Mindset", ["Focused", "Bored", "Impulsive", "Revenge"])
            if st.form_submit_button("LOCK TRADE"):
                c.execute("INSERT INTO trades (date, pair, type, outcome, pnl, setup, mindset, rr, balance) VALUES (?,?,?,?,?,?,?,?,?)",
                          (str(d_in), asset, side, res, p_val, setup, mind, r_val, balance))
                conn.commit()
                st.rerun()
    with col2:
        if not df.empty:
            total_pnl = df['pnl'].sum()
            st.metric("CURRENT EQUITY", f"${(df['balance'].iloc[-1] + total_pnl):.2f}")
            df['eq'] = df['balance'].iloc[0] + df['pnl'].cumsum()
            st.plotly_chart(px.line(df, x='date_dt', y='eq', template="plotly_dark").update_traces(line_color='#00ffcc'), use_container_width=True)

# --- TAB 2: DAILY LOG (Zella Grid) ---
with tabs[1]:
    if not df.empty:
        c_stats, c_zella = st.columns([1, 4])
        with c_stats:
            st.markdown(f"### 🗓️ {now.strftime('%B %Y')}")
            if not m_df.empty:
                m_wr = (len(m_df[m_df['outcome']=='WIN']) / len(m_df)) * 100
                st.metric("Monthly Win Rate", f"{m_wr:.1f}%")
                st.metric("Monthly P&L", f"${m_df['pnl'].sum():.2f}")
        
        with c_zella:
            days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            cols = st.columns(7)
            start_of_week = now - timedelta(days=now.weekday())
            for i, col in enumerate(cols):
                d = start_of_week + timedelta(days=i)
                d_str = d.strftime('%Y-%m-%d')
                day_trades = df[df['date'] == d_str]
                with col:
                    st.markdown(f'<div class="zella-day"><div class="zella-header">{days_of_week[i]} {d.day}</div>', unsafe_allow_html=True)
                    for _, row in day_trades.iterrows():
                        style = "zella-win" if row.outcome == "WIN" else "zella-loss" if row.outcome == "LOSS" else "zella-be"
                        st.markdown(f'<div class="zella-trade {style}">{row.pair}<br>${row.pnl:.2f}<br>{row.rr:.2f}RR</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: PERFORMANCE ---
with tabs[2]:
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.pie(df, names='outcome', hole=0.5, color='outcome', color_discrete_map={'WIN':'#00ffcc','LOSS':'#ff4b4b','BE':'#ffa500'}, title="Success Distribution"), use_container_width=True)
        c2.plotly_chart(px.bar(df, x='setup', y='pnl', color='outcome', template="plotly_dark", title="Profit by Strategy"), use_container_width=True)

# --- TAB 4: DISCIPLINE, CONSISTENCY & RISK (THE CORE) ---
with tabs[3]:
    if not df.empty:
        st.subheader("🧬 Discipline & Performance Analyser")
        
        col_risk, col_mind = st.columns(2)
        
        with col_risk:
            # 1. Risk Management Tracker (RR vs PnL)
            st.markdown("### ⚖️ Risk Management Tracker")
            fig_risk = px.scatter(df, x='rr', y='pnl', size=df['pnl'].abs().clip(lower=1), 
                                 color='outcome', color_discrete_map={'WIN':'#00ffcc','LOSS':'#ff4b4b','BE':'#ffa500'},
                                 title="RR Expectancy vs Realized P&L", template="plotly_dark")
            st.plotly_chart(fig_risk, use_container_width=True)
            
        with col_mind:
            # 2. Mindset Tracker
            st.markdown("### 🧠 Mindset Tracker")
            mindset_stats = df.groupby('mindset')['pnl'].sum().reset_index()
            fig_mind = px.bar(mindset_stats, x='mindset', y='pnl', color='pnl', 
                             color_continuous_scale=['#ff4b4b', '#00ffcc'], title="Profit by Mental State", template="plotly_dark")
            st.plotly_chart(fig_mind, use_container_width=True)
            
        st.write("---")
        
        # 3. Consistency Tracker (Score)
        st.markdown("### 🏆 Consistency Tracker")
        avg_win = df[df['pnl'] > 0]['pnl'].mean() if not df[df['pnl'] > 0].empty else 1
        avg_loss = abs(df[df['pnl'] < 0]['pnl'].mean()) if not df[df['pnl'] < 0].empty else 1
        win_rate = len(df[df['outcome']=='WIN']) / len(df)
        consistency_score = (avg_win / avg_loss) * win_rate * 10
        
        c_score, c_info = st.columns([1, 2])
        c_score.metric("Consistency Score", f"{consistency_score:.1f} / 10")
        c_info.progress(min(consistency_score/10, 1.0))
        st.info("Your score is calculated based on: Win Rate, Profit Factor, and R:R Stability.")

# --- TAB 5: JOURNAL ---
with tabs[4]:
    if not df.empty:
        st.dataframe(df.sort_values('date', ascending=False).style.format({"pnl": "{:.2f}", "rr": "{:.2f}", "balance": "{:.2f}"}), use_container_width=True)

# --- TAB 6: NOTION ---
with tabs[5]:
    st.markdown("### 📓 Notion Space")
    st.write("Keep following the 369 rules. Consistency is the only way to the top.")
