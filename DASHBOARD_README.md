# MLB YRFI/NRFI Betting Dashboard

Production-ready Streamlit web app for daily MLB first inning predictions.

## 🚀 Quick Start

### 1. Install Streamlit
```bash
pip install streamlit --break-system-packages
```

### 2. Run the Dashboard
```bash
cd Desktop/MLB_Model
streamlit run mlb_dashboard.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📱 Features

### Page 1: Today's Picks
- View all value bets ranked by edge
- See detailed game analysis
- Star ratings (5★ = best, 3★ = marginal)
- One-click bet logging
- Expandable pitcher stats, team form, weather

### Page 2: Performance
- Overall win rate and profit
- Performance by star rating
- Recent bets table
- Track your success over time

### Page 3: Settings
- Adjust minimum edge threshold
- Set default stake size
- Model information
- Clear history / retrain model

---

## 🔧 Next Steps (TODO for Next Session)

### CRITICAL FIX:
- [ ] Fix backtest script (feature mismatch issue with park names)
- [ ] Run full 2024 backtest to get real performance numbers
- [ ] Calibrate star ratings based on actual win rates

### Dashboard Enhancements:
- [ ] Connect to daily_predictor.py for live predictions
- [ ] Add DraftKings odds scraper integration
- [ ] Add charts/graphs to Performance page
- [ ] Implement calendar heatmap
- [ ] Add push notifications (Pushover)

### Deployment:
- [ ] Deploy to Streamlit Cloud (free hosting)
- [ ] Set up daily automation (run predictions every morning)
- [ ] Configure data persistence (PostgreSQL or SQLite)

---

## 📂 Project Structure

```
MLB_Model/
├── mlb_dashboard.py              # Streamlit app (main file)
├── first_inning_predictor.py     # Model training
├── daily_predictor.py            # Daily predictions
├── backtest_model.py             # Backtesting (needs fix)
├── rotowire_scraper.py           # Lineup data
├── umpire_scraper.py             # Umpire data
├── draftkings_odds_scraper.py    # Odds data
├── models/                       # Trained models
│   └── first_inning_model_latest.pkl
├── mlb_data/                     # Historical data
│   ├── first_inning_data_2022.csv
│   ├── first_inning_data_2023.csv
│   └── first_inning_data_2024.csv
└── data/                         # App data
    └── bet_history.json          # Logged bets
```

---

## 🎯 Current Status

✅ **COMPLETED:**
- Data collection (7,275 games from 2022-2024)
- Model training (56% accuracy on test set)
- All data scrapers built (RotoWire, Umpires, DraftKings)
- Dashboard UI design (hybrid professional theme)
- Basic Streamlit app structure
- Bet logging functionality

⚠️ **IN PROGRESS:**
- Backtest script (feature mismatch - fix next session)
- Live predictions integration
- Charts and visualizations

📋 **NEXT SESSION:**
- Fix backtest and get real 2024 results
- Integrate daily predictions into dashboard
- Add performance charts
- Deploy to Streamlit Cloud

---

## 💡 Usage Tips

### Running Daily Predictions:
```bash
# Once backtest is fixed, you'll run:
python3 daily_predictor.py --date 2026-04-15

# This creates predictions which the dashboard will display
```

### Logging Bets:
1. Open dashboard
2. Go to "Today's Picks"
3. Click "Log This Bet" on any game
4. After the game, update result in bet_history.json
5. Dashboard auto-updates stats

### Deploying Online:
```bash
# Push to GitHub
# Connect Streamlit Cloud to your repo
# Auto-deploys on every commit
# Free tier: https://streamlit.io/cloud
```

---

## 🔐 Security Notes

- Never commit API keys or credentials
- Use environment variables for sensitive data
- Keep bet_history.json private (contains your betting data)

---

## 📞 Support

Check the project README files:
- QUICK_START_GUIDE.py
- COMPLETE_WORKFLOW_GUIDE.py
- BACKTEST_GUIDE.py

---

**Built with:** Python 3.14, Streamlit, Pandas, Scikit-learn
**Season:** 2026
**Model Version:** 1.0
