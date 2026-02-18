"""
Model Backtesting - Test on Historical Season
==============================================

Tests the trained model on a complete historical season to see
how profitable it would have been.

Features:
- Makes predictions for every game in the season
- Compares to actual results
- Calculates win rate, accuracy, ROI
- Shows performance by edge tier
- Identifies best/worst conditions
- Simulates betting with odds

Usage:
    python backtest_model.py --season 2024 --data mlb_data/first_inning_data_2024.csv
"""

import pandas as pd
import numpy as np
import argparse
from first_inning_predictor import FirstInningPredictor
from typing import Dict, List
import json


class ModelBacktester:
    """Backtest model performance on historical season"""
    
    def __init__(self):
        self.predictor = FirstInningPredictor()
        self.results = []
        
    def run_backtest(self, test_data_file: str, odds: int = -110):
        """
        Run complete backtest on a season
        
        Args:
            test_data_file: CSV file with season data to test
            odds: Assumed odds for betting (default -110)
        """
        print("="*70)
        print("MODEL BACKTESTING")
        print("="*70)
        
        # Load trained model
        try:
            self.predictor.load_model()
        except FileNotFoundError:
            print("\n❌ No trained model found!")
            print("Please train the model first:")
            print("  python first_inning_predictor.py --train --data mlb_data/combined_2022_2023.csv")
            return None
        
        # Load test data
        print(f"\nLoading test data from {test_data_file}...")
        test_df = pd.read_csv(test_data_file)
        print(f"Loaded {len(test_df)} games to test")
        
        # Prepare features for test data
        print("Preparing features...")
        test_df_prepared = self.predictor.prepare_features(
            test_df, 
            historical_data=test_df
        )
        
        # Get features
        X_test = test_df_prepared[self.predictor.feature_names].fillna(0)
        X_test_scaled = self.predictor.scaler.transform(X_test)
        
        # Get actual outcomes
        y_actual = test_df_prepared['target'].values
        
        # Make predictions
        print("Generating predictions...")
        y_pred_proba = self.predictor.model.predict_proba(X_test_scaled)[:, 1]
        y_pred = self.predictor.model.predict(X_test_scaled)
        
        # Store results
        results_df = pd.DataFrame({
            'game_id': range(len(test_df)),
            'date': test_df['date'],
            'home_team': test_df['home_team'],
            'away_team': test_df['away_team'],
            'venue': test_df['venue'],
            'temperature': test_df['temperature'],
            'predicted_prob': y_pred_proba,
            'predicted': y_pred,
            'actual': y_actual,
            'correct': y_pred == y_actual
        })
        
        # Calculate implied probability and edge (assuming odds)
        if odds < 0:
            implied_prob = abs(odds) / (abs(odds) + 100)
        else:
            implied_prob = 100 / (odds + 100)
        
        results_df['implied_prob'] = implied_prob
        results_df['edge'] = results_df['predicted_prob'] - implied_prob
        results_df['edge_pct'] = results_df['edge'] * 100
        
        # Classify edge tiers
        results_df['edge_tier'] = results_df['edge_pct'].apply(self._classify_edge)
        
        # Calculate bet outcomes (if we bet on predicted YES)
        results_df['would_bet'] = results_df['edge'] > 0.05  # 5%+ edge threshold
        results_df['bet_won'] = (results_df['would_bet']) & (results_df['actual'] == 1)
        results_df['bet_lost'] = (results_df['would_bet']) & (results_df['actual'] == 0)
        
        # Calculate profit/loss per bet
        if odds < 0:
            win_amount = 100 / abs(odds) * 100
        else:
            win_amount = odds
        
        results_df['profit'] = 0.0
        results_df.loc[results_df['bet_won'], 'profit'] = win_amount
        results_df.loc[results_df['bet_lost'], 'profit'] = -100
        
        self.results_df = results_df
        
        # Display comprehensive results
        self.display_results()
        
        # Save results
        output_file = test_data_file.replace('.csv', '_backtest_results.csv')
        results_df.to_csv(output_file, index=False)
        print(f"\n✅ Detailed results saved to {output_file}")
        
        return results_df
    
    def _classify_edge(self, edge_pct: float) -> str:
        """Classify edge into tiers"""
        if edge_pct >= 10:
            return "Excellent (10%+)"
        elif edge_pct >= 7:
            return "Great (7-10%)"
        elif edge_pct >= 5:
            return "Good (5-7%)"
        elif edge_pct >= 3:
            return "Fair (3-5%)"
        elif edge_pct >= 0:
            return "Marginal (0-3%)"
        else:
            return "Negative Edge"
    
    def display_results(self):
        """Display comprehensive backtest results"""
        df = self.results_df
        
        print("\n" + "="*70)
        print("OVERALL MODEL PERFORMANCE")
        print("="*70)
        
        total_games = len(df)
        correct = df['correct'].sum()
        accuracy = (correct / total_games) * 100
        
        # Predicted YES games
        pred_yes = (df['predicted'] == 1).sum()
        pred_yes_correct = ((df['predicted'] == 1) & (df['actual'] == 1)).sum()
        pred_yes_acc = (pred_yes_correct / pred_yes * 100) if pred_yes > 0 else 0
        
        # Predicted NO games
        pred_no = (df['predicted'] == 0).sum()
        pred_no_correct = ((df['predicted'] == 0) & (df['actual'] == 0)).sum()
        pred_no_acc = (pred_no_correct / pred_no * 100) if pred_no > 0 else 0
        
        print(f"\nTotal Games: {total_games}")
        print(f"Overall Accuracy: {accuracy:.2f}%")
        print(f"\nPredicted YES: {pred_yes} games ({pred_yes_acc:.1f}% correct)")
        print(f"Predicted NO: {pred_no} games ({pred_no_acc:.1f}% correct)")
        
        # Baseline comparison
        actual_yes_rate = (df['actual'] == 1).mean() * 100
        print(f"\nBaseline (actual YES rate): {actual_yes_rate:.1f}%")
        print(f"Model improvement: {accuracy - 50:+.2f} percentage points over random")
        
        # Calibration
        print("\n" + "="*70)
        print("MODEL CALIBRATION")
        print("="*70)
        
        bins = [0, 0.4, 0.45, 0.5, 0.55, 0.6, 1.0]
        labels = ['<40%', '40-45%', '45-50%', '50-55%', '55-60%', '>60%']
        
        df['prob_bin'] = pd.cut(df['predicted_prob'], bins=bins, labels=labels)
        
        cal_stats = df.groupby('prob_bin', observed=True).agg({
            'predicted_prob': 'mean',
            'actual': 'mean',
            'game_id': 'count'
        }).round(3)
        
        cal_stats.columns = ['Predicted %', 'Actual %', 'Games']
        cal_stats['Predicted %'] = (cal_stats['Predicted %'] * 100).round(1)
        cal_stats['Actual %'] = (cal_stats['Actual %'] * 100).round(1)
        
        print(cal_stats)
        
        # Betting performance
        print("\n" + "="*70)
        print("BETTING PERFORMANCE (5%+ EDGE THRESHOLD)")
        print("="*70)
        
        value_bets = df[df['would_bet']]
        
        if len(value_bets) > 0:
            bets_placed = len(value_bets)
            bets_won = value_bets['bet_won'].sum()
            bets_lost = value_bets['bet_lost'].sum()
            win_rate = (bets_won / bets_placed) * 100
            
            total_staked = bets_placed * 100
            total_profit = value_bets['profit'].sum()
            roi = (total_profit / total_staked) * 100
            
            avg_edge = value_bets['edge_pct'].mean()
            
            print(f"\nValue Bets Identified: {bets_placed}")
            print(f"Record: {bets_won}W - {bets_lost}L")
            print(f"Win Rate: {win_rate:.2f}%")
            print(f"Average Edge: {avg_edge:+.2f}%")
            print(f"\nTotal Staked: ${total_staked:,.2f}")
            print(f"Total Profit: ${total_profit:+,.2f}")
            print(f"ROI: {roi:+.2f}%")
            
            # Break-even comparison
            breakeven_rate = 52.4  # For -110 odds
            print(f"\nBreak-even win rate (-110 odds): {breakeven_rate}%")
            if win_rate > breakeven_rate:
                print(f"✅ PROFITABLE! ({win_rate - breakeven_rate:+.2f} percentage points above break-even)")
            else:
                print(f"❌ Not profitable ({win_rate - breakeven_rate:+.2f} percentage points below break-even)")
        else:
            print("\nNo bets met the 5%+ edge threshold")
        
        # Performance by edge tier
        print("\n" + "="*70)
        print("PERFORMANCE BY EDGE TIER")
        print("="*70)
        
        bet_tiers = value_bets.groupby('edge_tier').agg({
            'game_id': 'count',
            'bet_won': 'sum',
            'edge_pct': 'mean',
            'profit': 'sum'
        })
        
        bet_tiers.columns = ['Bets', 'Wins', 'Avg Edge', 'Profit']
        bet_tiers['Win %'] = (bet_tiers['Wins'] / bet_tiers['Bets'] * 100).round(1)
        bet_tiers['ROI %'] = (bet_tiers['Profit'] / (bet_tiers['Bets'] * 100) * 100).round(1)
        
        # Sort by edge tier
        tier_order = {
            'Excellent (10%+)': 0,
            'Great (7-10%)': 1,
            'Good (5-7%)': 2,
            'Fair (3-5%)': 3
        }
        bet_tiers['sort'] = bet_tiers.index.map(tier_order)
        bet_tiers = bet_tiers.sort_values('sort').drop('sort', axis=1)
        
        print(bet_tiers)
        
        # Best/worst conditions
        print("\n" + "="*70)
        print("BEST PERFORMING CONDITIONS")
        print("="*70)
        
        # By temperature
        if 'temperature' in df.columns:
            df['temp_range'] = pd.cut(df['temperature'], 
                                     bins=[0, 60, 70, 80, 120],
                                     labels=['Cold (<60)', 'Cool (60-70)', 'Warm (70-80)', 'Hot (>80)'])
            
            temp_perf = df[df['would_bet']].groupby('temp_range', observed=True).agg({
                'game_id': 'count',
                'bet_won': 'sum',
                'profit': 'sum'
            })
            
            if len(temp_perf) > 0:
                temp_perf.columns = ['Bets', 'Wins', 'Profit']
                temp_perf['Win %'] = (temp_perf['Wins'] / temp_perf['Bets'] * 100).round(1)
                
                print("\nBy Temperature:")
                print(temp_perf)
        
        # By venue (top 10)
        venue_perf = df[df['would_bet']].groupby('venue').agg({
            'game_id': 'count',
            'bet_won': 'sum',
            'profit': 'sum'
        })
        
        if len(venue_perf) > 0:
            venue_perf.columns = ['Bets', 'Wins', 'Profit']
            venue_perf['Win %'] = (venue_perf['Wins'] / venue_perf['Bets'] * 100).round(1)
            venue_perf = venue_perf[venue_perf['Bets'] >= 5]  # Min 5 bets
            venue_perf = venue_perf.sort_values('Win %', ascending=False)
            
            print("\nTop 5 Venues (min 5 bets):")
            print(venue_perf.head())
        
        # Monthly performance
        if 'date' in df.columns:
            df['month'] = pd.to_datetime(df['date']).dt.month
            monthly = df[df['would_bet']].groupby('month').agg({
                'game_id': 'count',
                'bet_won': 'sum',
                'profit': 'sum'
            })
            
            if len(monthly) > 0:
                monthly.columns = ['Bets', 'Wins', 'Profit']
                monthly['Win %'] = (monthly['Wins'] / monthly['Bets'] * 100).round(1)
                monthly.index = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][monthly.index[0]-1:monthly.index[-1]]
                
                print("\nBy Month:")
                print(monthly)
        
        print("\n" + "="*70)


