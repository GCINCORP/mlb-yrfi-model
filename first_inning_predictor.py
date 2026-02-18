"""
MLB First Inning Run Prediction Model
======================================

Machine learning model to predict whether the first inning will have a run scored.

Features:
- Trains on historical data
- Generates predictions for upcoming games
- Identifies value bets by comparing to odds
- Tracks performance over time

Usage:
    # Train the model
    python first_inning_predictor.py --train --data mlb_data/first_inning_data_2024.csv
    
    # Make predictions for today
    python first_inning_predictor.py --predict --date 2024-04-15
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
import pickle
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
import argparse


class FirstInningPredictor:
    """Predicts first inning runs and identifies value bets"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.team_stats = None  # Store team stats
        self.pitcher_stats = None  # Store pitcher stats
        self.model_dir = "models"
        self.predictions_dir = "predictions"
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.predictions_dir, exist_ok=True)
        
    def prepare_features(self, df: pd.DataFrame, historical_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Engineer features from raw data
        
        Features to create:
        - Team offensive rates (actual first inning scoring)
        - Pitcher defensive rates (actual first inning runs allowed)
        - Pitcher walk rates (BB/9 and first inning walks)
        - Temperature (numerical)
        - Park factor (one-hot encoded)
        - Home vs away
        """
        print("Engineering features...")
        
        # Make a copy to avoid modifying original
        data = df.copy()
        
        # Convert first_inning_run_scored to binary if it's not already
        if 'first_inning_run_scored' in data.columns:
            data['target'] = data['first_inning_run_scored'].astype(int)
        
        # Calculate team and pitcher stats from historical data
        if historical_data is not None:
            print("Calculating team and pitcher statistics from historical data...")
            team_stats = self._calculate_team_stats(historical_data)
            pitcher_stats = self._calculate_pitcher_stats(historical_data)
            
            # Merge team offensive stats
            data = data.merge(
                team_stats[['team', 'home_1st_inn_score_rate', 'away_1st_inn_score_rate']],
                left_on='home_team',
                right_on='team',
                how='left'
            ).drop('team', axis=1)
            data.rename(columns={
                'home_1st_inn_score_rate': 'home_team_off_rate',
                'away_1st_inn_score_rate': 'home_team_off_rate_away'
            }, inplace=True)
            
            data = data.merge(
                team_stats[['team', 'home_1st_inn_score_rate', 'away_1st_inn_score_rate']],
                left_on='away_team',
                right_on='team',
                how='left'
            ).drop('team', axis=1)
            data.rename(columns={
                'home_1st_inn_score_rate': 'away_team_off_rate_home',
                'away_1st_inn_score_rate': 'away_team_off_rate'
            }, inplace=True)
            
            # Merge pitcher stats (expanded)
            # Check if pitcher columns exist
            if 'home_pitcher' in data.columns and len(pitcher_stats) > 0:
                data = data.merge(
                    pitcher_stats,
                    left_on='home_pitcher',
                    right_on='pitcher',
                    how='left',
                    suffixes=('', '_home_p')
                )
                if 'pitcher' in data.columns:
                    data = data.drop('pitcher', axis=1)
            else:
                # Create placeholder columns if no pitcher data
                for col in ['1st_inn_run_rate', 'walk_rate', 'strikeout_rate', 'hr_rate', 'gb_rate', '1st_inn_walk_rate', '1st_inn_hr_rate']:
                    data[f'home_{col}'] = 0.42 if '1st_inn_run_rate' in col else (3.0 if 'walk' in col else 8.5)
            data.rename(columns={
                '1st_inn_run_rate': 'home_pitcher_1st_inn_rate',
                'walk_rate': 'home_pitcher_walk_rate',
                'strikeout_rate': 'home_pitcher_k_rate',
                'hr_rate': 'home_pitcher_hr_rate',
                'gb_rate': 'home_pitcher_gb_rate',
                '1st_inn_walk_rate': 'home_pitcher_1st_inn_walk_rate',
                '1st_inn_hr_rate': 'home_pitcher_1st_inn_hr_rate'
            }, inplace=True)
            
            data = data.merge(
                pitcher_stats,
                left_on='away_pitcher',
                right_on='pitcher',
                how='left',
                suffixes=('', '_away_p')
            ).drop('pitcher', axis=1)
            data.rename(columns={
                '1st_inn_run_rate': 'away_pitcher_1st_inn_rate',
                'walk_rate': 'away_pitcher_walk_rate',
                'strikeout_rate': 'away_pitcher_k_rate',
                'hr_rate': 'away_pitcher_hr_rate',
                'gb_rate': 'away_pitcher_gb_rate',
                '1st_inn_walk_rate': 'away_pitcher_1st_inn_walk_rate',
                '1st_inn_hr_rate': 'away_pitcher_1st_inn_hr_rate'
            }, inplace=True)
            
            # Calculate lineup quality for both teams
            print("Calculating lineup quality metrics...")
            
            # Home team lineup (batting in bottom of 1st)
            for idx, row in data.iterrows():
                home_lineup = self._calculate_lineup_quality(row['home_team'], historical_data, 'home')
                for key, value in home_lineup.items():
                    data.at[idx, f'home_{key}'] = value
                
                away_lineup = self._calculate_lineup_quality(row['away_team'], historical_data, 'away')
                for key, value in away_lineup.items():
                    data.at[idx, f'away_{key}'] = value
            
            # Fill missing pitcher values with league averages
            pitcher_features = [
                'home_pitcher_1st_inn_rate', 'away_pitcher_1st_inn_rate',
                'home_pitcher_walk_rate', 'away_pitcher_walk_rate',
                'home_pitcher_k_rate', 'away_pitcher_k_rate',
                'home_pitcher_hr_rate', 'away_pitcher_hr_rate',
                'home_pitcher_gb_rate', 'away_pitcher_gb_rate',
                'home_pitcher_1st_inn_walk_rate', 'away_pitcher_1st_inn_walk_rate',
                'home_pitcher_1st_inn_hr_rate', 'away_pitcher_1st_inn_hr_rate'
            ]
            
            league_avg_pitcher = {
                'home_pitcher_1st_inn_rate': 0.42,
                'away_pitcher_1st_inn_rate': 0.42,
                'home_pitcher_walk_rate': 3.0,
                'away_pitcher_walk_rate': 3.0,
                'home_pitcher_k_rate': 8.5,
                'away_pitcher_k_rate': 8.5,
                'home_pitcher_hr_rate': 1.2,
                'away_pitcher_hr_rate': 1.2,
                'home_pitcher_gb_rate': 0.45,
                'away_pitcher_gb_rate': 0.45,
                'home_pitcher_1st_inn_walk_rate': 0.35,
                'away_pitcher_1st_inn_walk_rate': 0.35,
                'home_pitcher_1st_inn_hr_rate': 0.11,
                'away_pitcher_1st_inn_hr_rate': 0.11
            }
            
            for feat in pitcher_features:
                if feat in data.columns:
                    data[feat] = data[feat].fillna(league_avg_pitcher[feat])
        else:
            # Use league average placeholders if no historical data
            print("WARNING: No historical data provided. Using league averages.")
            data['home_team_off_rate'] = 0.45
            data['away_team_off_rate'] = 0.42
            data['home_pitcher_1st_inn_rate'] = 0.42
            data['away_pitcher_1st_inn_rate'] = 0.42
            data['home_pitcher_walk_rate'] = 3.0
            data['away_pitcher_walk_rate'] = 3.0
            data['home_pitcher_1st_inn_walk_rate'] = 0.35
            data['away_pitcher_1st_inn_walk_rate'] = 0.35
        
        # Temperature (fill missing with median)
        if 'temperature' in data.columns:
            temp_median = data['temperature'].median()
            data['temp'] = data['temperature'].fillna(temp_median)
        else:
            data['temp'] = 72  # Default moderate temperature
        
        # Create temperature bins for non-linear effects
        data['temp_hot'] = (data['temp'] > 80).astype(int)
        data['temp_cold'] = (data['temp'] < 60).astype(int)
        
        # Park factor (encode top venues)
        if 'venue' in data.columns:
            # Get top 10 most common venues
            top_venues = data['venue'].value_counts().head(10).index
            for venue in top_venues:
                data[f'park_{venue.replace(" ", "_")}'] = (data['venue'] == venue).astype(int)
        
        # Wind (if available)
        if 'wind' in data.columns:
            # Extract wind speed from string like "8 mph SW"
            data['wind_speed'] = data['wind'].str.extract(r'(\d+)').astype(float).fillna(8)
            data['high_wind'] = (data['wind_speed'] > 15).astype(int)
        else:
            data['wind_speed'] = 8
            data['high_wind'] = 0
        
        # Time features (if date available)
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data['month'] = data['date'].dt.month
            data['is_summer'] = data['month'].isin([6, 7, 8]).astype(int)
        
        print(f"Created features for {len(data)} games")
        return data
    
    def _calculate_team_stats(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate team offensive rates from historical data
        
        Returns DataFrame with:
        - team: Team name
        - home_1st_inn_score_rate: How often team scores in 1st when home
        - away_1st_inn_score_rate: How often team scores in 1st when away
        """
        teams = []
        
        all_teams = set(historical_data['home_team'].unique()) | set(historical_data['away_team'].unique())
        
        for team in all_teams:
            # Home games
            home_games = historical_data[historical_data['home_team'] == team]
            if len(home_games) > 0:
                home_scored = (home_games['first_inning_runs_home'] > 0).sum()
                home_rate = home_scored / len(home_games)
            else:
                home_rate = 0.45  # Default
            
            # Away games
            away_games = historical_data[historical_data['away_team'] == team]
            if len(away_games) > 0:
                away_scored = (away_games['first_inning_runs_away'] > 0).sum()
                away_rate = away_scored / len(away_games)
            else:
                away_rate = 0.42  # Default
            
            teams.append({
                'team': team,
                'home_1st_inn_score_rate': home_rate,
                'away_1st_inn_score_rate': away_rate,
                'total_games': len(home_games) + len(away_games)
            })
        
        return pd.DataFrame(teams)
    
    def _calculate_pitcher_stats(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate comprehensive pitcher stats from historical data
        
        Returns DataFrame with:
        - pitcher: Pitcher name
        - 1st_inn_run_rate: How often pitcher allows 1st inning run
        - walk_rate: BB/9 rate (estimated from performance)
        - strikeout_rate: K/9 rate (estimated)
        - hr_rate: HR/9 rate (estimated)
        - gb_rate: Ground ball rate (estimated)
        - 1st_inn_walk_rate: How often pitcher walks someone in 1st inning
        - 1st_inn_hr_rate: How often pitcher allows HR in 1st inning
        
        NOTE: Until we parse play-by-play data, K/BB/HR/GB rates are 
        estimated using correlations with first inning performance.
        Real data can be added via Baseball Savant scraper.
        """
        pitchers = []
        
        # Check which column names are used
        home_pitcher_col = 'home_pitcher' if 'home_pitcher' in historical_data.columns else 'home_starter'
        away_pitcher_col = 'away_pitcher' if 'away_pitcher' in historical_data.columns else 'away_starter'
        
        all_pitchers = set(historical_data[home_pitcher_col].unique()) | set(historical_data[away_pitcher_col].unique())
        all_pitchers.discard('Unknown')  # Remove unknowns
        
        for pitcher in all_pitchers:
            # Games where this pitcher started at home
            home_starts = historical_data[historical_data[home_pitcher_col] == pitcher]
            # Games where this pitcher started away
            away_starts = historical_data[historical_data[away_pitcher_col] == pitcher]
            
            total_starts = len(home_starts) + len(away_starts)
            
            if total_starts > 0:
                # Calculate 1st inning runs allowed rate
                home_runs_allowed = (home_starts['first_inning_runs_away'] > 0).sum()
                away_runs_allowed = (away_starts['first_inning_runs_home'] > 0).sum()
                first_inn_run_rate = (home_runs_allowed + away_runs_allowed) / total_starts
                
                # ESTIMATED STATS (using correlations)
                # These are proxies until we get real data from Baseball Savant
                
                # Walk rate: Good pitchers (low run rate) walk less
                # Elite: ~2.0 BB/9, Average: ~3.0, Poor: ~4.0+
                walk_rate = 2.5 + (first_inn_run_rate * 2.5)
                
                # Strikeout rate: Good pitchers (low run rate) strike out more
                # Elite: ~10+ K/9, Average: ~8.5, Poor: ~7.0
                strikeout_rate = 10.0 - (first_inn_run_rate * 4.0)
                
                # HR rate: Pitchers who allow runs give up more homers
                # Elite: ~0.8 HR/9, Average: ~1.2, Poor: ~1.6+
                hr_rate = 0.8 + (first_inn_run_rate * 1.2)
                
                # Ground ball rate: More grounders = fewer runs (generally)
                # Elite GB: ~50-55%, Average: ~45%, Fly ball: ~40%
                gb_rate = 0.52 - (first_inn_run_rate * 0.2)
                
                # First inning specific rates
                first_inn_walk_rate = 0.25 + (first_inn_run_rate * 0.35)
                first_inn_hr_rate = 0.08 + (first_inn_run_rate * 0.15)
                
                pitchers.append({
                    'pitcher': pitcher,
                    '1st_inn_run_rate': first_inn_run_rate,
                    'walk_rate': walk_rate,
                    'strikeout_rate': strikeout_rate,
                    'hr_rate': hr_rate,
                    'gb_rate': gb_rate,
                    '1st_inn_walk_rate': first_inn_walk_rate,
                    '1st_inn_hr_rate': first_inn_hr_rate,
                    'starts': total_starts
                })
        
        return pd.DataFrame(pitchers)
    
    def _calculate_lineup_quality(self, team: str, historical_data: pd.DataFrame, position: str = 'home') -> Dict:
        """
        Calculate weighted lineup quality for top 6 batters
        
        Weighting:
        - Batter 1 (leadoff): 30%
        - Batter 2: 25%
        - Batter 3 (heart): 20%
        - Batter 4 (cleanup): 12.5%
        - Batter 5: 7.5%
        - Batter 6: 5%
        
        Returns composite metrics:
        - weighted_obp: Weighted on-base percentage
        - weighted_slg: Weighted slugging
        - weighted_ops: Weighted OPS
        - weighted_walk_rate: Weighted walk rate (BB%)
        - weighted_iso: Weighted isolated power (SLG - AVG)
        - weighted_1st_inn_performance: Weighted 1st inning production
        - hot_streak_score: Recent performance (last 14 days)
        
        NOTE: This is placeholder/estimated until we have real lineup data
        In production, would fetch actual lineups and calculate real stats
        """
        
        # Batting order weights
        weights = [0.30, 0.25, 0.20, 0.125, 0.075, 0.05]
        
        # Team offensive quality (proxy for lineup quality)
        team_games = historical_data[
            (historical_data['home_team'] == team) | 
            (historical_data['away_team'] == team)
        ]
        
        if len(team_games) == 0:
            # Return league average
            return {
                'weighted_obp': 0.320,
                'weighted_slg': 0.420,
                'weighted_ops': 0.740,
                'weighted_walk_rate': 0.085,
                'weighted_iso': 0.160,
                'weighted_1st_inn_perf': 0.450,
                'hot_streak_score': 0.50
            }
        
        # Calculate team scoring tendency as proxy
        if position == 'home':
            scoring_rate = (team_games[team_games['home_team'] == team]['first_inning_runs_home'] > 0).mean()
        else:
            scoring_rate = (team_games[team_games['away_team'] == team]['first_inning_runs_away'] > 0).mean()
        
        # Estimate lineup quality from team performance
        # Better teams = better top of order
        # These are PROXIES - real implementation would use actual batter stats
        
        base_obp = 0.300 + (scoring_rate * 0.15)  # .300-.345 range
        base_slg = 0.380 + (scoring_rate * 0.25)  # .380-.495 range
        base_walk_rate = 0.075 + (scoring_rate * 0.03)  # .075-.105 range
        base_iso = 0.140 + (scoring_rate * 0.12)  # .140-.200 range
        
        # Recent form (last 20% of games as proxy for "hot streak")
        recent_games = team_games.tail(int(len(team_games) * 0.2))
        if len(recent_games) > 0:
            if position == 'home':
                recent_rate = (recent_games[recent_games['home_team'] == team]['first_inning_runs_home'] > 0).mean()
            else:
                recent_rate = (recent_games[recent_games['away_team'] == team]['first_inning_runs_away'] > 0).mean()
            
            # Hot streak score: recent vs overall
            hot_streak_score = recent_rate / scoring_rate if scoring_rate > 0 else 1.0
            hot_streak_score = max(0.7, min(1.3, hot_streak_score))  # Bound it
        else:
            hot_streak_score = 1.0
        
        return {
            'weighted_obp': base_obp,
            'weighted_slg': base_slg,
            'weighted_ops': base_obp + base_slg,
            'weighted_walk_rate': base_walk_rate,
            'weighted_iso': base_iso,
            'weighted_1st_inn_perf': scoring_rate,
            'hot_streak_score': hot_streak_score
        }
    
    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Get list of feature columns to use for modeling"""
        
        # Base features
        base_features = ['temp', 'temp_hot', 'temp_cold', 'wind_speed', 'high_wind']
        
        # Team offensive features
        team_features = ['home_team_off_rate', 'away_team_off_rate']
        base_features.extend(team_features)
        
        # Pitcher defensive features (EXPANDED)
        pitcher_features = [
            # First inning performance
            'home_pitcher_1st_inn_rate', 'away_pitcher_1st_inn_rate',
            # Walk rates
            'home_pitcher_walk_rate', 'away_pitcher_walk_rate',
            'home_pitcher_1st_inn_walk_rate', 'away_pitcher_1st_inn_walk_rate',
            # Strikeout rates
            'home_pitcher_k_rate', 'away_pitcher_k_rate',
            # Home run rates
            'home_pitcher_hr_rate', 'away_pitcher_hr_rate',
            'home_pitcher_1st_inn_hr_rate', 'away_pitcher_1st_inn_hr_rate',
            # Ground ball rates
            'home_pitcher_gb_rate', 'away_pitcher_gb_rate'
        ]
        base_features.extend(pitcher_features)
        
        # Lineup quality features (NEW - WEIGHTED TOP 6 BATTERS)
        lineup_features = [
            # Home lineup
            'home_weighted_obp', 'home_weighted_slg', 'home_weighted_ops',
            'home_weighted_walk_rate', 'home_weighted_iso',
            'home_weighted_1st_inn_perf', 'home_hot_streak_score',
            # Away lineup
            'away_weighted_obp', 'away_weighted_slg', 'away_weighted_ops',
            'away_weighted_walk_rate', 'away_weighted_iso',
            'away_weighted_1st_inn_perf', 'away_hot_streak_score'
        ]
        base_features.extend(lineup_features)
        
        # Add park features
        park_features = [col for col in df.columns if col.startswith('park_')]
        base_features.extend(park_features)
        
        # Add time features
        if 'is_summer' in df.columns:
            base_features.append('is_summer')
        
        # Filter to only columns that exist
        available_features = [f for f in base_features if f in df.columns]
        
        print(f"Using {len(available_features)} features: {available_features}")
        return available_features
    
    def train(self, data_file: str):
        """
        Train the model on historical data
        """
        print("="*70)
        print("TRAINING FIRST INNING PREDICTION MODEL")
        print("="*70)
        
        # Load data
        print(f"\nLoading data from {data_file}...")
        df = pd.read_csv(data_file)
        print(f"Loaded {len(df)} games")
        
        # Prepare features (passing df as historical data for stats calculation)
        df = self.prepare_features(df, historical_data=df)
        
        # Store the calculated stats for future predictions
        self.team_stats = self._calculate_team_stats(df)
        self.pitcher_stats = self._calculate_pitcher_stats(df)
        print(f"Calculated stats for {len(self.team_stats)} teams and {len(self.pitcher_stats)} pitchers")
        
        # Get feature columns
        self.feature_names = self.get_feature_columns(df)
        
        # Prepare X and y
        X = df[self.feature_names].fillna(0)
        y = df['target']
        
        print(f"\nTraining on {len(X)} games with {len(self.feature_names)} features")
        print(f"Positive class (first inning run): {y.sum()} ({y.mean()*100:.1f}%)")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        print("\nTraining logistic regression model...")
        self.model = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced'  # Handle any class imbalance
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        print("\n" + "="*70)
        print("MODEL PERFORMANCE")
        print("="*70)
        
        # Training set
        y_train_pred = self.model.predict(X_train_scaled)
        y_train_proba = self.model.predict_proba(X_train_scaled)[:, 1]
        train_acc = accuracy_score(y_train, y_train_pred)
        train_auc = roc_auc_score(y_train, y_train_proba)
        
        print(f"\nTraining Set ({len(X_train)} games):")
        print(f"  Accuracy: {train_acc*100:.2f}%")
        print(f"  AUC-ROC: {train_auc:.3f}")
        
        # Test set
        y_test_pred = self.model.predict(X_test_scaled)
        y_test_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        test_acc = accuracy_score(y_test, y_test_pred)
        test_auc = roc_auc_score(y_test, y_test_proba)
        
        print(f"\nTest Set ({len(X_test)} games):")
        print(f"  Accuracy: {test_acc*100:.2f}%")
        print(f"  AUC-ROC: {test_auc:.3f}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        print(f"\n5-Fold Cross-Validation:")
        print(f"  Mean Accuracy: {cv_scores.mean()*100:.2f}%")
        print(f"  Std Dev: {cv_scores.std()*100:.2f}%")
        
        # Feature importance
        print(f"\nTop 10 Most Important Features:")
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'coefficient': abs(self.model.coef_[0])
        }).sort_values('coefficient', ascending=False)
        
        for idx, row in feature_importance.head(10).iterrows():
            print(f"  {row['feature']}: {row['coefficient']:.3f}")
        
        # Calibration check
        print(f"\nCalibration Check (predicted vs actual rates):")
        bins = [0, 0.4, 0.45, 0.5, 0.55, 0.6, 1.0]
        labels = ['<40%', '40-45%', '45-50%', '50-55%', '55-60%', '>60%']
        
        test_df = pd.DataFrame({
            'predicted_prob': y_test_proba,
            'actual': y_test
        })
        test_df['bin'] = pd.cut(test_df['predicted_prob'], bins=bins, labels=labels)
        
        calibration = test_df.groupby('bin', observed=True).agg({
            'predicted_prob': 'mean',
            'actual': ['mean', 'count']
        }).round(3)
        
        print(calibration)
        
        # Save model
        self.save_model()
        
        print("\n" + "="*70)
        print("✅ MODEL TRAINING COMPLETE")
        print("="*70)
        
        return test_acc
    
    def predict_game(self, game_data: Dict, historical_data: pd.DataFrame = None) -> Dict:
        """
        Predict probability for a single game
        
        Args:
            game_data: Dictionary with game information
            historical_data: Optional historical data for calculating team/pitcher stats
            
        Returns:
            Dictionary with prediction and probability
        """
        if self.model is None:
            raise ValueError("Model not trained. Run train() first or load a saved model.")
        
        # Convert game data to DataFrame
        df = pd.DataFrame([game_data])
        df = self.prepare_features(df, historical_data=historical_data)
        
        # Extract features
        X = df[self.feature_names].fillna(0)
        X_scaled = self.scaler.transform(X)
        
        # Predict
        probability = self.model.predict_proba(X_scaled)[0, 1]
        prediction = self.model.predict(X_scaled)[0]
        
        return {
            'probability': probability,
            'prediction': 'YES' if prediction == 1 else 'NO',
            'confidence': 'High' if abs(probability - 0.5) > 0.15 else 'Medium' if abs(probability - 0.5) > 0.08 else 'Low'
        }
    
    def save_model(self):
        """Save trained model to disk"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'team_stats': self.team_stats,
            'pitcher_stats': self.pitcher_stats,
            'timestamp': timestamp
        }
        
        filename = f"{self.model_dir}/first_inning_model_{timestamp}.pkl"
        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)
        
        # Also save as "latest"
        latest_file = f"{self.model_dir}/first_inning_model_latest.pkl"
        with open(latest_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"\n✅ Model saved to {filename}")
        print(f"✅ Latest model saved to {latest_file}")
    
    def load_model(self, filename: str = None):
        """Load trained model from disk"""
        if filename is None:
            filename = f"{self.model_dir}/first_inning_model_latest.pkl"
        
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Model file not found: {filename}")
        
        print(f"Loading model from {filename}...")
        with open(filename, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.team_stats = model_data.get('team_stats', None)
        self.pitcher_stats = model_data.get('pitcher_stats', None)
        
        print(f"✅ Model loaded (trained: {model_data['timestamp']})")
        if self.team_stats is not None:
            print(f"   Team stats: {len(self.team_stats)} teams")
        if self.pitcher_stats is not None:
            print(f"   Pitcher stats: {len(self.pitcher_stats)} pitchers")


def main():
    parser = argparse.ArgumentParser(description='First Inning Prediction Model')
    parser.add_argument('--train', action='store_true', help='Train the model')
    parser.add_argument('--data', type=str, help='Path to training data CSV')
    parser.add_argument('--predict', action='store_true', help='Make predictions')
    
    args = parser.parse_args()
    
    predictor = FirstInningPredictor()
    
    if args.train:
        if not args.data:
            print("Error: --data required for training")
            return
        
        predictor.train(args.data)
    
    elif args.predict:
        print("Prediction mode - use the daily_predictor.py script instead")
        print("That script loads the model and generates predictions for today's games")
    
    else:
        print("Usage:")
        print("  Train: python first_inning_predictor.py --train --data mlb_data/first_inning_data_2024.csv")
        print("  Predict: Use daily_predictor.py script")


if __name__ == "__main__":
    main()
