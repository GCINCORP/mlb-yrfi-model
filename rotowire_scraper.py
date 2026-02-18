"""
RotoWire Free Scraper
=====================
Scrapes publicly available data from RotoWire:
- Daily confirmed MLB lineups
- Hot/cold indicators for batters and pitchers

When ROTOWIRE_PREMIUM = True (future upgrade):
- Full batter vs pitcher matchup stats
- Platoon splits
- Detailed pitcher analytics

Usage:
    python rotowire_scraper.py --date 2026-04-15
    python rotowire_scraper.py  # defaults to today
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime, date
import argparse

# ============================================================
# UPGRADE SWITCH - Change to True when you subscribe ($8.99/mo)
# ============================================================
ROTOWIRE_PREMIUM = False
ROTOWIRE_USERNAME = ""  # Add when subscribing
ROTOWIRE_PASSWORD = ""  # Add when subscribing
# ============================================================

class RotoWireScraper:
    """Scrapes RotoWire for lineup and hot/cold data"""
    
    def __init__(self):
        self.base_url = "https://www.rotowire.com/baseball"
        self.data_dir = "mlb_data/rotowire"
        os.makedirs(self.data_dir, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    # ===========================================================
    # FREE TIER METHODS
    # ===========================================================
    
    def get_daily_lineups(self, game_date: str = None) -> dict:
        """
        Scrape confirmed lineups from RotoWire free daily lineups page
        
        Returns dict of:
        {
          "ATL": {
            "confirmed": True,
            "lineup": [
              {"order": 1, "name": "Ronald Acuna Jr.", "position": "CF"},
              {"order": 2, "name": "Ozzie Albies", "position": "2B"},
              ...top 6...
            ],
            "pitcher": "Spencer Strider"
          },
          ...
        }
        """
        if game_date is None:
            game_date = date.today().strftime("%Y-%m-%d")
        
        print(f"Fetching RotoWire lineups for {game_date}...")
        
        url = f"{self.base_url}/daily-lineups.php"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            lineups = {}
            
            # Find all lineup cards on the page
            lineup_cards = soup.find_all('div', class_='lineup')
            
            for card in lineup_cards:
                try:
                    # Get team abbreviation
                    team_elem = card.find('div', class_='lineup__team')
                    if not team_elem:
                        continue
                    
                    # Get home and away teams
                    teams = card.find_all('div', class_='lineup__team-name')
                    if len(teams) < 2:
                        continue
                    
                    away_team = teams[0].get_text(strip=True)
                    home_team = teams[1].get_text(strip=True)
                    
                    # Check if lineup is confirmed
                    confirmed_badge = card.find('span', class_='lineup__confirmed')
                    is_confirmed = confirmed_badge is not None
                    
                    # Get pitcher names
                    pitchers = card.find_all('div', class_='lineup__pitcher')
                    away_pitcher = pitchers[0].get_text(strip=True) if len(pitchers) > 0 else "TBD"
                    home_pitcher = pitchers[1].get_text(strip=True) if len(pitchers) > 1 else "TBD"
                    
                    # Get batting orders (top 6 for each team)
                    away_batters = []
                    home_batters = []
                    
                    lineup_lists = card.find_all('ul', class_='lineup__list')
                    
                    if len(lineup_lists) >= 2:
                        # Away team batters
                        for i, li in enumerate(lineup_lists[0].find_all('li')[:6]):
                            player_link = li.find('a')
                            if player_link:
                                away_batters.append({
                                    "order": i + 1,
                                    "name": player_link.get_text(strip=True),
                                    "position": li.find('span', class_='lineup__pos').get_text(strip=True) if li.find('span', class_='lineup__pos') else "?"
                                })
                        
                        # Home team batters
                        for i, li in enumerate(lineup_lists[1].find_all('li')[:6]):
                            player_link = li.find('a')
                            if player_link:
                                home_batters.append({
                                    "order": i + 1,
                                    "name": player_link.get_text(strip=True),
                                    "position": li.find('span', class_='lineup__pos').get_text(strip=True) if li.find('span', class_='lineup__pos') else "?"
                                })
                    
                    lineups[away_team] = {
                        "confirmed": is_confirmed,
                        "lineup": away_batters,
                        "pitcher": away_pitcher,
                        "home_away": "away"
                    }
                    
                    lineups[home_team] = {
                        "confirmed": is_confirmed,
                        "lineup": home_batters,
                        "pitcher": home_pitcher,
                        "home_away": "home"
                    }
                    
                except Exception as e:
                    continue
            
            # Save to file
            output_file = f"{self.data_dir}/lineups_{game_date}.json"
            with open(output_file, 'w') as f:
                json.dump(lineups, f, indent=2)
            
            confirmed_count = sum(1 for t in lineups.values() if t.get('confirmed'))
            print(f"✅ Found {len(lineups)} teams ({confirmed_count} confirmed lineups)")
            print(f"💾 Saved to {output_file}")
            
            return lineups
            
        except Exception as e:
            print(f"❌ Error fetching lineups: {e}")
            print("Falling back to empty lineups dict")
            return {}
    
    def get_hot_cold_indicators(self, game_date: str = None) -> dict:
        """
        Scrape hot/cold indicators from RotoWire matchups page
        
        Returns dict of:
        {
          "Ronald Acuna Jr.": {"status": "hot", "detail": "5-for-10 last 3 games"},
          "Spencer Strider": {"status": "cold", "detail": "Allowed 8 runs last 2 starts"},
          ...
        }
        """
        if game_date is None:
            game_date = date.today().strftime("%Y-%m-%d")
        
        print(f"Fetching RotoWire hot/cold indicators for {game_date}...")
        
        url = f"{self.base_url}/player-news.php"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            indicators = {}
            
            # Find hot/cold news items
            news_items = soup.find_all('div', class_='news-update')
            
            for item in news_items:
                try:
                    player_elem = item.find('a', class_='news-update__player-link')
                    if not player_elem:
                        continue
                    
                    player_name = player_elem.get_text(strip=True)
                    
                    # Check for hot/cold badges
                    hot_badge = item.find('span', class_='hot') or item.find('span', class_='trending-up')
                    cold_badge = item.find('span', class_='cold') or item.find('span', class_='trending-down')
                    
                    detail_elem = item.find('p', class_='news-update__analysis')
                    detail = detail_elem.get_text(strip=True)[:100] if detail_elem else ""
                    
                    if hot_badge:
                        indicators[player_name] = {"status": "hot", "detail": detail}
                    elif cold_badge:
                        indicators[player_name] = {"status": "cold", "detail": detail}
                        
                except Exception:
                    continue
            
            # Save to file
            output_file = f"{self.data_dir}/hot_cold_{game_date}.json"
            with open(output_file, 'w') as f:
                json.dump(indicators, f, indent=2)
            
            hot_count = sum(1 for p in indicators.values() if p['status'] == 'hot')
            cold_count = sum(1 for p in indicators.values() if p['status'] == 'cold')
            print(f"✅ Found {hot_count} hot, {cold_count} cold players")
            print(f"💾 Saved to {output_file}")
            
            return indicators
            
        except Exception as e:
            print(f"❌ Error fetching hot/cold data: {e}")
            return {}
    
    def get_streak_score(self, player_name: str, indicators: dict) -> float:
        """
        Convert hot/cold indicator to numeric score for model
        
        Returns:
            1.15 = hot (15% boost)
            1.00 = neutral
            0.85 = cold (15% penalty)
        """
        if player_name in indicators:
            status = indicators[player_name]['status']
            if status == 'hot':
                return 1.15
            elif status == 'cold':
                return 0.85
        return 1.00
    
    # ===========================================================
    # PREMIUM TIER METHODS (Future - flip ROTOWIRE_PREMIUM = True)
    # ===========================================================
    
    def get_matchup_stats(self, home_team: str, away_team: str) -> dict:
        """
        PREMIUM: Full batter vs pitcher matchup data
        Requires RotoWire subscription ($8.99/month)
        
        Returns career and recent batter vs pitcher stats
        for top 6 batters on each team
        """
        if not ROTOWIRE_PREMIUM:
            print("⚠️  RotoWire Premium required for matchup stats")
            print("    Set ROTOWIRE_PREMIUM = True and add credentials")
            print("    Returning empty matchup data")
            return {}
        
        # Premium implementation goes here when subscribed
        # Will scrape full matchup tables from rotowire.com/baseball/matchups
        print("🔮 RotoWire Premium matchup data coming soon...")
        return {}
    
    def get_platoon_splits(self, team: str, pitcher_hand: str) -> dict:
        """
        PREMIUM: How team performs vs LHP or RHP
        Requires RotoWire subscription
        """
        if not ROTOWIRE_PREMIUM:
            return {}
        
        # Premium implementation
        print("🔮 RotoWire Premium platoon splits coming soon...")
        return {}
    
    def get_injury_report(self) -> dict:
        """
        PREMIUM: Full injury context and roster moves
        Requires RotoWire subscription
        """
        if not ROTOWIRE_PREMIUM:
            return {}
        
        print("🔮 RotoWire Premium injury report coming soon...")
        return {}
    
    # ===========================================================
    # HELPER METHODS
    # ===========================================================
    
    def load_lineups(self, game_date: str) -> dict:
        """Load saved lineups from file"""
        filepath = f"{self.data_dir}/lineups_{game_date}.json"
        if os.path.exists(filepath):
            with open(filepath) as f:
                return json.load(f)
        return {}
    
    def load_hot_cold(self, game_date: str) -> dict:
        """Load saved hot/cold data from file"""
        filepath = f"{self.data_dir}/hot_cold_{game_date}.json"
        if os.path.exists(filepath):
            with open(filepath) as f:
                return json.load(f)
        return {}
    
    def get_all_data(self, game_date: str = None) -> dict:
        """
        Get all available RotoWire data for a given date
        Called automatically each morning by daily scraper
        """
        if game_date is None:
            game_date = date.today().strftime("%Y-%m-%d")
        
        print("=" * 60)
        print(f"ROTOWIRE DATA COLLECTION - {game_date}")
        print("=" * 60)
        
        lineups = self.get_daily_lineups(game_date)
        time.sleep(2)  # Be respectful - don't hammer their servers
        hot_cold = self.get_hot_cold_indicators(game_date)
        
        if ROTOWIRE_PREMIUM:
            print("\n🔮 RotoWire Premium features active!")
            # Premium calls would go here
        else:
            print("\n💡 TIP: Subscribe to RotoWire ($8.99/mo) and set")
            print("   ROTOWIRE_PREMIUM = True to unlock matchup stats")
            print("   and platoon splits for improved accuracy!")
        
        return {
            "lineups": lineups,
            "hot_cold": hot_cold,
            "premium_active": ROTOWIRE_PREMIUM,
            "date": game_date
        }


def main():
    parser = argparse.ArgumentParser(description='Scrape RotoWire data')
    parser.add_argument('--date', type=str, help='Date (YYYY-MM-DD), defaults to today')
    parser.add_argument('--lineups-only', action='store_true', help='Only fetch lineups')
    parser.add_argument('--hot-cold-only', action='store_true', help='Only fetch hot/cold')
    args = parser.parse_args()
    
    scraper = RotoWireScraper()
    
    if args.lineups_only:
        scraper.get_daily_lineups(args.date)
    elif args.hot_cold_only:
        scraper.get_hot_cold_indicators(args.date)
    else:
        data = scraper.get_all_data(args.date)
        print(f"\n✅ RotoWire data collection complete!")
        print(f"   Lineups: {len(data['lineups'])} teams")
        print(f"   Hot/Cold: {len(data['hot_cold'])} players flagged")
        print(f"   Premium: {'Active ✅' if data['premium_active'] else 'Not active (upgrade anytime)'}")


if __name__ == "__main__":
    main()
