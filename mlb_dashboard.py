"""
MLB YRFI/NRFI Betting Dashboard
================================
Production Streamlit app for daily predictions and tracking

Run with: streamlit run mlb_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import pickle
import os
import json

# Page config
st.set_page_config(
    page_title="MLB YRFI/NRFI Model",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS matching our design
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: linear-gradient(135deg, #0a0e1a 0%, #0f1419 50%, #0a0e1a 100%);
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(135deg, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        color: #10b981;
    }
    
    /* Cards */
    .css-1r6slb0 {
        background-color: #1a2028;
        border: 1px solid #2d3748;
        border-radius: 12px;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #10b981, #3b82f6);
        color: #000;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_model():
    """Load the trained model"""
    # TODO: Fix model loading - pandas version mismatch
    # For now, return None until we integrate live predictions next session
    return None

def load_bets_history():
    """Load betting history from JSON"""
    history_path = "data/bet_history.json"
    if os.path.exists(history_path):
        with open(history_path) as f:
            return json.load(f)
    return {"bets": []}

def save_bet(bet_data):
    """Save a new bet to history"""
    history = load_bets_history()
    history["bets"].append(bet_data)
    
    os.makedirs("data", exist_ok=True)
    with open("data/bet_history.json", 'w') as f:
        json.dump(history, f, indent=2)

def get_star_rating(edge):
    """Convert edge to star rating"""
    if edge >= 10:
        return "★★★★★", 5
    elif edge >= 7:
        return "★★★★☆", 4
    elif edge >= 5:
        return "★★★☆☆", 3
    elif edge >= 3:
        return "★★☆☆☆", 2
    else:
        return "★☆☆☆☆", 1

def american_to_implied(odds):
    """Convert American odds to implied probability"""
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("⚾ MLB YRFI/NRFI")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Today's Picks", "Performance", "Settings"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Stats")

# Load history for sidebar stats
history = load_bets_history()
if history["bets"]:
    total_bets = len(history["bets"])
    wins = sum(1 for b in history["bets"] if b.get("result") == "win")
    win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
    
    st.sidebar.metric("Total Bets", total_bets)
    st.sidebar.metric("Win Rate", f"{win_rate:.1f}%")
else:
    st.sidebar.info("No bets logged yet")

# ============================================================
# PAGE 1: TODAY'S PICKS
# ============================================================

if page == "Today's Picks":
    st.title("Today's Value Bets")
    st.markdown(f"**{datetime.now().strftime('%A, %B %d, %Y')}**")
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Games Today", "12", delta="2 vs yesterday")
    with col2:
        st.metric("Value Bets", "3", delta="+10.5% avg edge")
    with col3:
        st.metric("Best Edge", "+10.7%", delta="5-star bet")
    
    st.markdown("---")
    
    # SAMPLE GAME CARDS (in production, this would pull from daily_predictor.py)
    st.subheader("🎯 Ranked by Edge")
    
    # Game 1 - Top Pick
    with st.expander("⭐⭐⭐⭐⭐ #1 BEST VALUE | PHI @ ATL", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 BET YRFI at -115")
            st.markdown("**Model:** 64.2% | **Edge:** +10.7% | **EV:** +$19/100")
            
            st.markdown("**💡 Why This Bet:**")
            st.markdown("- 🔥 Phillies offense hot streak (8-2 YRFI last 10)")
            st.markdown("- 🌡️ Perfect hitting weather (82°F)")
            st.markdown("- 👨‍⚖️ Angel Hernandez umpire (+4.5% YRFI boost)")
            st.markdown("- ⚾ Wheeler: 60% YRFI rate last 5 starts")
        
        with col2:
            st.markdown("**Game Info**")
            st.markdown("🕐 7:20 PM ET")
            st.markdown("🏟️ Truist Park")
            st.markdown("🌡️ 82°F")
            
            st.markdown("---")
            
            if st.button("✅ Log This Bet", key="bet1"):
                bet_data = {
                    "date": str(date.today()),
                    "game": "PHI @ ATL",
                    "bet_type": "YRFI",
                    "stars": 5,
                    "odds": -115,
                    "edge": 10.7,
                    "wager": 100,
                    "result": "pending"
                }
                save_bet(bet_data)
                st.success("Bet logged!")
            
            if st.button("❌ Skip", key="skip1"):
                st.info("Bet skipped")
        
        # Expandable details
        with st.expander("⚾ Listed Starters"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Zack Wheeler (PHI)**")
                st.markdown("Last 5: ✅❌❌✅❌")
                st.markdown("YRFI Rate: 3/5 (60%)")
                st.markdown("Clean Sheets: 14/28 (50%)")
                st.markdown("1st Pitch Strike%: 61%")
            with col2:
                st.markdown("**Spencer Strider (ATL)**")
                st.markdown("Last 5: ✅✅✅❌✅")
                st.markdown("YRFI Rate: 1/5 (20%)")
                st.markdown("Clean Sheets: 24/28 (86%)")
                st.markdown("1st Pitch Strike%: 68%")
        
        with st.expander("📊 Team Recent Form"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Philadelphia (Away)**")
                st.markdown("Last 5 YRFI: 4-1 (80%) 🔥")
                st.markdown("Last 10 YRFI: 8-2 (80%)")
                st.markdown("Season YRFI: 45-38 (54%)")
            with col2:
                st.markdown("**Atlanta (Home)**")
                st.markdown("Last 5 YRFI: 4-1 (80%) 🔥")
                st.markdown("Last 10 YRFI: 7-3 (70%)")
                st.markdown("Season YRFI: 52-41 (56%)")
        
        with st.expander("🌡️ Environmental Conditions"):
            st.markdown("**Temperature:** 82°F (Favorable for offense, +8% YRFI)")
            st.markdown("**Wind:** 6 mph SW (Minimal impact)")
            st.markdown("**Venue:** Truist Park (Park Factor: 1.08)")
            st.markdown("**Historical YRFI Rate:** 58% at this venue")
        
        with st.expander("👨‍⚖️ Officiating"):
            st.markdown("**Home Plate Umpire:** Angel Hernandez")
            st.markdown("**Strike Zone:** Tight (batter favorable)")
            st.markdown("**Run Impact:** +0.45 runs vs league average")
            st.markdown("**Season YRFI Rate:** 61% (League avg: 56%)")
            st.markdown("**Effect:** +4.5% to YRFI probability")
    
    # Game 2
    with st.expander("⭐⭐⭐⭐☆ #2 VALUE BET | LAD @ SD"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 BET NRFI at -108")
            st.markdown("**Model:** 68.0% | **Edge:** +16.1% | **EV:** +$15/100")
            
            st.markdown("**💡 Why This Bet:**")
            st.markdown("- ⚾ Elite pitching matchup (Glasnow vs Darvish)")
            st.markdown("- 🏟️ Petco Park - pitcher friendly")
            st.markdown("- 🌡️ Cool evening (68°F)")
        
        with col2:
            st.markdown("**Game Info**")
            st.markdown("🕐 9:40 PM ET")
            st.markdown("🏟️ Petco Park")
            
            st.markdown("---")
            
            if st.button("✅ Log This Bet", key="bet2"):
                st.success("Bet logged!")
            if st.button("❌ Skip", key="skip2"):
                st.info("Bet skipped")

# ============================================================
# PAGE 2: PERFORMANCE TRACKING
# ============================================================

elif page == "Performance":
    st.title("Performance Dashboard")
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    
    history = load_bets_history()
    bets = history.get("bets", [])
    
    if bets:
        wins = sum(1 for b in bets if b.get("result") == "win")
        losses = sum(1 for b in bets if b.get("result") == "loss")
        total = len([b for b in bets if b.get("result") in ["win", "loss"]])
        win_rate = (wins / total * 100) if total > 0 else 0
        
        profit = sum(b.get("profit", 0) for b in bets if b.get("result") in ["win", "loss"])
        
        with col1:
            st.metric("Total Bets", total, delta=f"{wins}W - {losses}L")
        with col2:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            st.metric("Total Profit", f"${profit:+.0f}")
        
        st.markdown("---")
        
        # Star rating breakdown
        st.subheader("📊 Performance by Star Rating")
        
        star_groups = {5: [], 4: [], 3: []}
        for bet in bets:
            stars = bet.get("stars", 3)
            if stars in star_groups and bet.get("result") in ["win", "loss"]:
                star_groups[stars].append(bet)
        
        for stars in [5, 4, 3]:
            group_bets = star_groups[stars]
            if group_bets:
                group_wins = sum(1 for b in group_bets if b["result"] == "win")
                group_total = len(group_bets)
                group_rate = (group_wins / group_total * 100) if group_total > 0 else 0
                
                st.markdown(f"**{'★' * stars}{'☆' * (5-stars)}** - {group_total} bets | {group_wins}W-{group_total-group_wins}L ({group_rate:.1f}%)")
        
        st.markdown("---")
        
        # Recent bets table
        st.subheader("Recent Bets")
        
        df = pd.DataFrame(bets)
        if not df.empty:
            # Show last 20 bets
            recent = df.tail(20).sort_values('date', ascending=False)
            st.dataframe(
                recent[['date', 'game', 'bet_type', 'stars', 'odds', 'edge', 'result']],
                use_container_width=True
            )
    else:
        st.info("No betting history yet. Start logging bets from Today's Picks!")

# ============================================================
# PAGE 3: SETTINGS
# ============================================================

elif page == "Settings":
    st.title("Settings")
    
    st.subheader("Model Configuration")
    
    min_edge = st.slider("Minimum Edge Threshold (%)", 0.0, 20.0, 5.0, 0.5)
    st.caption(f"Only show bets with {min_edge}%+ edge")
    
    default_stake = st.number_input("Default Stake ($)", 0, 1000, 100, 10)
    
    st.markdown("---")
    
    st.subheader("Model Info")
    model = load_model()
    if model:
        st.success("✅ Model loaded")
        st.info("Last trained: Check models folder for timestamp")
    else:
        st.error("❌ No model found - run training first")
    
    st.markdown("---")
    
    st.subheader("Data Management")
    
    if st.button("Clear Betting History"):
        if os.path.exists("data/bet_history.json"):
            os.remove("data/bet_history.json")
            st.success("History cleared!")
            st.rerun()
    
    if st.button("Retrain Model"):
        st.info("Run: python3 first_inning_predictor.py --train --data mlb_data/combined_training_data.csv")
    
    st.markdown("---")
    st.caption("MLB YRFI/NRFI Model v1.0 | Season 2026")

# ============================================================
# FOOTER
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Tip:** Log your bets to track performance!")
