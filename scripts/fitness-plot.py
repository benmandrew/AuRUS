#!/usr/bin/env python3
from pathlib import Path
import matplotlib.pyplot as plt
import argparse


# Default custom sort order for arbiter parameters
DEFAULT_SORT_ORDER = [
    "arbiter-70-10-0-20",
    "arbiter-70-10-5-15",
    "arbiter-70-10-10-10",
    "arbiter-70-10-15-5",
    "arbiter-70-10-20-0",
]


def read_scores(data_directory: Path, score_property: str = "fitness"):
    runs = sorted(data_directory.glob("run_*"))
    scores = []
    labels = []
    for run in runs:
        # collect first score found in any spec*.tlsf inside the run
        found = False
        for spec_file in run.glob("spec*.tlsf"):
            with spec_file.open() as f:
                for line in f:
                    if line.startswith(f"//{score_property}: "):
                        score = float(line.split()[1])
                        scores.append(score)
                        labels.append(run.name)
                        found = True
                        break
            if found:
                break
    return scores, labels


def plot_histogram_multi(data_dict, bins=20, score_property: str = "fitness", save_path=None, sort_order=None):
    """Plot multiple datasets on a single histogram with different colors and transparency."""
    title = f"{score_property.capitalize()} scores distribution (comparison)"
    plt.figure(figsize=(10, 6))

    # Sort data_dict according to sort_order if provided
    if sort_order:
        sorted_items = [(label, data_dict[label]) for label in sort_order if label in data_dict]
        # Append any labels not in sort_order
        for label in sorted(data_dict.keys()):
            if label not in sort_order:
                sorted_items.append((label, data_dict[label]))
    else:
        sorted_items = sorted(data_dict.items())

    colors = plt.cm.tab10(range(len(sorted_items)))
    for (label, scores), color in zip(sorted_items, colors):
        plt.hist(scores, bins=bins, range=(0, 1), label=label, alpha=0.6, edgecolor='black', color=color)

    plt.xlabel("Score")
    plt.ylabel("Count")
    plt.minorticks_on()
    plt.title(title)
    plt.legend(loc='upper left')
    plt.grid(axis='y', alpha=0.3)
    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
    else:
        plt.show()
    plt.close()


def main():
    ap = argparse.ArgumentParser(description="Plot fitness scores with histogram.")
    ap.add_argument("data_dir", type=str, 
                    help="Folder containing run_* subfolders. Pass a parent directory to plot all subdirectories.")
    ap.add_argument("--bins", type=int, default=20, help="Bins for histogram")
    ap.add_argument("--save", type=str, default=None, help="Save figure to this path instead of showing")
    ap.add_argument("--property", type=str, choices=["syntactic", "semantic", "fitness"], default="fitness",
                    help="Which property to plot (default: fitness)")
    args = ap.parse_args()

    parent_dir = Path(args.data_dir)
    if not parent_dir.exists():
        ap.error(f"Parent directory not found: {parent_dir}")
    # Get all immediate subdirectories
    subdirs = sorted([d for d in parent_dir.iterdir() if d.is_dir()])
    if not subdirs:
        print(f"No subdirectories found in {parent_dir}")
        return
    data_dirs = [str(d) for d in subdirs]

    # Multi-folder mode: plot all on same histogram
    data_dict = {}
    for data_dir_str in data_dirs:
        data_dir = Path(data_dir_str)
        if not data_dir.exists():
            print(f"Warning: Data directory not found: {data_dir}")
            continue

        scores, _ = read_scores(data_dir)
        if scores:
            # Use folder name as label (last component of path)
            label = data_dir.name
            data_dict[label] = scores

    if not data_dict:
        print("No scores found in any folder.")
        return

    filtered_sort_order = [label for label in DEFAULT_SORT_ORDER if label in data_dict]
    plot_histogram_multi(data_dict, bins=args.bins, score_property=args.property, save_path=args.save, sort_order=filtered_sort_order if filtered_sort_order else None)


if __name__ == "__main__":
    main()
