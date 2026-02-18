#!/usr/bin/env python3

import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, MultipleLocator

def main():
    if len(sys.argv) != 2:
        print("Usage: plot-genuine-statistics-histogram.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    df = pd.read_csv(csv_file)

    plt.figure(figsize=(10, 6))
    max_solutions = int(df['n_total_solutions'].max())
    plt.hist(df['n_total_solutions'], bins=[i - 0.5 for i in range(max_solutions + 2)], edgecolor='black', alpha=0.7)
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.gca().xaxis.set_minor_locator(MultipleLocator(1))
    plt.xlabel('Number of Total Solutions')
    plt.ylabel('Frequency')
    plt.title('Distribution of Total Solutions')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(csv_file.replace('.csv', '_histogram.png'), dpi=150)
    # plt.show()
    print(f"Histogram saved to {csv_file.replace('.csv', '_histogram.png')}")

if __name__ == '__main__':
    main()
