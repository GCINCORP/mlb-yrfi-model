"""
MLB First Inning Prediction Model - Quick Start Guide
======================================================

WHAT THIS DOES:
--------------
Collects historical MLB data to predict whether the first inning
of a game will have a run scored (yes/no).

SETUP (5 minutes):
------------------

1. Install Python (if you don't have it):
   - Go to python.org/downloads
   - Download Python 3.8 or newer
   - Run installer (check "Add to PATH")

2. Install required libraries:
   Open command prompt/terminal and run:
   
   pip install requests pandas matplotlib seaborn

3. You're ready to go!


QUICK TEST (collect sample data):
---------------------------------

Run this command to collect data from 10 recent Braves games:

python mlb_first_inning_data_collector.py --season 2024 --team 144 --max-games 10

This will:
- Create a "mlb_data" folder
- Download data for 10 games
- Save to CSV file
- Show summary stats


COLLECT FULL SEASON DATA:
--------------------------

Once you verify it works, collect more data:

# Full 2024 season (all teams)
python mlb_first_inning_data_collector.py --season 2024

# Full 2023 season
python mlb_first_inning_data_collector.py --season 2023

# Full 2022 season  
python mlb_first_inning_data_collector.py --season 2022

Each season takes ~20-30 minutes (MLB API rate limiting)


ANALYZE THE DATA:
-----------------

After collecting data, run the analyzer:

python mlb_first_inning_analyzer.py --data mlb_data/first_inning_data_2024.csv

This shows you:
- Overall first inning scoring rates
- Temperature effects
- Park factors
- Team tendencies
- Key insights for your model


WHAT DATA IS COLLECTED:
------------------------

For each game:
✓ Date, teams, venue
✓ Starting pitchers (both teams)
✓ Weather (temperature, wind, conditions)
✓ First inning runs (home, away, total)
✓ Whether any runs scored in first inning (yes/no)
✓ Final score


NEXT STEPS:
-----------

Phase 1 (YOU ARE HERE):
✓ Collect historical data
✓ Analyze patterns
✓ Understand what matters

Phase 2 (Coming next):
→ Build prediction model
→ Add pitcher-specific stats
→ Add batter vs pitcher matchups
→ Backtest predictions

Phase 3 (Final):
→ Daily prediction system
→ Compare to betting odds
→ Identify value bets


COMMON ISSUES:
--------------

Problem: "requests module not found"
Solution: Run "pip install requests"

Problem: "No data collected"
Solution: Try a different season or check internet connection

Problem: Takes forever
Solution: Use --max-games flag to limit for testing


TEAM IDS (for --team flag):
----------------------------
108 - Angels          119 - Dodgers        133 - Athletics
109 - Diamondbacks    120 - Nationals      134 - Pirates  
110 - Orioles         121 - Mets           135 - Padres
111 - Red Sox         133 - Athletics      136 - Mariners
112 - Cubs            134 - Pirates        137 - Giants
113 - Reds            135 - Padres         138 - Cardinals
114 - Guardians       136 - Mariners       139 - Rays
115 - Rockies         137 - Giants         140 - Rangers
116 - Tigers          138 - Cardinals      141 - Blue Jays
117 - Astros          139 - Rays           142 - Twins
118 - Royals          140 - Rangers        143 - Phillies
144 - Braves          145 - White Sox      146 - Marlins
147 - Yankees         158 - Brewers


EXAMPLE WORKFLOW:
-----------------

# 1. Test with small dataset
python mlb_first_inning_data_collector.py --season 2024 --max-games 20

# 2. Analyze it
python mlb_first_inning_analyzer.py --data mlb_data/first_inning_data_2024.csv

# 3. If it looks good, collect full season
python mlb_first_inning_data_collector.py --season 2024

# 4. Collect previous seasons for more data
python mlb_first_inning_data_collector.py --season 2023
python mlb_first_inning_data_collector.py --season 2022

# 5. Analyze full dataset
python mlb_first_inning_analyzer.py --data mlb_data/first_inning_data_2024.csv


QUESTIONS?
----------
Run the scripts with --help flag for options:

python mlb_first_inning_data_collector.py --help
python mlb_first_inning_analyzer.py --help


LET'S GO!
---------
Start with the quick test command above and you'll have data in 2 minutes.
"""

print(__doc__)
