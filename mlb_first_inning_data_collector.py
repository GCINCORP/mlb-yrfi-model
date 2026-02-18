"""
MLB First Inning Run Prediction - Data Collection System
=========================================================

This script collects historical data needed to predict whether the first inning
will have a run scored (yes/no).

Data sources:
- Baseball Reference: Historical game data and first inning scoring
- MLB Stats API: Current season data, rosters, schedules
- Weather APIs: Temperature and conditions for game time

Usage:
    python mlb_first_inning_data_collector.py --season 2024 --team ATL
"""

import requests
import json
import time
from datetime import datetime, timedelta
import csv
import os
from typing import Dict, List, Optional
import argparse

class MLBDataCollector:
    """Collects MLB data for first inning run prediction model"""
    
    def __init__(self):
        self.mlb_api_base = "https://statsapi.mlb.com/api/v1"
        self.mlb_api_game = "https://statsapi.mlb.com/api/v1.1"  # v1.1 for game feed
        self.data_dir = "mlb_data"
        self.create_directories()
        
    def create_directories(self):
        """Create necessary directories for data storage"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f"{self.data_dir}/games", exist_ok=True)
        os.makedirs(f"{self.data_dir}/pitchers", exist_ok=True)
        os.makedirs(f"{self.data_dir}/teams", exist_ok=True)
        os.makedirs(f"{self.data_dir}/weather", exist_ok=True)
        
    def get_schedule(self, season: int, team_id: Optional[int] = None) -> List[Dict]:
        """
        Get season schedule from MLB Stats API
        
        Args:
            season: Year (e.g., 2024)
            team_id: Optional team ID to filter (e.g., 144 for Braves)
            
        Returns:
            List of game dictionaries
        """
        print(f"Fetching {season} schedule...")
        
        # Get season dates
        start_date = f"{season}-03-20"  # Spring games start
        end_date = f"{season}-10-31"    # End of regular season
        
        url = f"{self.mlb_api_base}/schedule"
        params = {
            "sportId": 1,  # MLB
            "startDate": start_date,
            "endDate": end_date,
            "gameType": "R"  # Regular season only
        }
        
        if team_id:
            params["teamId"] = team_id
            
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            games = []
            for date_entry in data.get("dates", []):
                for game in date_entry.get("games", []):
                    games.append({
                        "game_id": game["gamePk"],
                        "date": date_entry["date"],
                        "home_team": game["teams"]["home"]["team"]["name"],
                        "home_id": game["teams"]["home"]["team"]["id"],
                        "away_team": game["teams"]["away"]["team"]["name"],
                        "away_id": game["teams"]["away"]["team"]["id"],
                        "venue": game["venue"]["name"],
                        "game_type": game["gameType"],
                        "status": game["status"]["detailedState"]
                    })
                    
            print(f"Found {len(games)} games")
            return games
            
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return []
    
    def get_game_data(self, game_id: int) -> Dict:
        """
        Get detailed game data including play-by-play for first inning analysis
        
        Args:
            game_id: MLB game ID
            
        Returns:
            Dictionary with game details and first inning data
        """
        url = f"{self.mlb_api_game}/game/{game_id}/feed/live"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            game_data = data.get("gameData", {})
            live_data = data.get("liveData", {})
            
            # Extract first inning data
            first_inning_runs = self.extract_first_inning_runs(live_data)
            
            return {
                "game_id": game_id,
                "date": game_data.get("datetime", {}).get("officialDate"),
                "venue": game_data.get("venue", {}).get("name"),
                "temperature": game_data.get("weather", {}).get("temp"),
                "wind": game_data.get("weather", {}).get("wind"),
                "condition": game_data.get("weather", {}).get("condition"),
                "home_team": game_data.get("teams", {}).get("home", {}).get("name"),
                "away_team": game_data.get("teams", {}).get("away", {}).get("name"),
                "home_pitcher": self.get_starter_name(live_data, "home"),   # Fixed: was home_starter
                "away_pitcher": self.get_starter_name(live_data, "away"),   # Fixed: was away_starter
                "first_inning_runs_home": first_inning_runs["home"],
                "first_inning_runs_away": first_inning_runs["away"],
                "first_inning_run_scored": first_inning_runs["total"] > 0,
                "final_score_home": live_data.get("linescore", {}).get("teams", {}).get("home", {}).get("runs"),
                "final_score_away": live_data.get("linescore", {}).get("teams", {}).get("away", {}).get("runs")
            }
            
        except Exception as e:
            print(f"Error fetching game {game_id}: {e}")
            return {}
    
    def extract_first_inning_runs(self, live_data: Dict) -> Dict:
        """Extract runs scored in first inning from linescore"""
        try:
            innings = live_data.get("linescore", {}).get("innings", [])
            if innings and len(innings) > 0:
                first_inning = innings[0]
                home_runs = first_inning.get("home", {}).get("runs", 0)
                away_runs = first_inning.get("away", {}).get("runs", 0)
                return {
                    "home": home_runs,
                    "away": away_runs,
                    "total": home_runs + away_runs
                }
        except:
            pass
        
        return {"home": 0, "away": 0, "total": 0}
    
    def get_starter_name(self, live_data: Dict, home_away: str) -> str:
        """Extract starting pitcher name from game data"""
        try:
            boxscore = live_data.get("boxscore", {})
            teams = boxscore.get("teams", {})
            pitchers = teams.get(home_away, {}).get("pitchers", [])
            
            if pitchers:
                # First pitcher listed is usually the starter
                pitcher_id = pitchers[0]
                players = boxscore.get("teams", {}).get(home_away, {}).get("players", {})
                player_key = f"ID{pitcher_id}"
                return players.get(player_key, {}).get("person", {}).get("fullName", "Unknown")
        except:
            pass
        
        return "Unknown"
    
    def get_pitcher_stats(self, pitcher_name: str, season: int) -> Dict:
        """
        Get pitcher's first inning statistics
        
        Note: This is a placeholder - would need to aggregate game-by-game data
        """
        # This would require building from individual game data
        return {
            "name": pitcher_name,
            "season": season,
            "first_inning_era": None,  # To be calculated
            "first_inning_runs_allowed": None
        }
    
    def save_to_csv(self, games_data: List[Dict], filename: str):
        """Save collected data to CSV file"""
        if not games_data:
            print("No data to save")
            return
            
        filepath = f"{self.data_dir}/{filename}"
        
        # Get all unique keys from all games
        all_keys = set()
        for game in games_data:
            all_keys.update(game.keys())
        
        fieldnames = sorted(all_keys)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(games_data)
            
        print(f"Saved {len(games_data)} games to {filepath}")
    
    def collect_season_data(self, season: int, team_id: Optional[int] = None, 
                          max_games: Optional[int] = None):
        """
        Main function to collect all data for a season
        
        Args:
            season: Year to collect
            team_id: Optional team ID to filter
            max_games: Optional limit on number of games (for testing)
        """
        print(f"\n{'='*60}")
        print(f"COLLECTING DATA FOR {season} SEASON")
        print(f"{'='*60}\n")
        
        # Get schedule
        schedule = self.get_schedule(season, team_id)
        
        if max_games:
            schedule = schedule[:max_games]
        
        # Collect game-by-game data
        games_data = []
        total = len(schedule)
        
        for i, game_info in enumerate(schedule, 1):
            if game_info["status"] == "Final":  # Only get completed games
                print(f"[{i}/{total}] Fetching game {game_info['game_id']}...")
                game_data = self.get_game_data(game_info["game_id"])
                
                if game_data:
                    games_data.append(game_data)
                
                # Rate limiting - be nice to the API
                time.sleep(0.5)
        
        # Save data
        filename = f"first_inning_data_{season}"
        if team_id:
            filename += f"_team{team_id}"
        filename += ".csv"
        
        self.save_to_csv(games_data, filename)
        
        # Print summary stats
        self.print_summary(games_data, season)
        
    def print_summary(self, games_data: List[Dict], season: int):
        """Print summary statistics"""
        if not games_data:
            return
            
        total_games = len(games_data)
        games_with_first_inning_run = sum(1 for g in games_data if g.get("first_inning_run_scored"))
        pct = (games_with_first_inning_run / total_games * 100) if total_games > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"SUMMARY FOR {season} SEASON")
        print(f"{'='*60}")
        print(f"Total games collected: {total_games}")
        print(f"Games with first inning run: {games_with_first_inning_run}")
        print(f"Percentage: {pct:.1f}%")
        print(f"Games without first inning run: {total_games - games_with_first_inning_run}")
        print(f"{'='*60}\n")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Collect MLB first inning data')
    parser.add_argument('--season', type=int, default=2024, help='Season year (default: 2024)')
    parser.add_argument('--team', type=int, help='Team ID (optional, e.g., 144 for Braves)')
    parser.add_argument('--max-games', type=int, help='Maximum games to collect (for testing)')
    
    args = parser.parse_args()
    
    collector = MLBDataCollector()
    collector.collect_season_data(
        season=args.season,
        team_id=args.team,
        max_games=args.max_games
    )
    
    print("\n✅ Data collection complete!")
    print(f"📁 Data saved in: {collector.data_dir}/")
    print("\nNext steps:")
    print("1. Run this for multiple seasons (2022, 2023, 2024)")
    print("2. Analyze the data to find patterns")
    print("3. Build the prediction model")


if __name__ == "__main__":
    main()
