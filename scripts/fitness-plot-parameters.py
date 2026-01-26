#!/usr/bin/env python3
from pathlib import Path
import matplotlib.pyplot as plt
import argparse


# Default experiment order
DEFAULT_EXPERIMENT_ORDER = [
    "25-10-30-original-arbiter",
    "25-12-02-ltl-filter-arbiter",
    "25-12-05-well-separation-arbiter",
    "25-12-05-disable-semsim-arbiter",
    "25-12-10-ltl-filter-disable-semsim-arbiter",
    "25-12-10-ltl-filter-well-separation-disable-semsim-arbiter",
]

EXPERIMENT_NAME_MAP = {
    "25-10-30-original-arbiter": "Original",
    "25-12-02-ltl-filter-arbiter": "Original + LTL Filter",
    "25-12-05-well-separation-arbiter": "Original + LTL Filter + Well Separation",
    "25-12-05-disable-semsim-arbiter": "Disable SemSim",
    "25-12-10-ltl-filter-disable-semsim-arbiter": "Disable SemSim + LTL Filter",
    "25-12-10-ltl-filter-well-separation-disable-semsim-arbiter": "Disable SemSim + LTL Filter + Well Separation",
}


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
        mapped_label = EXPERIMENT_NAME_MAP.get(label, label)
        plt.hist(scores, bins=bins, range=(0, 1), label=mapped_label, alpha=0.6, edgecolor='black', color=color)

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
    ap = argparse.ArgumentParser(description="Plot fitness scores across experiments for a single parameter configuration.")
    ap.add_argument("--parameter", type=str, default="arbiter-70-10-10-10",
                    help="Parameter configuration to plot (default: arbiter-70-10-10-10)")
    ap.add_argument("--base-dir", type=str, default=".",
                    help="Base directory containing experiment folders (default: current directory)")
    ap.add_argument("--bins", type=int, default=20, help="Bins for histogram")
    ap.add_argument("--save", type=str, default=None, help="Save figure to this path instead of showing")
    ap.add_argument("--property", type=str, choices=["syntactic", "semantic", "fitness"], default="fitness",
                    help="Which property to plot (default: fitness)")
    ap.add_argument("--experiments", type=str, nargs='+', default=None,
                    help="Custom list of experiment folders to include (space-separated)")
    args = ap.parse_args()

    base_dir = Path(args.base_dir)
    if not base_dir.exists():
        ap.error(f"Base directory not found: {base_dir}")

    # Determine which experiments to include
    if args.experiments:
        experiment_folders = args.experiments
    else:
        experiment_folders = DEFAULT_EXPERIMENT_ORDER

    # Collect data for the specified parameter across all experiments
    data_dict = {}
    for exp_name in experiment_folders:
        exp_dir = base_dir / exp_name / args.parameter
        if not exp_dir.exists():
            print(f"Warning: Directory not found: {exp_dir}")
            continue

        scores, _ = read_scores(exp_dir, args.property)
        if scores:
            # Use experiment name as label
            data_dict[exp_name] = scores
        else:
            print(f"Warning: No scores found in {exp_dir}")

    if not data_dict:
        print(f"No scores found for parameter '{args.parameter}' in any experiment.")
        return

    # Use experiment order for sorting
    if args.experiments:
        filtered_sort_order = [label for label in args.experiments if label in data_dict]
    else:
        filtered_sort_order = [label for label in DEFAULT_EXPERIMENT_ORDER if label in data_dict]

    plot_histogram_multi(data_dict, bins=args.bins, score_property=args.property, save_path=args.save, sort_order=filtered_sort_order if filtered_sort_order else None)


if __name__ == "__main__":
    main()
