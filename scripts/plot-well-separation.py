#!/usr/bin/env python3
"""Plot ratio of well-separated satisfiable solutions as a grouped bar chart.

Reads a CSV with columns: experiment, parameters, satisfiable, notwellseparated,
wellseparated, unsatisfiable, timeout, errors. Computes wellseparated / satisfiable
per (experiment, parameters) and plots bars grouped by parameters with one bar per
experiment.
"""

from pathlib import Path
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Default parameter order used for the arbiter datasets
DEFAULT_PARAM_ORDER = [
    "arbiter-70-10-0-20",
    "arbiter-70-10-5-15",
    "arbiter-70-10-10-10",
    "arbiter-70-10-15-5",
    "arbiter-70-10-20-0",
]


def load_ratios(csv_path: Path):
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    required_cols = {"experiment", "parameters", "satisfiable", "wellseparated"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

    # Avoid division by zero
    df = df[df["satisfiable"] > 0].copy()
    df["ratio"] = df["wellseparated"] / df["satisfiable"]

    return df


def plot_grouped_bars(df, output: Path | None, param_order=None, title="Well-separated ratio", dpi=150):
    # Determine order for parameters and experiments
    if param_order is None:
        param_order = sorted(df["parameters"].unique())
    else:
        # Keep only parameters present in data; append any missing ones that exist in data
        present = [p for p in param_order if p in set(df["parameters"])]
        remaining = [p for p in sorted(df["parameters"].unique()) if p not in present]
        param_order = present + remaining

    experiments = sorted(df["experiment"].unique())

    # Pivot to parameters x experiments
    pivot = df.pivot_table(
        index="parameters",
        columns="experiment",
        values="ratio",
        aggfunc="mean",
    ).reindex(param_order)

    n_params = len(param_order)
    n_exps = len(experiments)
    width = 0.8 / n_exps if n_exps else 0.8

    fig, ax = plt.subplots(figsize=(max(10, 1.6 * n_params), 6))
    x = np.arange(n_params)

    colors = plt.cm.tab10.colors
    for i, exp in enumerate(experiments):
        offsets = x - 0.4 + width / 2 + i * width
        values = pivot[exp].to_numpy()
        ax.bar(offsets, values, width=width, label=exp, color=colors[i % len(colors)], edgecolor="black", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(param_order, rotation=30, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Well-separated / satisfiable")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="Experiment")

    fig.tight_layout()
    if output:
        fig.savefig(output, dpi=dpi, bbox_inches="tight")
        print(f"Saved plot to {output}")
    else:
        plt.show()

    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Plot well-separated ratio as grouped bar chart.")
    parser.add_argument("csv", type=str, help="Path to wellseparation.csv")
    parser.add_argument("--output", type=str, default=None, help="Optional path to save the plot (e.g., plot.png)")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for saved figure")
    parser.add_argument(
        "--param-order",
        nargs="+",
        default=None,
        help="Custom parameter order for x-axis (space-separated parameter names)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    df = load_ratios(csv_path)

    # Use default order unless a custom one is provided
    param_order = args.param_order if args.param_order else DEFAULT_PARAM_ORDER

    title = "Well-separated ratio per parameter"
    plot_grouped_bars(df, output=Path(args.output) if args.output else None, param_order=param_order, title=title, dpi=args.dpi)


if __name__ == "__main__":
    main()
