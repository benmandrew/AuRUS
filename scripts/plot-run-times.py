#!/usr/bin/env python3

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

IGNORES = {
    "amba",
    "HumanoidLTL_531",
    "lift",
    "lily02",
    # "RG1",
    # "GyroUnrealizable_Var2",
}

def main():
    if len(sys.argv) != 2:
        print("Usage: plot-run-times.py <run_times_csv>")
        sys.exit(1)
    csv_file = sys.argv[1]
    df = pd.read_csv(csv_file)
    # Extract case study names from paths
    df['case_study_name'] = df['case_study'].apply(
        lambda x: os.path.basename(os.path.dirname(x)) if '/' in x else x
    )
    # Get unique case studies and filter
    case_studies = [cs for cs in df['case_study_name'].unique() if cs not in IGNORES]
    # Prepare data for box plot
    data_by_case = [df[df['case_study_name'] == cs]['total_seconds'].values 
                    for cs in case_studies]
    plt.rcParams.update({"font.size": 14})
    # Create figure
    fig, ax = plt.subplots(figsize=(max(10, len(case_studies) * 0.8), 6))
    # Create box plot without showing outliers
    labels = []
    for case_study in case_studies:
        if case_study == "GyroUnrealizable_Var2":
            labels.append("gyro_var2")
        elif case_study == "GyroUnrealizable_Var1":
            labels.append("gyro_var1")
        else:
            labels.append(case_study)
    bp = ax.boxplot(data_by_case, labels=labels, patch_artist=True,
                    showfliers=False, widths=0.6,
                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                    medianprops=dict(color='red', linewidth=2),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5))
    # Add indication of outliers above each box
    for idx, cs in enumerate(case_studies):
        study_data = df[df['case_study_name'] == cs]['total_seconds']
        q1 = study_data.quantile(0.25)
        q3 = study_data.quantile(0.75)
        iqr = q3 - q1
        upper_fence = q3 + 1.5 * iqr
        outliers = study_data[study_data > upper_fence]
        if len(outliers) > 0:
            max_val = study_data.max()
            # Add small triangle at top of whisker to indicate outliers exist
            ax.plot(idx + 1, upper_fence, '^', color='orange', markersize=8, 
                   markeredgecolor='black', markeredgewidth=0.5)
            # Add text annotation with outlier info
            ax.text(idx + 1, upper_fence * 1.02, f'↑{len(outliers)}\nmax={max_val:.0f}', 
                   ha='center', va='bottom', fontsize=8, color='orange',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                            edgecolor='orange', alpha=0.8))
    ax.set_xlabel('Case Study', fontsize=12)
    ax.set_ylabel('Total Runtime (seconds)', fontsize=12)
    ax.set_title('Runtime Distribution by Case Study', fontsize=14, fontweight='bold')
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    output_path = csv_file.replace('.csv', '_plots.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Plots saved to {output_path}")

if __name__ == '__main__':
    main()
