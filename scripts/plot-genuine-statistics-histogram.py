#!/usr/bin/env python3

import sys
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, MultipleLocator, AutoMinorLocator

IGNORES = {
    # "RG1.csv",
    # "GyroUnrealizable_Var2.csv",
    # "lily02.csv",
    "amba.csv",
    "HumanoidLTL_531.csv",
    # "lift.csv",
    "lily02.csv",
    # "RG1.csv",
    # "GyroUnrealizable_Var2.csv",
    "lily02.csv",
}

def main():
    if len(sys.argv) != 2:
        print("Usage: plot-genuine-statistics-histogram.py <csv_file_or_directory>")
        sys.exit(1)
    input_path = sys.argv[1]
    if os.path.isdir(input_path):
        csv_files = sorted(glob.glob(os.path.join(input_path, "*.csv")))
        csv_files = [f for f in csv_files if os.path.basename(f) not in IGNORES]
        if not csv_files:
            print(f"No CSV files found in directory: {input_path}")
            sys.exit(1)
        df = pd.concat((pd.read_csv(path) for path in csv_files), ignore_index=True)
        case_study_count = len(csv_files)
        title_suffix = f"{case_study_count} case studies"
        output_path = os.path.join(input_path, "aggregated_genuine_histogram.png")
    else:
        df = pd.read_csv(input_path)
        title_suffix = os.path.splitext(os.path.basename(input_path))[0]
        output_path = input_path.replace('.csv', '_genuine_histogram.png')
    plt.rcParams.update({"font.size": 14})
    plt.figure(figsize=(10, 6))
    summed_solutions = df['n_genuine_solutions'] + df['n_weaker_solutions'] + df['n_stronger_solutions']
    # summed_solutions = df['n_total_solutions']
    max_solutions = int(summed_solutions.max())
    plt.hist(summed_solutions, bins=[i - 0.5 for i in range(max_solutions + 2)], edgecolor='black', alpha=0.7)
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.gca().xaxis.set_minor_locator(MultipleLocator(1))
    plt.gca().yaxis.set_minor_locator(AutoMinorLocator())
    plt.xlabel('Number of Genuine Solutions')
    plt.ylabel('Frequency')
    total_runs = len(df)
    plt.title(f"Distribution of Genuine Solutions ({title_suffix}, {total_runs} runs)")
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    # plt.show()
    print(f"Histogram saved to {output_path}")

if __name__ == '__main__':
    main()
