"""
MLB First Inning Analysis - Pattern Discovery
==============================================

This script analyzes collected first inning data to identify factors
that correlate with first inning runs being scored.

Usage:
    python mlb_first_inning_analyzer.py --data mlb_data/first_inning_data_2024.csv
"""

import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import os

class FirstInningAnalyzer:
    """Analyzes first inning scoring patterns"""
    
    def __init__(self, data_file: str):
        """Load data from CSV"""
        print(f"Loading data from {data_file}...")
        self.df = pd.read_csv(data_file)
        print(f"Loaded {len(self.df)} games\n")
        
    def basic_stats(self):
        """Print basic statistics about first inning scoring"""
        print("=" * 70)
        print("BASIC FIRST INNING STATISTICS")
        print("=" * 70)
        
        total_games = len(self.df)
        games_with_runs = self.df['first_inning_run_scored'].sum()
        pct = (games_with_runs / total_games * 100)
        
        print(f"Total games: {total_games}")
        print(f"Games with first inning run: {games_with_runs} ({pct:.1f}%)")
        print(f"Games without first inning run: {total_games - games_with_runs} ({100-pct:.1f}%)")
        
        # Average runs in first inning
        avg_runs = (self.df['first_inning_runs_home'] + self.df['first_inning_runs_away']).mean()
        print(f"Average first inning runs per game: {avg_runs:.2f}")
        
        print()
    
    def analyze_by_temperature(self):
        """Analyze correlation between temperature and first inning scoring"""
        print("=" * 70)
        print("TEMPERATURE ANALYSIS")
        print("=" * 70)
        
        # Filter out games without temperature data
        temp_data = self.df.dropna(subset=['temperature'])
        
        if len(temp_data) == 0:
            print("No temperature data available")
            return
        
        # Create temperature bins
        temp_data['temp_range'] = pd.cut(temp_data['temperature'], 
                                         bins=[0, 50, 60, 70, 80, 90, 120],
                                         labels=['<50°F', '50-60°F', '60-70°F', 
                                                '70-80°F', '80-90°F', '>90°F'])
        
        # Calculate first inning run rate by temperature
        temp_analysis = temp_data.groupby('temp_range').agg({
            'first_inning_run_scored': ['sum', 'count', 'mean']
        }).round(3)
        
        temp_analysis.columns = ['Runs Scored', 'Total Games', 'Rate']
        temp_analysis['Rate'] = (temp_analysis['Rate'] * 100).round(1)
        
        print(temp_analysis)
        print(f"\nColdest games (<60°F): {temp_analysis.loc[temp_analysis.index[:2], 'Rate'].mean():.1f}% rate")
        print(f"Hottest games (>80°F): {temp_analysis.loc[temp_analysis.index[-2:], 'Rate'].mean():.1f}% rate")
        print()
    
    def analyze_by_venue(self, top_n: int = 10):
        """Analyze which venues have highest first inning scoring rates"""
        print("=" * 70)
        print(f"TOP {top_n} VENUES FOR FIRST INNING RUNS")
        print("=" * 70)
        
        venue_stats = self.df.groupby('venue').agg({
            'first_inning_run_scored': ['sum', 'count', 'mean']
        })
        
        venue_stats.columns = ['Runs', 'Games', 'Rate']
        venue_stats['Rate'] = (venue_stats['Rate'] * 100).round(1)
        
        # Filter venues with at least 10 games
        venue_stats = venue_stats[venue_stats['Games'] >= 10]
        venue_stats = venue_stats.sort_values('Rate', ascending=False)
        
        print(venue_stats.head(top_n))
        print()
    
    def analyze_by_team(self):
        """Analyze teams that score/allow most first inning runs"""
        print("=" * 70)
        print("TEAM ANALYSIS - FIRST INNING OFFENSE")
        print("=" * 70)
        
        # Home team offense
        home_off = self.df.groupby('home_team').agg({
            'first_inning_runs_home': ['sum', 'count', 'mean']
        })
        
        # Away team offense  
        away_off = self.df.groupby('away_team').agg({
            'first_inning_runs_away': ['sum', 'count', 'mean']
        })
        
        # Combine
        home_off.columns = ['Runs', 'Games', 'Avg']
        away_off.columns = ['Runs', 'Games', 'Avg']
        
        total_off = pd.concat([home_off, away_off]).groupby(level=0).sum()
        total_off['Avg'] = total_off['Runs'] / total_off['Games']
        total_off = total_off.sort_values('Avg', ascending=False)
        
        print("Top 10 teams scoring first inning runs:")
        print(total_off.head(10).round(3))
        print()
        
        print("=" * 70)
        print("TEAM ANALYSIS - FIRST INNING PITCHING")
        print("=" * 70)
        
        # Home pitching (allowing runs to away team)
        home_pitch = self.df.groupby('home_team').agg({
            'first_inning_runs_away': ['sum', 'count', 'mean']
        })
        
        # Away pitching (allowing runs to home team)
        away_pitch = self.df.groupby('away_team').agg({
            'first_inning_runs_home': ['sum', 'count', 'mean']
        })
        
        home_pitch.columns = ['Runs Allowed', 'Games', 'Avg']
        away_pitch.columns = ['Runs Allowed', 'Games', 'Avg']
        
        total_pitch = pd.concat([home_pitch, away_pitch]).groupby(level=0).sum()
        total_pitch['Avg'] = total_pitch['Runs Allowed'] / total_pitch['Games']
        total_pitch = total_pitch.sort_values('Avg', ascending=True)  # Lower is better
        
        print("Top 10 teams preventing first inning runs:")
        print(total_pitch.head(10).round(3))
        print()
    
    def analyze_home_vs_away(self):
        """Compare first inning scoring at home vs away"""
        print("=" * 70)
        print("HOME VS AWAY FIRST INNING SCORING")
        print("=" * 70)
        
        home_runs = self.df['first_inning_runs_home'].sum()
        away_runs = self.df['first_inning_runs_away'].sum()
        total_games = len(self.df)
        
        print(f"Home teams first inning runs: {home_runs} ({home_runs/total_games:.3f} per game)")
        print(f"Away teams first inning runs: {away_runs} ({away_runs/total_games:.3f} per game)")
        
        home_scored = (self.df['first_inning_runs_home'] > 0).sum()
        away_scored = (self.df['first_inning_runs_away'] > 0).sum()
        
        print(f"\nHome teams scored in first: {home_scored} games ({home_scored/total_games*100:.1f}%)")
        print(f"Away teams scored in first: {away_scored} games ({away_scored/total_games*100:.1f}%)")
        print()
    
    def key_insights(self):
        """Print key actionable insights for the model"""
        print("=" * 70)
        print("KEY INSIGHTS FOR MODEL BUILDING")
        print("=" * 70)
        
        total = len(self.df)
        base_rate = (self.df['first_inning_run_scored'].sum() / total * 100)
        
        print(f"1. BASELINE: {base_rate:.1f}% of games have first inning runs")
        print("   → This is your benchmark to beat")
        
        # Temperature insight
        temp_data = self.df.dropna(subset=['temperature'])
        if len(temp_data) > 0:
            hot_games = temp_data[temp_data['temperature'] > 75]
            cold_games = temp_data[temp_data['temperature'] < 60]
            
            if len(hot_games) > 0 and len(cold_games) > 0:
                hot_rate = hot_games['first_inning_run_scored'].mean() * 100
                cold_rate = cold_games['first_inning_run_scored'].mean() * 100
                print(f"\n2. TEMPERATURE MATTERS:")
                print(f"   → Hot games (>75°F): {hot_rate:.1f}% have first inning runs")
                print(f"   → Cold games (<60°F): {cold_rate:.1f}% have first inning runs")
                print(f"   → Difference: {hot_rate - cold_rate:+.1f} percentage points")
        
        # Venue insight
        venue_var = self.df.groupby('venue')['first_inning_run_scored'].mean().std() * 100
        print(f"\n3. PARK FACTORS:")
        print(f"   → Standard deviation across parks: {venue_var:.1f}%")
        print("   → Some parks are significantly more/less favorable")
        
        print("\n4. DATA NEEDED NEXT:")
        print("   ✓ Starting pitcher first inning ERA/performance")
        print("   ✓ Top-of-order hitter quality (1-3 batters)")
        print("   ✓ Batter vs pitcher historical matchups")
        print("   ✓ Recent form (last 7-14 days)")
        
        print("\n5. MODEL APPROACH:")
        print("   → Start with logistic regression (simple, interpretable)")
        print("   → Features: temp, park, pitcher quality, lineup quality")
        print("   → Goal: Beat baseline rate with consistent edge")
        print("=" * 70)
        print()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Analyze MLB first inning data')
    parser.add_argument('--data', type=str, required=True, 
                       help='Path to CSV data file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data):
        print(f"Error: File {args.data} not found")
        return
    
    analyzer = FirstInningAnalyzer(args.data)
    
    # Run all analyses
    analyzer.basic_stats()
    analyzer.analyze_by_temperature()
    analyzer.analyze_by_venue()
    analyzer.analyze_by_team()
    analyzer.analyze_home_vs_away()
    analyzer.key_insights()
    
    print("✅ Analysis complete!")
    print("\nNext step: Collect pitcher and batter data to enhance the model")


if __name__ == "__main__":
    main()