def combine_seasons(season1_file: str, season2_file: str, output_file: str):
    """Combine multiple seasons into one training file"""
    print(f"Combining {season1_file} and {season2_file}...")
    
    df1 = pd.read_csv(season1_file)
    df2 = pd.read_csv(season2_file)
    
    combined = pd.concat([df1, df2], ignore_index=True)
    combined.to_csv(output_file, index=False)
    
    print(f"✅ Combined {len(combined)} games saved to {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(description='Backtest model on historical season')
    parser.add_argument('--season', type=int, help='Season to test (e.g., 2024)')
    parser.add_argument('--data', type=str, help='Path to test data CSV')
    parser.add_argument('--odds', type=int, default=-110, help='Assumed betting odds (default: -110)')
    parser.add_argument('--combine', action='store_true', help='Combine 2022+2023 for training')
    
    args = parser.parse_args()
    
    if args.combine:
        # Helper to combine training data
        combine_seasons(
            'mlb_data/first_inning_data_2022.csv',
            'mlb_data/first_inning_data_2023.csv',
            'mlb_data/combined_2022_2023.csv'
        )
        return
    
    if not args.data:
        print("Error: --data required")
        print("\nUsage:")
        print("  1. Combine training data:")
        print("     python backtest_model.py --combine")
        print("\n  2. Train model:")
        print("     python first_inning_predictor.py --train --data mlb_data/combined_2022_2023.csv")
        print("\n  3. Run backtest:")
        print("     python backtest_model.py --data mlb_data/first_inning_data_2024.csv")
        return
    
    backtester = ModelBacktester()
    backtester.run_backtest(args.data, odds=args.odds)


if __name__ == "__main__":
    main()
