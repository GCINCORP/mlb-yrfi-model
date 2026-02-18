"""
Bet Tracker - Track Performance of Value Bets
==============================================

Tracks all your bets and analyzes performance, specifically monitoring
the win rate of bets that the model determined had "good value."

Features:
- Log all bets placed
- Track results (win/loss/push)
- Calculate win percentage overall and by edge tier
- Show ROI and profit/loss
- Identify which edge levels are most profitable
- Compare to closing line value

Usage:
    # Log a new bet
    python bet_tracker.py --log
    
    # View stats
    python bet_tracker.py --stats
    
    # View detailed history
    python bet_tracker.py --history
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List
import argparse


class BetTracker:
    """Track and analyze betting performance"""
    
    def __init__(self):
        self.data_dir = "bet_tracking"
        self.bets_file = f"{self.data_dir}/bets_log.csv"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize CSV if it doesn't exist
        if not os.path.exists(self.bets_file):
            self._initialize_bet_log()
    
    def _initialize_bet_log(self):
        """Create empty bet log CSV"""
        columns = [
            'bet_id', 'date', 'game', 'home_team', 'away_team',
            'bet_type', 'selection', 'odds', 'stake',
            'model_probability', 'implied_probability', 'edge', 'edge_tier',
            'ev_dollars', 'ev_percent',
            'result', 'profit_loss', 'actual_occurred',
            'closing_odds', 'beat_closing_line',
            'notes'
        ]
        
        df = pd.DataFrame(columns=columns)
        df.to_csv(self.bets_file, index=False)
        print(f"✅ Initialized bet log at {self.bets_file}")
    
    def log_bet(self, bet_data: Dict = None):
        """
        Log a new bet
        
        If bet_data not provided, prompts user for input
        """
        if bet_data is None:
            bet_data = self._prompt_bet_entry()
        
        # Load existing bets
        df = pd.read_csv(self.bets_file)
        
        # Generate bet ID
        bet_id = f"BET{len(df)+1:04d}"
        bet_data['bet_id'] = bet_id
        
        # Classify edge tier
        edge = bet_data.get('edge', 0)
        bet_data['edge_tier'] = self._classify_edge_tier(edge)
        
        # Add to dataframe
        new_row = pd.DataFrame([bet_data])
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Save
        df.to_csv(self.bets_file, index=False)
        
        print(f"\n✅ Bet logged: {bet_id}")
        print(f"   Game: {bet_data['game']}")
        print(f"   Selection: {bet_data['selection']} @ {bet_data['odds']}")
        print(f"   Stake: ${bet_data['stake']}")
        print(f"   Edge: {edge*100:+.1f}% ({bet_data['edge_tier']})")
    
    def _prompt_bet_entry(self) -> Dict:
        """Prompt user to enter bet details"""
        print("\n" + "="*70)
        print("LOG NEW BET")
        print("="*70)
        
        bet_data = {}
        
        # Basic info
        bet_data['date'] = input("Date (YYYY-MM-DD) [today]: ").strip() or datetime.now().strftime("%Y-%m-%d")
        bet_data['away_team'] = input("Away team: ").strip()
        bet_data['home_team'] = input("Home team: ").strip()
        bet_data['game'] = f"{bet_data['away_team']} @ {bet_data['home_team']}"
        
        # Bet details
        bet_data['bet_type'] = input("Bet type [First Inning Run]: ").strip() or "First Inning Run"
        bet_data['selection'] = input("Selection (YES/NO): ").strip().upper()
        bet_data['odds'] = int(input("Odds (e.g., -110): "))
        bet_data['stake'] = float(input("Stake amount ($): "))
        
        # Model data
        model_prob = float(input("Model probability (0-100): ")) / 100
        bet_data['model_probability'] = model_prob
        
        # Calculate implied probability
        odds = bet_data['odds']
        if odds < 0:
            implied_prob = abs(odds) / (abs(odds) + 100)
        else:
            implied_prob = 100 / (odds + 100)
        
        bet_data['implied_probability'] = implied_prob
        bet_data['edge'] = model_prob - implied_prob
        
        # Calculate EV
        if odds < 0:
            win_amount = bet_data['stake'] * (100 / abs(odds))
        else:
            win_amount = bet_data['stake'] * (odds / 100)
        
        ev = (model_prob * win_amount) - ((1 - model_prob) * bet_data['stake'])
        bet_data['ev_dollars'] = ev
        bet_data['ev_percent'] = (ev / bet_data['stake']) * 100
        
        # Result (if known)
        result = input("Result (WIN/LOSS/PUSH/PENDING) [PENDING]: ").strip().upper() or "PENDING"
        bet_data['result'] = result
        
        if result == "WIN":
            bet_data['profit_loss'] = win_amount
            bet_data['actual_occurred'] = True
        elif result == "LOSS":
            bet_data['profit_loss'] = -bet_data['stake']
            bet_data['actual_occurred'] = False
        elif result == "PUSH":
            bet_data['profit_loss'] = 0
            bet_data['actual_occurred'] = None
        else:
            bet_data['profit_loss'] = 0
            bet_data['actual_occurred'] = None
        
        # Optional fields
        bet_data['closing_odds'] = None
        bet_data['beat_closing_line'] = None
        bet_data['notes'] = input("Notes (optional): ").strip()
        
        return bet_data
    
    def update_result(self, bet_id: str, result: str, actual_occurred: bool = None):
        """
        Update the result of a bet
        
        Args:
            bet_id: Bet ID (e.g., "BET0001")
            result: "WIN", "LOSS", or "PUSH"
            actual_occurred: Whether first inning run actually happened (for calibration)
        """
        df = pd.read_csv(self.bets_file)
        
        # Find bet
        idx = df[df['bet_id'] == bet_id].index
        
        if len(idx) == 0:
            print(f"❌ Bet {bet_id} not found")
            return
        
        idx = idx[0]
        
        # Update result
        df.loc[idx, 'result'] = result
        df.loc[idx, 'actual_occurred'] = actual_occurred
        
        # Calculate profit/loss
        odds = df.loc[idx, 'odds']
        stake = df.loc[idx, 'stake']
        
        if result == "WIN":
            if odds < 0:
                profit = stake * (100 / abs(odds))
            else:
                profit = stake * (odds / 100)
            df.loc[idx, 'profit_loss'] = profit
        elif result == "LOSS":
            df.loc[idx, 'profit_loss'] = -stake
        else:  # PUSH
            df.loc[idx, 'profit_loss'] = 0
        
        # Save
        df.to_csv(self.bets_file, index=False)
        
        print(f"✅ Updated {bet_id}: {result}")
    
    def _classify_edge_tier(self, edge: float) -> str:
        """Classify edge into tiers"""
        if edge >= 0.10:
            return "Excellent (10%+)"
        elif edge >= 0.07:
            return "Great (7-10%)"
        elif edge >= 0.05:
            return "Good (5-7%)"
        elif edge >= 0.03:
            return "Fair (3-5%)"
        elif edge >= 0:
            return "Marginal (0-3%)"
        else:
            return "Negative Edge"
    
    def get_stats(self, min_edge: float = 0.03):
        """
        Calculate and display comprehensive statistics
        
        Args:
            min_edge: Minimum edge to consider a "value bet" (default 3%)
        """
        df = pd.read_csv(self.bets_file)
        
        # Filter to completed bets
        completed = df[df['result'].isin(['WIN', 'LOSS', 'PUSH'])].copy()
        
        if len(completed) == 0:
            print("\n📊 No completed bets yet!")
            return
        
        print("\n" + "="*70)
        print("BET TRACKING STATISTICS")
        print("="*70)
        
        # Overall stats
        total_bets = len(completed)
        wins = len(completed[completed['result'] == 'WIN'])
        losses = len(completed[completed['result'] == 'LOSS'])
        pushes = len(completed[completed['result'] == 'PUSH'])
        
        win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
        
        total_staked = completed['stake'].sum()
        total_profit = completed['profit_loss'].sum()
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0
        
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"   Total Bets: {total_bets}")
        print(f"   Record: {wins}W - {losses}L - {pushes}P")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Total Staked: ${total_staked:.2f}")
        print(f"   Total Profit: ${total_profit:+.2f}")
        print(f"   ROI: {roi:+.1f}%")
        
        # Value bets performance (the key metric!)
        print(f"\n⭐ VALUE BETS PERFORMANCE (Edge ≥ {min_edge*100:.0f}%):")
        print("-"*70)
        
        value_bets = completed[completed['edge'] >= min_edge]
        
        if len(value_bets) > 0:
            vb_total = len(value_bets)
            vb_wins = len(value_bets[value_bets['result'] == 'WIN'])
            vb_losses = len(value_bets[value_bets['result'] == 'LOSS'])
            vb_win_rate = (vb_wins / (vb_wins + vb_losses)) * 100 if (vb_wins + vb_losses) > 0 else 0
            
            vb_staked = value_bets['stake'].sum()
            vb_profit = value_bets['profit_loss'].sum()
            vb_roi = (vb_profit / vb_staked) * 100 if vb_staked > 0 else 0
            
            avg_edge = value_bets['edge'].mean() * 100
            
            print(f"   Value Bets Placed: {vb_total}")
            print(f"   Record: {vb_wins}W - {vb_losses}L")
            print(f"   Win Rate: {vb_win_rate:.1f}% 🎯")
            print(f"   Average Edge: {avg_edge:+.1f}%")
            print(f"   Total Profit: ${vb_profit:+.2f}")
            print(f"   ROI: {vb_roi:+.1f}%")
            
            # Expected vs Actual
            expected_wins = value_bets['model_probability'].sum()
            print(f"\n   Expected Wins (per model): {expected_wins:.1f}")
            print(f"   Actual Wins: {vb_wins}")
            print(f"   Difference: {vb_wins - expected_wins:+.1f}")
        else:
            print(f"   No value bets placed yet with ≥{min_edge*100:.0f}% edge")
        
        # Performance by edge tier
        print(f"\n📈 PERFORMANCE BY EDGE TIER:")
        print("-"*70)
        
        edge_tiers = completed.groupby('edge_tier').agg({
            'bet_id': 'count',
            'result': lambda x: (x == 'WIN').sum(),
            'stake': 'sum',
            'profit_loss': 'sum',
            'edge': 'mean'
        }).round(2)
        
        edge_tiers.columns = ['Bets', 'Wins', 'Staked', 'Profit', 'Avg Edge']
        edge_tiers['Win%'] = ((edge_tiers['Wins'] / edge_tiers['Bets']) * 100).round(1)
        edge_tiers['ROI%'] = ((edge_tiers['Profit'] / edge_tiers['Staked']) * 100).round(1)
        edge_tiers['Avg Edge'] = (edge_tiers['Avg Edge'] * 100).round(1)
        
        # Sort by edge tier
        tier_order = {
            'Excellent (10%+)': 0,
            'Great (7-10%)': 1,
            'Good (5-7%)': 2,
            'Fair (3-5%)': 3,
            'Marginal (0-3%)': 4,
            'Negative Edge': 5
        }
        edge_tiers['sort_order'] = edge_tiers.index.map(tier_order)
        edge_tiers = edge_tiers.sort_values('sort_order').drop('sort_order', axis=1)
        
        print(edge_tiers.to_string())
        
        # Model calibration
        print(f"\n🎯 MODEL CALIBRATION:")
        print("-"*70)
        
        calibration_data = completed[completed['actual_occurred'].notna()].copy()
        
        if len(calibration_data) > 0:
            bins = [0, 0.45, 0.5, 0.55, 0.6, 1.0]
            labels = ['<45%', '45-50%', '50-55%', '55-60%', '>60%']
            
            calibration_data['prob_bin'] = pd.cut(
                calibration_data['model_probability'],
                bins=bins,
                labels=labels
            )
            
            cal_stats = calibration_data.groupby('prob_bin', observed=True).agg({
                'model_probability': 'mean',
                'actual_occurred': 'mean',
                'bet_id': 'count'
            }).round(3)
            
            cal_stats.columns = ['Predicted', 'Actual', 'Count']
            cal_stats['Predicted'] = (cal_stats['Predicted'] * 100).round(1)
            cal_stats['Actual'] = (cal_stats['Actual'] * 100).round(1)
            
            print("Model predictions vs actual outcomes:")
            print(cal_stats.to_string())
        else:
            print("Not enough data yet (need to record actual outcomes)")
        
        # Recent performance
        print(f"\n📅 RECENT PERFORMANCE (Last 10 Bets):")
        print("-"*70)
        
        recent = completed.tail(10)[['date', 'game', 'selection', 'odds', 'edge', 'result', 'profit_loss']]
        recent['edge'] = (recent['edge'] * 100).round(1)
        recent['profit_loss'] = recent['profit_loss'].round(2)
        
        print(recent.to_string(index=False))
        
        print("\n" + "="*70)
    
    def get_history(self, n: int = 20):
        """Display bet history"""
        df = pd.read_csv(self.bets_file)
        
        print("\n" + "="*70)
        print(f"BET HISTORY (Last {n} bets)")
        print("="*70)
        
        recent = df.tail(n)
        
        display_cols = ['bet_id', 'date', 'game', 'selection', 'odds', 'stake',
                       'edge', 'edge_tier', 'result', 'profit_loss']
        
        display = recent[display_cols].copy()
        display['edge'] = (display['edge'] * 100).round(1)
        display['profit_loss'] = display['profit_loss'].round(2)
        
        print(display.to_string(index=False))
    
    def export_data(self, filename: str = None):
        """Export bet data to CSV"""
        if filename is None:
            filename = f"{self.data_dir}/bet_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        df = pd.read_csv(self.bets_file)
        df.to_csv(filename, index=False)
        
        print(f"✅ Data exported to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Bet tracking system')
    parser.add_argument('--log', action='store_true', help='Log a new bet')
    parser.add_argument('--stats', action='store_true', help='View statistics')
    parser.add_argument('--history', action='store_true', help='View bet history')
    parser.add_argument('--update', type=str, help='Update bet result (bet_id)')
    parser.add_argument('--result', type=str, help='Result for update (WIN/LOSS/PUSH)')
    parser.add_argument('--export', action='store_true', help='Export data to CSV')
    
    args = parser.parse_args()
    
    tracker = BetTracker()
    
    if args.log:
        tracker.log_bet()
    
    elif args.stats:
        tracker.get_stats()
    
    elif args.history:
        tracker.get_history()
    
    elif args.update and args.result:
        tracker.update_result(args.update, args.result.upper())
    
    elif args.export:
        tracker.export_data()
    
    else:
        print("Usage:")
        print("  Log bet:     python bet_tracker.py --log")
        print("  View stats:  python bet_tracker.py --stats")
        print("  View history: python bet_tracker.py --history")
        print("  Update result: python bet_tracker.py --update BET0001 --result WIN")
        print("  Export data: python bet_tracker.py --export")


if __name__ == "__main__":
    main()
