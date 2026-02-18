"""
Fix MLB Data - Calculate first_inning_run_scored
=================================================
The data collector didn't populate the first_inning_run_scored column.
This script calculates it from first_inning_runs_away and first_inning_runs_home.
"""

import pandas as pd
import sys

def fix_csv(filepath):
    print(f"Processing {filepath}...")
    
    # Load the CSV
    df = pd.read_csv(filepath)
    
    print(f"  Rows before: {len(df)}")
    
    # Calculate first_inning_run_scored from the runs columns
    # If either team scored in the 1st inning, set to 1, otherwise 0
    df['first_inning_run_scored'] = (
        (df['first_inning_runs_away'] > 0) | 
        (df['first_inning_runs_home'] > 0)
    ).astype(int)
    
    # Show distribution
    yrfi_count = df['first_inning_run_scored'].sum()
    nrfi_count = len(df) - yrfi_count
    yrfi_pct = (yrfi_count / len(df)) * 100
    
    print(f"  YRFI (run scored): {yrfi_count} ({yrfi_pct:.1f}%)")
    print(f"  NRFI (no run):     {nrfi_count} ({100-yrfi_pct:.1f}%)")
    
    # Save back
    df.to_csv(filepath, index=False)
    print(f"  ✅ Fixed and saved!\n")
    
    return len(df)

if __name__ == "__main__":
    total_games = 0
    
    for year in [2022, 2023, 2024]:
        filepath = f"mlb_data/first_inning_data_{year}.csv"
        try:
            games = fix_csv(filepath)
            total_games += games
        except FileNotFoundError:
            print(f"  ⚠️  {filepath} not found, skipping...\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
    
    print(f"{'='*60}")
    print(f"Total games fixed: {total_games}")
    print(f"{'='*60}")
