from pathlib import Path
import bisect
from termcolor import colored
import argparse
import subprocess
import json
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
import random
import statistics


# Global configuration for Monte Carlo permutations
NUM_PERMUTATIONS = 10000


def getSortedSpecs(specs: list[Path], spec_dir: Path) -> list[tuple[float, str, str]]:
    scores: list[tuple[float, str, str]] = []
    for spec_path in specs:
        spec_file = spec_dir / spec_path.name
        with spec_file.open() as f:
            contents = f.read()
            syntactic_score = None
            for line in contents.splitlines():
                if line.startswith("//syntactic: "):
                    syntactic_score = float(line.split()[1])
            assert syntactic_score is not None, f"Missing syntactic score in {spec_path}"
            bisect.insort(scores, (syntactic_score, spec_file.name, contents), key=lambda x: -x[0])
    return scores


def getGenuineStatistics(solutions_dir: Path, genuine_dir: Path) -> dict[str, set[str]]:
    """Call the Java program to get genuine statistics."""
    references = []
    for f in genuine_dir.glob("*.tlsf"):
        references.extend(["--ref=" + str(f)])
    classpath = ":".join([
        "bin",
        "lib/commons-math3-3.6.1.jar",
        "lib/rltlconv.jar",
        "lib/JFLAP-7.0_With_Source.jar",
        "lib/owl-18.10-snapshot.jar",
        "lib/ejml/ejml-core-0.34.jar",
        "lib/ejml/ejml-cdense-0.34.jar",
        "lib/ejml/ejml-ddense-0.34.jar",
        "lib/ejml/ejml-fdense-0.34.jar",
        "lib/ejml/ejml-simple-0.34.jar",
        "lib/ejml/ejml-zdense-0.34.jar",
        "lib/ejml/ejml-dsparse-0.34.jar",
        "lib/ejml/ejml-experimental-0.34.jar",
        "lib/ltl2buchi.jar"
    ])
    cmd = [
        "java", "-Xmx8g", "-Djava.library.path=/usr/local/lib",
        "-cp", classpath,
        "main.GenuineSolutionsMinimal"
    ] + references + [str(solutions_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # Parse JSON output
    output = result.stdout.strip()
    data = json.loads(output)
    return {
        "genuine": set(data.get("genuine_solutions", [])),
        "weaker": set(data.get("weaker_solutions", [])),
        "stronger": set(data.get("stronger_solutions", []))
    }


def computeNdcg(ranking: list[tuple[float, str, str]], stats: dict[str, set[str]]) -> float:
    """
    Compute Normalized Discounted Cumulative Gain for the ranking.
    Relevance scores: genuine=1.0, weaker=1.0, stronger=1.0
    """
    def get_relevance(filename: str) -> float:
        if filename in stats["genuine"]:
            return 1.0
        elif filename in stats["weaker"]:
            return 1.0
        elif filename in stats["stronger"]:
            return 1.0
        else:
            return 0.0
    # Compute DCG
    dcg = 0.0
    seen = set()
    for _, filename, tlsf in ranking:
        if filename in seen:
            continue
        seen.add(filename)
        relevance = get_relevance(filename)
        position = len(seen)  # 1-indexed
        discount = math.log2(position + 1)
        dcg += relevance / discount
    # Compute IDCG (ideal ranking with all items sorted by relevance)
    all_files = set().union(stats["genuine"], stats["weaker"], stats["stronger"])
    relevances = []
    for filename in all_files:
        relevances.append(get_relevance(filename))
    relevances.sort(reverse=True)
    idcg = 0.0
    for i, relevance in enumerate(relevances):
        position = i + 1
        discount = math.log2(position + 1)
        idcg += relevance / discount
    if idcg == 0:
        return 0.0
    return dcg / idcg


def compute_monte_carlo_pvalue(ranking: list[tuple[float, str, str]], stats: dict[str, set[str]], num_permutations: int = None) -> tuple[float, float, float]:
    """
    Compute p-value and effect size using Monte Carlo permutation test.
    Returns: (p_value, effect_size, mean_random_ndcg)
    """
    if num_permutations is None:
        num_permutations = NUM_PERMUTATIONS
    # Compute actual NDCG
    actual_ndcg = computeNdcg(ranking, stats)
    # Extract just the filenames in order (preserving order)
    filenames = []
    seen = set()
    for _, filename, tlsf in ranking:
        if filename in seen:
            continue
        seen.add(filename)
        filenames.append(filename)
    # Generate random permutations and compute their NDCG
    random_ndcgs = []
    for _ in range(num_permutations):
        shuffled = filenames.copy()
        random.shuffle(shuffled)
        # Convert back to ranking format with dummy scores
        shuffled_ranking = [(0.0, filename, "") for filename in shuffled]
        random_ndcg = computeNdcg(shuffled_ranking, stats)
        random_ndcgs.append(random_ndcg)
    # Compute p-value (proportion of random permutations >= actual)
    p_value = sum(1 for ndcg in random_ndcgs if ndcg >= actual_ndcg) / num_permutations
    # Compute effect size (z-score)
    mean_random = statistics.mean(random_ndcgs)
    if len(random_ndcgs) > 1:
        std_random = statistics.stdev(random_ndcgs)
        if std_random > 0:
            effect_size = (actual_ndcg - mean_random) / std_random
        else:
            effect_size = 0.0
    else:
        effect_size = 0.0
    return (p_value, effect_size, mean_random)


def printRanking(run_dir: Path, scores: list[tuple[float, str, str]], stats: dict[str, set[str]]):
    seen: set[str] = set()
    rank = 1
    print(f"\n{run_dir.name}:")
    print("-" * 60)
    for _syntactic_score, file_name, tlsf in scores:
        if file_name in seen:
            continue
        seen.add(file_name)
        # Determine classification
        annotation = ""
        if file_name in stats["genuine"]:
            annotation = colored(" [genuine]", "green")
        elif file_name in stats["weaker"]:
            annotation = colored(" [weaker]", "yellow")
        elif file_name in stats["stronger"]:
            annotation = colored(" [stronger]", "red")
        print(f"{rank:>2}: {file_name:>11}{annotation}")
        rank += 1


def processRunDirectory(run_dir: Path, genuine_dir: Path) -> tuple[str, float, float, float] | None:
    """Process a single run directory and return (name, ndcg, p_value, effect_size) or None if directory is invalid."""
    if not run_dir.is_dir():
        return None
    specs_file = run_dir / "maximal-specs.txt"
    if not specs_file.exists():
        return None
    with specs_file.open() as f:
        specs = [Path(line.strip()) for line in f if line.strip()]
    # Get genuine statistics
    stats = getGenuineStatistics(run_dir, genuine_dir)
    if not stats["genuine"] and not stats["weaker"] and not stats["stronger"]:
        print(f"Warning: No genuine/weaker/stronger solutions found for {run_dir.name}")
        return None
    # Get sorted specs
    scores = getSortedSpecs(specs, run_dir)
    # printRanking(run_dir, scores, stats)
    # Compute NDCG
    ndcg = computeNdcg(scores, stats)
    # Compute p-value and effect size
    p_value, effect_size, mean_random = compute_monte_carlo_pvalue(scores, stats)
    print(f"NDCG: {ndcg:.4f} (p-value: {p_value:.4f}, effect size: {effect_size:.2f})")
    return (run_dir.name, ndcg, p_value, effect_size)


def processAggregateAll(run_dirs: list[Path], genuine_dir: Path) -> tuple[float, float, float] | None:
    """Process all runs aggregated together and return (ndcg, p_value, effect_size)."""
    all_specs = []
    all_stats = {"genuine": set(), "weaker": set(), "stronger": set()}
    all_scores = []
    # Collect all specs and stats from all runs
    for run_dir in run_dirs:
        specs_file = run_dir / "maximal-specs.txt"
        if not specs_file.exists():
            continue
        with specs_file.open() as f:
            specs = [Path(line.strip()) for line in f if line.strip()]
        # Get genuine statistics for this run
        stats = getGenuineStatistics(run_dir, genuine_dir)
        all_stats["genuine"].update(stats["genuine"])
        all_stats["weaker"].update(stats["weaker"])
        all_stats["stronger"].update(stats["stronger"])
        # Get sorted specs for this run
        scores = getSortedSpecs(specs, run_dir)
        all_scores.extend(scores)
        all_specs.extend(specs)
    if not all_specs:
        print("Warning: No specs found in any run")
        return None
    print(f"\nAggregated Results (from {len(run_dirs)} runs):")
    print("-" * 60)
    print(f"Total specs: {len(all_specs)}")
    print(f"Genuine solutions: {len(all_stats['genuine'])}")
    print(f"Weaker solutions: {len(all_stats['weaker'])}")
    print(f"Stronger solutions: {len(all_stats['stronger'])}")
    print()
    # Compute NDCG on aggregated data
    ndcg = computeNdcg(all_scores, all_stats)
    p_value, effect_size, mean_random = compute_monte_carlo_pvalue(all_scores, all_stats)
    print(f"Aggregated NDCG: {ndcg:.4f}")
    print(f"p-value: {p_value:.4f}")
    print(f"Effect size: {effect_size:.2f}")
    print(f"Mean random NDCG: {mean_random:.4f}")
    return (ndcg, p_value, effect_size)


def main():
    global NUM_PERMUTATIONS
    ap = argparse.ArgumentParser(description="Rank runs and compute NDCG with Monte Carlo p-values")
    ap.add_argument("results_dir", help="Directory containing run subdirectories with maximal-specs.txt")
    ap.add_argument("--genuine-dir", help="Directory containing genuine solutions", required=True)
    ap.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    ap.add_argument("--permutations", type=int, default=NUM_PERMUTATIONS, help="Number of random permutations for Monte Carlo test")
    ap.add_argument("--aggregate-all", action="store_true", help="Aggregate all specs from all runs for single NDCG computation")
    args = ap.parse_args()
    NUM_PERMUTATIONS = args.permutations
    results_dir = Path(args.results_dir)
    genuine_dir = Path(args.genuine_dir)
    if not results_dir.is_dir():
        print(f"Error: {results_dir} is not a directory")
        return
    # Collect all run directories
    run_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()])
    # If aggregate-all mode, process all runs together
    if args.aggregate_all:
        result = processAggregateAll(run_dirs, genuine_dir)
        if result:
            ndcg, p_value, effect_size = result
            print("\n" + "=" * 60)
            significance = ""
            if p_value < 0.001:
                significance = " ***"
            elif p_value < 0.01:
                significance = " **"
            elif p_value < 0.05:
                significance = " *"
            print(f"[Aggregated] NDCG={ndcg:.4f}, p-value={p_value:.4f}, effect_size={effect_size:.2f}{significance}")
        return
    # Process each subdirectory in parallel
    ndcg_scores = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(processRunDirectory, run_dir, genuine_dir): run_dir for run_dir in run_dirs}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                ndcg_scores.append(result)
    # Summary
    if ndcg_scores:
        print("\n" + "=" * 60)
        print("NDCG Summary:")
        print("=" * 60)
        print(f"{'Run':<5} {'NDCG':<7} {'p-value':<7} {'Effect Size':<8}")
        print("-" * 60)
        for name, ndcg, p_value, effect_size in sorted(ndcg_scores, key=lambda x: -x[1]):
            significance = ""
            if p_value < 0.001:
                significance = " ***"
            elif p_value < 0.01:
                significance = " **"
            elif p_value < 0.05:
                significance = " *"
            print(f"{name:>5} {ndcg:>7.4f} {p_value:>7.4f} {effect_size:>8.2f}{significance}")


if __name__ == "__main__":
    main()
