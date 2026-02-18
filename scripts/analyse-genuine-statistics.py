#!/usr/bin/env python3

import sys
import pandas as pd

def main():
    if len(sys.argv) != 2:
        print("Usage: analyze-genuine-statistics.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    df = pd.read_csv(csv_file)

    # Filter out rows where n_total_solutions is 0 to avoid division by zero
    df_filtered = df[df['n_total_solutions'] > 0]

    if len(df_filtered) == 0:
        print("No valid data (all rows have 0 total solutions)")
        return

    # Calculate averages
    avg_total = df_filtered['n_total_solutions'].mean()
    avg_genuine = df_filtered['n_genuine_solutions'].mean()
    avg_weaker = df_filtered['n_weaker_solutions'].mean()
    avg_stronger = df_filtered['n_stronger_solutions'].mean()
    
    # Calculate standard deviations
    std_total = df_filtered['n_total_solutions'].std()
    std_genuine = df_filtered['n_genuine_solutions'].std()
    std_weaker = df_filtered['n_weaker_solutions'].std()
    std_stronger = df_filtered['n_stronger_solutions'].std()
    
    print(f"Statistics for {csv_file}:")

    print(f"  {'Avg total solutions:':<24}{avg_total:>5.2f} [{std_total:.2f}]")
    print(f"  {'Avg genuine solutions:':<24}{avg_genuine:>5.2f} [{std_genuine:.2f}]")
    print(f"  {'Avg weaker solutions:':<24}{avg_weaker:>5.2f} [{std_weaker:.2f}]")
    print(f"  {'Avg stronger solutions:':<24}{avg_stronger:>5.2f} [{std_stronger:.2f}]")

if __name__ == '__main__':
    main()
