# MLB First Inning Run Prediction Model

Complete data collection and analysis system for predicting whether the first inning of an MLB game will have a run scored (yes/no).

## 🎯 What This Does

This system helps you build a predictive model for MLB first inning scoring by:
- Collecting historical game data
- Scraping advanced pitch-level statistics
- Analyzing patterns and trends
- (Coming soon) Generating daily predictions

## 📦 What's Included

### Core Scripts

1. **mlb_first_inning_data_collector.py**
   - Collects historical game data from MLB Stats API
   - Gets first inning scoring, weather, pitchers, etc.
   - Saves to CSV for analysis

2. **baseball_savant_scraper.py**
   - Scrapes Baseball Savant for pitch-level data
   - Pitcher arsenal, effectiveness, splits
   - Batter performance vs pitch types
   - Full matchup analysis

3. **mlb_first_inning_analyzer.py**
   - Analyzes collected data
   - Finds patterns and correlations
   - Temperature effects, park factors, team tendencies

4. **daily_scraper.py**
   - Automated daily data collection
   - Can be scheduled to run automatically
   - Keeps your database up to date

### User Interface

5. **mlb_scraper_dashboard.html**
   - Easy-to-use web interface
   - Click buttons to generate commands
   - No need to type commands manually!

6. **QUICK_START_GUIDE.py**
   - Step-by-step instructions
   - Example workflows
   - Troubleshooting tips

## 🚀 Quick Start (5 Minutes)

### 1. Install Python
- Download from [python.org](https://python.org/downloads)
- Version 3.8 or newer
- Make sure to check "Add to PATH" during installation

### 2. Install Required Libraries
Open your terminal/command prompt and run:
```bash
pip install requests pandas matplotlib seaborn beautifulsoup4
```

### 3. Test It Out
Run this command to collect 10 sample games:
```bash
python mlb_first_inning_data_collector.py --season 2024 --team 144 --max-games 10
```

This will:
- Create a `mlb_data` folder
- Download 10 Braves games from 2024
- Save data to CSV
- Show you summary statistics

### 4. Analyze the Data
```bash
python mlb_first_inning_analyzer.py --data mlb_data/first_inning_data_2024.csv
```

You'll see:
- First inning scoring rates
- Temperature correlations
- Park factors
- Team tendencies

## 💻 Using the Dashboard (Easiest Way!)

1. Open `mlb_scraper_dashboard.html` in your web browser
2. Click the buttons to generate commands
3. Copy the commands and run them in your terminal

**No typing required!**

## 📊 What Data Gets Collected

### Game-Level Data (from MLB Stats API)
- ✅ Date, teams, venue
- ✅ Starting pitchers
- ✅ Weather (temperature, wind, conditions)
- ✅ First inning runs (home, away, total)
- ✅ Whether first inning had a run (yes/no)
- ✅ Final score

### Pitch-Level Data (from Baseball Savant)
- ✅ Pitcher's pitch mix and usage
- ✅ Effectiveness by pitch type
- ✅ First inning vs later innings splits
- ✅ Batter performance vs pitch types
- ✅ Historical matchup data

## 🎓 Example Workflows

### Workflow 1: Build Historical Database
```bash
# Collect multiple seasons
python mlb_first_inning_data_collector.py --season 2024
python mlb_first_inning_data_collector.py --season 2023
python mlb_first_inning_data_collector.py --season 2022

# Analyze the full dataset
python mlb_first_inning_analyzer.py --data mlb_data/first_inning_data_2024.csv
```

### Workflow 2: Analyze Today's Matchup
```bash
# Get pitcher data
python baseball_savant_scraper.py --pitcher "Chris Sale" --season 2024

# Get batter data
python baseball_savant_scraper.py --batter "Bryce Harper" --season 2024

# Full matchup analysis
python baseball_savant_scraper.py --matchup \
  --pitcher "Chris Sale" \
  --batters "Kyle Schwarber" "Bryce Harper" "Trea Turner" \
  --season 2024
```

### Workflow 3: Automated Daily Collection
```bash
# Set up automation (shows instructions)
python daily_scraper.py --setup

# Test manual run
python daily_scraper.py
```

## 📈 Next Steps (Building the Model)

After collecting data, you'll:

1. **Feature Engineering**
   - Combine pitcher quality + batter quality
   - Add park factors and weather
   - Calculate recent form

2. **Model Training**
   - Start with logistic regression
   - Can upgrade to more complex models
   - Backtest on historical data

3. **Daily Predictions**
   - Generate predictions for today's games
   - Compare to betting odds
   - Identify value bets

## 🔧 Common Issues & Solutions

**Problem:** "Module not found"
```bash
Solution: pip install [module_name]
```

**Problem:** No data collected
```bash
Solution: Check internet connection, try different season
```

**Problem:** Script takes forever
```bash
Solution: Use --max-games flag for testing first
```

**Problem:** Network access disabled
```bash
Solution: This is expected in some environments - the scripts are ready to run on your local machine
```

## 📁 File Structure

```
your-folder/
├── mlb_first_inning_data_collector.py   # Main data collector
├── baseball_savant_scraper.py           # Pitch-level scraper
├── mlb_first_inning_analyzer.py         # Data analysis
├── daily_scraper.py                     # Automated collection
├── mlb_scraper_dashboard.html           # Web interface
├── QUICK_START_GUIDE.py                 # Instructions
├── README.md                            # This file
├── mlb_data/                            # Generated data folder
│   ├── first_inning_data_2024.csv
│   ├── first_inning_data_2023.csv
│   └── ...
├── savant_data/                         # Baseball Savant data
│   ├── pitcher_519242_arsenal_2024.csv
│   └── ...
└── logs/                                # Daily scraper logs
    └── scraper_log_2024-XX-XX.txt
```

## 🎯 Team IDs (for --team flag)

| Team | ID | Team | ID |
|------|-----|------|-----|
| Braves | 144 | Yankees | 147 |
| Phillies | 143 | Mets | 121 |
| Dodgers | 119 | Red Sox | 111 |
| Astros | 117 | Giants | 137 |
| Padres | 135 | Angels | 108 |

(See QUICK_START_GUIDE.py for complete list)

## 💡 Pro Tips

1. **Start small** - Use --max-games 20 to test before collecting full seasons
2. **Check the data** - Run analyzer after each collection to verify quality
3. **Be patient** - Full season collection takes 20-30 minutes due to rate limiting
4. **Use the dashboard** - Much easier than typing commands!
5. **Automate it** - Set up daily_scraper.py to keep data current

## 🤝 Support

If you run into issues:
1. Check the QUICK_START_GUIDE.py
2. Run scripts with --help flag
3. Check the logs/ folder for error messages

## 📝 Notes

- MLB Stats API is free and doesn't require authentication
- Baseball Savant data is publicly available
- Be respectful of rate limits (built into scripts)
- All data is for personal use and analysis

## 🎬 What's Next?

Phase 1: ✅ Data Collection (YOU ARE HERE!)
Phase 2: ⏳ Model Building (coming next)
Phase 3: ⏳ Daily Predictions
Phase 4: ⏳ Odds Comparison & Value Betting

---

**Ready to get started? Run the Quick Start test command above!** ⚾
