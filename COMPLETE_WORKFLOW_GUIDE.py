"""
COMPLETE WORKFLOW GUIDE
=======================

Full step-by-step guide for using the MLB First Inning Prediction System

═══════════════════════════════════════════════════════════════════════
PART 1: ONE-TIME SETUP (15 minutes)
═══════════════════════════════════════════════════════════════════════

1. Install Python 3.8+
   - Download from python.org
   - During installation, CHECK "Add to PATH"

2. Install Required Libraries
   Open terminal/command prompt:
   
   pip install requests pandas scikit-learn matplotlib seaborn beautifulsoup4

3. Download All Scripts
   - Put all .py files in one folder
   - Keep them together!

4. Collect Historical Data (for training)
   
   # Test with 20 games first
   python mlb_first_inning_data_collector.py --season 2024 --max-games 20
   
   # If that works, collect full seasons
   python mlb_first_inning_data_collector.py --season 2024
   python mlb_first_inning_data_collector.py --season 2023
   python mlb_first_inning_data_collector.py --season 2022
   
   ⏱️ This takes 20-30 minutes per season (API rate limits)

5. Train the Model
   
   python first_inning_predictor.py --train --data mlb_data/first_inning_data_2024.csv
   
   ✅ This creates your trained model
   ⏱️ Takes about 30 seconds


═══════════════════════════════════════════════════════════════════════
PART 2: DAILY WORKFLOW (10-15 minutes per day)
═══════════════════════════════════════════════════════════════════════

STEP 1: Generate Predictions (Morning)
---------------------------------------

Run:
    python daily_predictor.py --odds
    
This will:
- Load your trained model
- Show today's games
- Ask you to enter odds from sportsbook
- Calculate edge/value for each game
- AUTO-SORT by best value (highest edge first!)
- Show EV and bet recommendations

Example output:

    🎯 GAMES WITH ODDS (SORTED BY BEST VALUE):
    
    #1 - Phillies @ Braves
       Edge: +8.5% | ⭐⭐ GREAT
       💰 EV: +$18.30 per $100 bet (+15.9% ROI)
       ✅ RECOMMENDATION: BET - ⭐⭐ GREAT
    
    #2 - Red Sox @ Yankees
       Edge: +5.2% | ⭐ GOOD
       💰 EV: +$11.50 per $100 bet (+9.8% ROI)
       ✅ RECOMMENDATION: BET - ⭐ GOOD
    
    #3 - Dodgers @ Padres
       Edge: +2.1% | • MARGINAL
       ❌ RECOMMENDATION: SKIP (insufficient edge)


STEP 2: Get Odds from Sportsbooks
----------------------------------

Check these sites (all free to view):
- DraftKings.com
- FanDuel.com
- BetMGM.com
- OddsChecker.com (compares multiple books)

Look for "First Inning - Run Scored? Yes/No"

Enter the odds when prompted by daily_predictor.py


STEP 3: Place Bets on Value Games
----------------------------------

Only bet games with:
✅ 5%+ edge (recommended minimum)
✅ High or Medium confidence
✅ Reasonable odds (avoid extreme longshots)


STEP 4: Log Your Bets
----------------------

For EVERY bet you place:

    python bet_tracker.py --log

Enter the details when prompted.

This is CRITICAL - without logging, you can't track if your model works!


STEP 5: Update Results (Evening)
---------------------------------

After games finish:

    python bet_tracker.py --update BET0001 --result WIN
    python bet_tracker.py --update BET0002 --result LOSS

Or use --log again and enter the result interactively.


═══════════════════════════════════════════════════════════════════════
PART 3: WEEKLY REVIEW (15 minutes per week)
═══════════════════════════════════════════════════════════════════════

Check Your Stats:

    python bet_tracker.py --stats

This shows:
📊 Overall win rate and profit
⭐ VALUE BETS win rate (THIS IS THE KEY METRIC!)
📈 Performance by edge tier
🎯 Model calibration
📅 Recent results

WHAT TO LOOK FOR:

✅ GOOD SIGNS:
   - Value bets (5%+ edge) winning at 54-55%+
   - Positive ROI on value bets
   - Higher edge tiers performing better
   - Model calibration is accurate

❌ WARNING SIGNS:
   - Value bets winning <50%
   - Negative ROI despite positive edge
   - Higher edge bets performing worse than lower edge
   - Model predictions way off actual results

If you see warning signs → STOP betting, review model


═══════════════════════════════════════════════════════════════════════
PART 4: EXAMPLE DAILY SESSION
═══════════════════════════════════════════════════════════════════════

9:00 AM - Generate Predictions
-------------------------------
$ python daily_predictor.py --odds

Found 12 games today.
Enter odds for each game...

[Shows sorted list, top game has 7.5% edge]


9:15 AM - Review Top 3 Value Bets
----------------------------------
Game 1: Braves vs Phillies (7.5% edge) ✅ BET $50
Game 2: Yankees vs Red Sox (5.8% edge) ✅ BET $50  
Game 3: Dodgers vs Padres (3.2% edge) ❌ SKIP (below 5% threshold)


9:20 AM - Place Bets on Sportsbook
-----------------------------------
Place the 2 bets identified above


9:25 AM - Log Bets
------------------
$ python bet_tracker.py --log
[Enter details for Braves bet]

$ python bet_tracker.py --log
[Enter details for Yankees bet]


10:00 PM - Update Results
--------------------------
Braves bet: WON ✅
Yankees bet: LOST ❌

$ python bet_tracker.py --update BET0015 --result WIN
$ python bet_tracker.py --update BET0016 --result LOSS


═══════════════════════════════════════════════════════════════════════
PART 5: KEY METRICS TO TRACK
═══════════════════════════════════════════════════════════════════════

PRIMARY METRIC:
📊 Win rate on value bets (5%+ edge)
   Target: 54-55%+ to be profitable
   Minimum: 52% to break even

SECONDARY METRICS:
💰 ROI on value bets
   Target: +5-10%
   Acceptable: +2-5%
   Warning: <0%

📈 Performance by edge tier
   10%+ edge should win more than 5% edge
   If reversed, model may be miscalibrated

🎯 Actual vs Expected
   Model says 58%, should win ~58% of time
   If way off, model needs retraining


═══════════════════════════════════════════════════════════════════════
PART 6: BANKROLL MANAGEMENT
═══════════════════════════════════════════════════════════════════════

RECOMMENDED APPROACH:

1. Start with a dedicated bankroll
   Example: $1,000

2. Bet 1-3% per bet
   $1,000 bankroll → $10-30 per bet

3. Scale with edge:
   3-5% edge  → 1% of bankroll
   5-7% edge  → 2% of bankroll
   7-10% edge → 3% of bankroll
   10%+ edge  → 4-5% of bankroll (max)

4. Never risk more than 5% on one bet
   Even if edge is huge!

5. Track bankroll weekly
   Adjust bet sizes as bankroll grows/shrinks


═══════════════════════════════════════════════════════════════════════
PART 7: WHEN TO STOP/ADJUST
═══════════════════════════════════════════════════════════════════════

STOP BETTING IF:
❌ Value bets losing 55%+ (over 50+ bets)
❌ Consistent negative ROI (over 100+ bets)
❌ Model predictions consistently wrong
❌ Can't find games with 5%+ edge anymore

REVIEW MODEL IF:
⚠️ Win rate fluctuating wildly
⚠️ Calibration way off
⚠️ Performance varies dramatically by park/team

RETRAIN MODEL IF:
🔄 New season starts
🔄 MLB rule changes
🔄 After 6+ months
🔄 Performance degrades


═══════════════════════════════════════════════════════════════════════
PART 8: QUICK REFERENCE COMMANDS
═══════════════════════════════════════════════════════════════════════

# Daily routine
python daily_predictor.py --odds          # Generate predictions
python bet_tracker.py --log               # Log a bet
python bet_tracker.py --update BET0001 --result WIN  # Update result

# Weekly review
python bet_tracker.py --stats             # View all stats
python bet_tracker.py --history           # View recent bets

# Data collection (occasional)
python mlb_first_inning_data_collector.py --season 2024
python first_inning_predictor.py --train --data mlb_data/first_inning_data_2024.csv

# Advanced
python baseball_savant_scraper.py --matchup --pitcher "Chris Sale" --batters "Batter1" "Batter2" "Batter3"


═══════════════════════════════════════════════════════════════════════
PART 9: TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════

PROBLEM: "No module named 'sklearn'"
SOLUTION: pip install scikit-learn

PROBLEM: "Model file not found"
SOLUTION: Run training first:
          python first_inning_predictor.py --train --data mlb_data/first_inning_data_2024.csv

PROBLEM: "No games found"
SOLUTION: Check that you're running during baseball season (April-October)

PROBLEM: Model accuracy is terrible
SOLUTION: Need more training data. Collect 2-3 full seasons.

PROBLEM: Can't find value bets
SOLUTION: Either sportsbooks are very sharp, or your model needs work.
          This is normal - value bets are rare!


═══════════════════════════════════════════════════════════════════════
PART 10: REALISTIC EXPECTATIONS
═══════════════════════════════════════════════════════════════════════

✅ REALISTIC:
   - Finding 1-3 value bets per day
   - 53-55% win rate on value bets
   - 5-10% ROI long-term
   - Variance - winning/losing streaks happen
   - Slow, steady profit over months

❌ UNREALISTIC:
   - 70% win rate
   - Getting rich quick
   - Betting every game
   - Never losing
   - Consistent daily profit

📊 SAMPLE RESULTS (100 bets, 54% win rate, avg $50/bet):
   Total wagered: $5,000
   Total profit: $250-500
   ROI: 5-10%

This is GOOD! Beating sportsbooks consistently is hard.


═══════════════════════════════════════════════════════════════════════
SUMMARY
═══════════════════════════════════════════════════════════════════════

DAILY (15 min):
1. Generate predictions
2. Enter odds
3. Bet top value games (5%+ edge)
4. Log all bets
5. Update results

WEEKLY (15 min):
1. Review stats
2. Check value bet performance
3. Adjust strategy if needed

MONTHLY:
1. Deep dive into which factors are working
2. Consider retraining model
3. Evaluate overall profitability

The system AUTO-SORTS by value, TRACKS your value bet performance,
and helps you MAKE MONEY long-term if used disciplined.

Good luck! 🍀⚾💰
"""

print(__doc__)
