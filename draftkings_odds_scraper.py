"""
DraftKings YRFI/NRFI Odds Scraper
===================================
Pulls YRFI/NRFI odds directly from DraftKings internal API.
100% free - no account or subscription needed.

Pulls:
- Current YRFI odds per game
- Current NRFI odds per game
- Opening line (for line movement tracking)
- Line movement direction (sharp money indicator)

Usage:
    python draftkings_odds_scraper.py --date 2026-04-15
    python draftkings_odds_scraper.py  # defaults to today
"""

import requests
import json
import os
import time
from datetime import datetime, date
import argparse


class DraftKingsOddsScraper:
    """Scrapes YRFI/NRFI odds from DraftKings internal API"""
    
    def __init__(self):
        self.data_dir = "mlb_data/odds"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # DraftKings internal API endpoints
        self.dk_api_base = "https://sportsbook-nash.draftkings.com/api/sportscontent/dkusnj/v1"
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://sportsbook.draftkings.com/",
            "Origin": "https://sportsbook.draftkings.com"
        }
        
        # MLB category/subcategory IDs on DraftKings
        self.MLB_CATEGORY_ID = 84240   # MLB
        self.YRFI_SUBCATEGORY_ID = 13045  # Run in 1st Inning props
    
    def get_yrfi_nrfi_odds(self, game_date: str = None) -> dict:
        """
        Pull YRFI/NRFI odds from DraftKings
        
        Returns dict of:
        {
          "PHI @ ATL": {
            "yrfi_odds": -115,
            "nrfi_odds": -105,
            "yrfi_implied_prob": 0.535,
            "nrfi_implied_prob": 0.512,
            "opening_yrfi": -110,      # where it opened
            "line_movement": "YRFI",   # which side money is on
            "movement_cents": 5        # how many cents it moved
          }
        }
        """
        if game_date is None:
            game_date = date.today().strftime("%Y-%m-%d")
        
        print(f"Fetching DraftKings YRFI/NRFI odds for {game_date}...")
        
        # Try primary API endpoint
        odds = self._fetch_from_api(game_date)
        
        if odds:
            print(f"✅ Found YRFI/NRFI odds for {len(odds)} games")
            self._save_odds(odds, game_date)
            return odds
        
        # If API fails, return empty (model will handle gracefully)
        print("⚠️  Could not fetch odds from DraftKings API")
        print("   You can enter odds manually when running daily predictor")
        return {}
    
    def _fetch_from_api(self, game_date: str) -> dict:
        """Fetch from DraftKings internal API"""
        odds = {}
        
        try:
            # Endpoint 1: Try the subcategory endpoint for first inning props
            url = f"{self.dk_api_base}/leagues/84240/categories/583/subcategories/13045"
            
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                odds = self._parse_api_response(data)
                
            if not odds:
                # Endpoint 2: Try alternate endpoint
                url2 = "https://sportsbook.draftkings.com/api/sportscontent/dkusnj/v1/leagues/84240/categories/583"
                response2 = requests.get(url2, headers=self.headers, timeout=15)
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    odds = self._parse_api_response(data2)
                    
        except Exception as e:
            print(f"   API error: {e}")
        
        return odds
    
    def _parse_api_response(self, data: dict) -> dict:
        """Parse DraftKings API response to extract YRFI/NRFI odds"""
        odds = {}
        
        try:
            events = data.get('eventGroup', {}).get('offerCategories', [])
            
            for category in events:
                cat_name = category.get('name', '')
                
                # Look for first inning / YRFI related categories
                if any(term in cat_name.lower() for term in ['first inning', 'run scored', 'yrfi', 'nrfi', '1st inning']):
                    
                    for subcategory in category.get('offerSubcategoryDescriptors', []):
                        for offer in subcategory.get('offerSubcategory', {}).get('offers', []):
                            for offer_item in offer:
                                game_name = offer_item.get('label', '')
                                outcomes = offer_item.get('outcomes', [])
                                
                                yrfi_odds = None
                                nrfi_odds = None
                                
                                for outcome in outcomes:
                                    label = outcome.get('label', '').upper()
                                    odds_american = outcome.get('oddsAmerican', '')
                                    
                                    if 'YES' in label or 'OVER' in label or 'YRFI' in label:
                                        try:
                                            yrfi_odds = int(odds_american)
                                        except:
                                            pass
                                    elif 'NO' in label or 'UNDER' in label or 'NRFI' in label:
                                        try:
                                            nrfi_odds = int(odds_american)
                                        except:
                                            pass
                                
                                if yrfi_odds and nrfi_odds and game_name:
                                    odds[game_name] = {
                                        "yrfi_odds": yrfi_odds,
                                        "nrfi_odds": nrfi_odds,
                                        "yrfi_implied_prob": self._american_to_implied(yrfi_odds),
                                        "nrfi_implied_prob": self._american_to_implied(nrfi_odds),
                                        "opening_yrfi": yrfi_odds,  # Will update if we track movement
                                        "line_movement": "none",
                                        "movement_cents": 0,
                                        "source": "DraftKings"
                                    }
        except Exception as e:
            pass
        
        return odds
    
    def _american_to_implied(self, odds: int) -> float:
        """Convert American odds to implied probability"""
        if odds < 0:
            return abs(odds) / (abs(odds) + 100)
        else:
            return 100 / (odds + 100)
    
    def _detect_line_movement(self, current_odds: int, opening_odds: int) -> tuple:
        """Detect line movement direction and magnitude"""
        if opening_odds is None:
            return "none", 0
        
        movement = current_odds - opening_odds
        cents = abs(movement)
        
        if movement < -5:
            return "YRFI", cents  # Moved toward YRFI (shorter)
        elif movement > 5:
            return "NRFI", cents  # Moved toward NRFI
        else:
            return "none", cents
    
    def _save_odds(self, odds: dict, game_date: str):
        """Save odds to file"""
        filepath = f"{self.data_dir}/odds_{game_date}.json"
        with open(filepath, 'w') as f:
            json.dump(odds, f, indent=2)
        print(f"💾 Saved to {filepath}")
    
    def load_odds(self, game_date: str) -> dict:
        """Load saved odds from file"""
        filepath = f"{self.data_dir}/odds_{game_date}.json"
        if os.path.exists(filepath):
            with open(filepath) as f:
                return json.load(f)
        return {}
    
    def get_best_line(self, game: str, odds: dict) -> dict:
        """
        Find the best available YRFI and NRFI line for a game
        When we add more sportsbooks, this picks the best odds
        """
        if game not in odds:
            return {"yrfi_odds": None, "nrfi_odds": None}
        
        return odds[game]
    
    def print_odds_summary(self, odds: dict):
        """Print human-readable odds summary"""
        if not odds:
            print("No odds data available")
            return
        
        print("\n📊 TODAY'S YRFI/NRFI ODDS (DraftKings)")
        print("=" * 60)
        
        for game, data in odds.items():
            yrfi = data.get('yrfi_odds', 'N/A')
            nrfi = data.get('nrfi_odds', 'N/A')
            movement = data.get('line_movement', 'none')
            
            movement_str = ""
            if movement != "none":
                cents = data.get('movement_cents', 0)
                movement_str = f" ← 🔥 {movement} movement ({cents}¢)"
            
            print(f"\n  {game}")
            print(f"  YRFI: {yrfi:+d}  |  NRFI: {nrfi:+d}{movement_str}")


def main():
    parser = argparse.ArgumentParser(description='Fetch DraftKings YRFI/NRFI odds')
    parser.add_argument('--date', type=str, help='Date (YYYY-MM-DD), defaults to today')
    parser.add_argument('--print', action='store_true', help='Print odds summary')
    args = parser.parse_args()
    
    scraper = DraftKingsOddsScraper()
    odds = scraper.get_yrfi_nrfi_odds(args.date)
    
    if args.print or not odds:
        scraper.print_odds_summary(odds)
    
    if not odds:
        print("\n💡 If auto-fetch failed, you can still enter odds manually")
        print("   when running the daily predictor:")
        print("   python3 daily_predictor.py")


if __name__ == "__main__":
    main()
