#!/usr/bin/env python3
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import argparse

# SCORE_PREFIX = "//semantic: "
# METRIC_NAME = "Semantic"
SCORE_PREFIX = "//fitness: "
METRIC_NAME = "Fitness"

def read_scores(data_directory: Path, pattern="run_*"):
    runs = sorted(data_directory.glob("run_*"))
    scores = []
    labels = []
    for run in runs:
        # collect first score found in any spec*.tlsf inside the run
        found = False
        for spec_file in run.glob("spec*.tlsf"):
            with spec_file.open() as f:
                for line in f:
                    if line.startswith(SCORE_PREFIX):
                        try:
                            score = float(line.split()[1])
                            scores.append(score)
                            labels.append(run.name)
                            found = True
                            break
                        except Exception:
                            # ignore malformed lines
                            pass
            if found:
                break
    return scores, labels

def plot_histogram(scores, bins=20, title=f"{METRIC_NAME} scores distribution", save_path=None):
    plt.figure(figsize=(8,5))
    plt.hist(scores, bins=bins, range=(0,1), edgecolor='black', alpha=0.8)
    plt.xlabel("Score")
    plt.ylabel("Count")
    plt.title(title)
    plt.grid(axis='y', alpha=0.3)
    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
    else:
        plt.show()
    plt.close()

def main():
    ap = argparse.ArgumentParser(description="Plot fitness scores (histogram or bar chart).")
    ap.add_argument("data_dir", nargs="?", default="25-10-30-original-arbiter/arbiter-70-10-10-10",
                    help="Root folder containing run_* subfolders")
    ap.add_argument("--bins", type=int, default=20, help="Bins for histogram")
    ap.add_argument("--sort", action="store_true", help="Sort bars descending by score")
    ap.add_argument("--save", type=str, default=None, help="Save figure to this path instead of showing")
    ap.add_argument("--max-bars", type=int, default=200, help="Max bars to display for bar chart (for readability)")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        ap.error(f"Data directory not found: {data_dir}")

    scores, labels = read_scores(data_dir)
    if not scores:
        print("No scores found. Ensure spec*.tlsf files contain lines like: //fitness: 0.123")
        return

    plot_histogram(scores, bins=args.bins, save_path=args.save)

if __name__ == "__main__":
    main()