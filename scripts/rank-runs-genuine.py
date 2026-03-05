from pathlib import Path
import bisect
import sys
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


def getSortedSpecs(original_spec_path: Path, repaired_specs_dir: Path) -> list[tuple[str, float, float]]:
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
        "main.SemanticSimilarity",
        str(original_spec_path),
        str(repaired_specs_dir)
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=3600,
        )
    except subprocess.TimeoutExpired:
        print(f"Error: SemanticSimilarity timed out for {repaired_specs_dir.name}", file=sys.stderr)
        sys.exit(1)
    if result.returncode != 0:
        print("SemanticSimilarity failed (stderr was printed above).", file=sys.stderr)
        sys.exit(1)
    # Parse CSV output: filename,semantic_similarity,elapsed_time,progress
    scores = []
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            parts = line.split(',')
            if len(parts) >= 2:
                try:
                    print(parts)
                    filename = parts[0]
                    semantic_similarity = float(parts[1])
                    time = float(parts[2])
                    scores.append((filename, semantic_similarity, filename, time))
                except (ValueError, IndexError):
                    pass
    # Sort by semantic similarity in descending order
    scores.sort(key=lambda x: -x[1])
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
    try:
        print(f"Running GenuineSolutionsMinimal for {solutions_dir.name}...", file=sys.stderr, flush=True)
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=3600,
        )
        if result.returncode != 0:
            print(f"Warning: GenuineSolutionsMinimal failed with return code {result.returncode}", file=sys.stderr)
            return {"genuine": set(), "weaker": set(), "stronger": set()}
        # Parse JSON output
        output = result.stdout.strip()
        if not output:
            print(f"Warning: GenuineSolutionsMinimal returned empty output", file=sys.stderr)
            return {"genuine": set(), "weaker": set(), "stronger": set()}
        data = json.loads(output)
        return {
            "genuine": set(data.get("genuine_solutions", [])),
            "weaker": set(data.get("weaker_solutions", [])),
            "stronger": set(data.get("stronger_solutions", []))
        }
    except subprocess.TimeoutExpired:
        print(f"Error: GenuineSolutionsMinimal timed out for {solutions_dir.name}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON output from GenuineSolutionsMinimal: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error in getGenuineStatistics: {e}", file=sys.stderr)
        sys.exit(1)


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


def processAggregateAll(run_dirs: list[Path], genuine_dir: Path, original_spec: Path) -> tuple[float, float, float] | None:
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
        # stats = getGenuineStatistics(run_dir, genuine_dir)
        # all_stats["genuine"].update(stats["genuine"])
        # all_stats["weaker"].update(stats["weaker"])
        # all_stats["stronger"].update(stats["stronger"])
        # Get sorted specs for this run
        scores = getSortedSpecs(original_spec, run_dir)
        # all_scores.extend(scores)
        # all_specs.extend(specs)
    if not all_specs:
        # print("Warning: No specs found in any run")
        return None
    # Compute NDCG on aggregated data
    ndcg = computeNdcg(all_scores, all_stats)
    p_value, effect_size, mean_random = compute_monte_carlo_pvalue(all_scores, all_stats)
    return (ndcg, p_value, effect_size)


def get_inputs() -> tuple[list[Path], list[Path], list[Path]]:
    results_dirs = [
        # Path("result/lily02"),
        # Path("result/minepump"),
        # Path("result/Lift"),
        Path("result/arbiter"),
        # Path("result/RG1"),
        # Path("result/RG2"),
        # Path("result/gyro_var1"),
        # Path("result/gyro_var2"),
        # Path("result/HumanoidLTL_531_Humanoid_unrealizable"),
    ]
    for d in results_dirs:
        if not d.is_dir():
            print(f"Error: Results directory {d} does not exist or is not a directory")
            return
    genuine_dirs = [
        # Path("case-studies/lily02/genuine"),
        # Path("case-studies/minepump/genuine"),
        # Path("case-studies/lift/genuine"),
        Path("case-studies/arbiter/genuine"),
        # Path("case-studies/RG1/genuine"),
        # Path("case-studies/RG2/genuine"),
        # Path("case-studies/GyroUnrealizable_Var1/genuine"),
        # Path("case-studies/GyroUnrealizable_Var2/genuine"),
        # Path("case-studies/HumanoidLTL_531/genuine")
    ]
    for d in genuine_dirs:
        if not d.is_dir():
            print(f"Error: Genuine directory {d} does not exist or is not a directory")
            return
    original_specs = [
        # Path("case-studies/lily02/lily02.tlsf"),
        # Path("case-studies/minepump/minepump.tlsf"),
        # Path("case-studies/lift/Lift.tlsf"),
        Path("case-studies/arbiter/arbiter.tlsf"),
        # Path("case-studies/RG1/RG1.tlsf"),
        # Path("case-studies/RG2/RG2.tlsf"),
        # Path("case-studies/GyroUnrealizable_Var1/original.tlsf"),
        # Path("case-studies/GyroUnrealizable_Var2/original.tlsf"),
        # Path("case-studies/HumanoidLTL_531/original.tlsf")
    ]
    for d in original_specs:
        if not d.is_file():
            print(f"Error: Original spec file {d} does not exist or is not a file")
            return
    return results_dirs, genuine_dirs, original_specs


def main():
    global NUM_PERMUTATIONS
    ap = argparse.ArgumentParser(description="Rank runs and compute NDCG with Monte Carlo p-values")
    ap.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    ap.add_argument("--permutations", type=int, default=NUM_PERMUTATIONS, help="Number of random permutations for Monte Carlo test")
    args = ap.parse_args()
    NUM_PERMUTATIONS = args.permutations
    results_dirs, genuine_dirs, original_specs = get_inputs()
    # print("case-study,ndcg,p-value,effect-size", flush=True)
    for results_dir, genuine_dir, original_spec in zip(results_dirs, genuine_dirs, original_specs):
        # Collect all run directories
        run_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()])
        result = processAggregateAll(run_dirs, genuine_dir, original_spec)
        if result:
            ndcg, p_value, effect_size = result
            print(f"{results_dir.name},{ndcg:.4f},{p_value:.4f},{effect_size:.2f}", flush=True)


if __name__ == "__main__":
    main()
