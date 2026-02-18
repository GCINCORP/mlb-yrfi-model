"""
Daily First Inning Predictions - Value Bet Identifier
======================================================

Generates predictions for today's games and identifies value bets.

Features:
- Auto-sorts games by best value/edge
- Compares model predictions to sportsbook odds
- Highlights +EV opportunities
- Saves predictions to file

Usage:
    python daily_predictor.py --date 2024-04-15
    python daily_predictor.py  # Uses today's date
"""

import pandas as pd
import json
import os
from datetime import datetime, date
from typing import List, Dict
import argparse
from first_inning_predictor import FirstInningPredictor


class DailyPredictor:
    """Generate daily predictions and identify value bets"""
    
    def __init__(self):
        self.predictor = FirstInningPredictor()
        self.predictions_dir = "predictions"
        os.makedirs(self.predictions_dir, exist_ok=True)
        
    def american_odds_to_probability(self, odds: int) -> float:
        """
        Convert American odds to implied probability
        
        Args:
            odds: American odds (e.g., -110, +150)
            
        Returns:
            Implied probability as decimal (e.g., 0.524 for -110)
        """
        if odds < 0:
            # Favorite
            return abs(odds) / (abs(odds) + 100)
        else:
            # Underdog
            return 100 / (odds + 100)
    
    def calculate_edge(self, model_prob: float, implied_prob: float) -> float:
        """Calculate betting edge"""
        return model_prob - implied_prob
    
    def calculate_ev(self, model_prob: float, odds: int, stake: float = 100) -> Dict:
        """
        Calculate expected value of a bet
        
        Args:
            model_prob: Model's probability (0-1)
            odds: American odds
            stake: Bet amount
            
        Returns:
            Dict with EV calculations
        """
        # Calculate potential win amount
        if odds < 0:
            win_amount = stake * (100 / abs(odds))
        else:
            win_amount = stake * (odds / 100)
        
        # Calculate EV
        ev = (model_prob * win_amount) - ((1 - model_prob) * stake)
        ev_percent = (ev / stake) * 100
        
        return {
            'stake': stake,
            'win_amount': win_amount,
            'ev_dollars': ev,
            'ev_percent': ev_percent,
            'roi': ev_percent
        }
    
    def get_todays_games(self, target_date: str = None) -> List[Dict]:
        """
        Get today's MLB schedule
        
        In production, this would call MLB Stats API
        For now, returns sample data
        """
        if target_date is None:
            target_date = date.today().strftime("%Y-%m-%d")
        
        print(f"Getting games for {target_date}...")
        
        # Sample games for demonstration
        # In production, you'd fetch from MLB API
        games = [
            {
                'game_id': 'ATL_PHI_20240415',
                'date': target_date,
                'home_team': 'Atlanta Braves',
                'away_team': 'Philadelphia Phillies',
                'home_pitcher': 'Spencer Strider',
                'away_pitcher': 'Zack Wheeler',
                'venue': 'Truist Park',
                'temperature': 78,
                'wind': '8 mph SW',
                'game_time': '19:20'
            },
            {
                'game_id': 'NYY_BOS_20240415',
                'date': target_date,
                'home_team': 'New York Yankees',
                'away_team': 'Boston Red Sox',
                'home_pitcher': 'Gerrit Cole',
                'away_pitcher': 'Chris Sale',
                'venue': 'Yankee Stadium',
                'temperature': 65,
                'wind': '12 mph NE',
                'game_time': '19:05'
            },
            {
                'game_id': 'LAD_SD_20240415',
                'date': target_date,
                'home_team': 'San Diego Padres',
                'away_team': 'Los Angeles Dodgers',
                'home_pitcher': 'Yu Darvish',
                'away_pitcher': 'Tyler Glasnow',
                'venue': 'Petco Park',
                'temperature': 72,
                'wind': '6 mph W',
                'game_time': '21:40'
            },
            {
                'game_id': 'HOU_SEA_20240415',
                'date': target_date,
                'home_team': 'Seattle Mariners',
                'away_team': 'Houston Astros',
                'home_pitcher': 'Logan Gilbert',
                'away_pitcher': 'Framber Valdez',
                'venue': 'T-Mobile Park',
                'temperature': 58,
                'wind': '15 mph N',
                'game_time': '21:40'
            },
        ]
        
        return games
    
    def add_manual_odds(self, predictions: List[Dict]) -> List[Dict]:
        """
        Prompt user to enter odds for each game
        
        In production, this would fetch from odds API
        """
        print("\n" + "="*70)
        print("ENTER SPORTSBOOK ODDS")
        print("="*70)
        print("Enter the odds for 'YES - First Inning Run' for each game")
        print("Format: Enter American odds (e.g., -110, +150)")
        print("Press Enter to skip a game")
        print()
        
        for pred in predictions:
            print(f"\n{pred['away_team']} @ {pred['home_team']}")
            print(f"Model prediction: {pred['model_probability']*100:.1f}% chance of first inning run")
            
            odds_input = input("Enter odds for YES (or press Enter to skip): ").strip()
            
            if odds_input:
                try:
                    odds = int(odds_input)
                    pred['odds'] = odds
                    pred['has_odds'] = True
                except ValueError:
                    print("Invalid odds format. Skipping...")
                    pred['has_odds'] = False
            else:
                pred['has_odds'] = False
        
        return predictions
    
    def generate_predictions(self, target_date: str = None, include_odds: bool = False):
        """
        Generate predictions for all games on target date
        """
        print("="*70)
        print("MLB FIRST INNING PREDICTIONS")
        print("="*70)
        
        # Load model
        try:
            self.predictor.load_model()
        except FileNotFoundError:
            print("\n❌ No trained model found!")
            print("Please train the model first:")
            print("  python first_inning_predictor.py --train --data mlb_data/first_inning_data_2024.csv")
            return None
        
        # Get today's games
        games = self.get_todays_games(target_date)
        
        if not games:
            print(f"\nNo games found for {target_date}")
            return None
        
        print(f"\nFound {len(games)} games")
        
        # Generate predictions
        predictions = []
        
        for game in games:
            # Get prediction
            pred = self.predictor.predict_game(game)
            
            # Combine game data with prediction
            result = {
                **game,
                'model_probability': pred['probability'],
                'model_prediction': pred['prediction'],
                'confidence': pred['confidence'],
                'has_odds': False
            }
            
            predictions.append(result)
        
        # Optionally add odds
        if include_odds:
            predictions = self.add_manual_odds(predictions)
        
        # Calculate value/edge for games with odds
        for pred in predictions:
            if pred['has_odds']:
                odds = pred['odds']
                model_prob = pred['model_probability']
                implied_prob = self.american_odds_to_probability(odds)
                edge = self.calculate_edge(model_prob, implied_prob)
                ev = self.calculate_ev(model_prob, odds)
                
                pred['implied_probability'] = implied_prob
                pred['edge'] = edge
                pred['edge_percent'] = edge * 100
                pred['ev_dollars'] = ev['ev_dollars']
                pred['ev_percent'] = ev['ev_percent']
                pred['is_value_bet'] = edge > 0.03  # 3%+ edge
                pred['bet_quality'] = self._classify_bet_quality(edge)
        
        # Sort by edge (best value first) for games with odds
        predictions_with_odds = [p for p in predictions if p['has_odds']]
        predictions_without_odds = [p for p in predictions if not p['has_odds']]
        
        if predictions_with_odds:
            predictions_with_odds.sort(key=lambda x: x.get('edge', 0), reverse=True)
        
        # Combine: odds games first (sorted by value), then no-odds games
        sorted_predictions = predictions_with_odds + predictions_without_odds
        
        # Display results
        self.display_predictions(sorted_predictions)
        
        # Save to file
        self.save_predictions(sorted_predictions, target_date)
        
        return sorted_predictions
    
    def _classify_bet_quality(self, edge: float) -> str:
        """Classify bet quality based on edge"""
        if edge >= 0.10:
            return "⭐⭐⭐ EXCELLENT"
        elif edge >= 0.07:
            return "⭐⭐ GREAT"
        elif edge >= 0.05:
            return "⭐ GOOD"
        elif edge >= 0.03:
            return "✓ FAIR"
        elif edge >= 0:
            return "• MARGINAL"
        else:
            return "✗ NO VALUE"
    
    def display_predictions(self, predictions: List[Dict]):
        """Display predictions in a formatted table"""
        
        print("\n" + "="*70)
        print("PREDICTIONS SORTED BY VALUE/EDGE")
        print("="*70)
        
        # Games with odds (sorted by value)
        games_with_odds = [p for p in predictions if p['has_odds']]
        games_without_odds = [p for p in predictions if not p['has_odds']]
        
        if games_with_odds:
            print("\n🎯 GAMES WITH ODDS (SORTED BY BEST VALUE):")
            print("-"*70)
            
            for i, pred in enumerate(games_with_odds, 1):
                print(f"\n#{i} - {pred['away_team']} @ {pred['home_team']}")
                print(f"   Time: {pred['game_time']} | Venue: {pred['venue']}")
                print(f"   Pitchers: {pred['away_pitcher']} vs {pred['home_pitcher']}")
                print(f"   Weather: {pred['temperature']}°F, {pred['wind']}")
                print()
                print(f"   MODEL: {pred['model_probability']*100:.1f}% chance of 1st inning run")
                print(f"   ODDS: {pred['odds']:+d} (implies {pred['implied_probability']*100:.1f}%)")
                print(f"   EDGE: {pred['edge_percent']:+.1f}% | {pred['bet_quality']}")
                
                if pred['is_value_bet']:
                    print(f"   💰 EV: ${pred['ev_dollars']:+.2f} per $100 bet ({pred['ev_percent']:+.1f}% ROI)")
                    print(f"   ✅ RECOMMENDATION: BET - {pred['bet_quality']}")
                else:
                    print(f"   ❌ RECOMMENDATION: SKIP (insufficient edge)")
                
                print("-"*70)
        
        if games_without_odds:
            print("\n📊 GAMES WITHOUT ODDS:")
            print("-"*70)
            
            for pred in games_without_odds:
                print(f"\n{pred['away_team']} @ {pred['home_team']}")
                print(f"   MODEL: {pred['model_probability']*100:.1f}% chance of 1st inning run")
                print(f"   Confidence: {pred['confidence']}")
                print("-"*70)
    
    def save_predictions(self, predictions: List[Dict], target_date: str = None):
        """Save predictions to JSON file"""
        if target_date is None:
            target_date = date.today().strftime("%Y-%m-%d")
        
        filename = f"{self.predictions_dir}/predictions_{target_date}.json"
        
        with open(filename, 'w') as f:
            json.dump(predictions, f, indent=2)
        
        print(f"\n✅ Predictions saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Generate daily first inning predictions')
    parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--odds', action='store_true', help='Include manual odds entry')
    
    args = parser.parse_args()
    
    predictor = DailyPredictor()
    predictor.generate_predictions(target_date=args.date, include_odds=args.odds)


if __name__ == "__main__":
    main()
