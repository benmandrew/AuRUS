from pathlib import Path
import bisect
from termcolor import colored
import argparse
import subprocess
import json
import math


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


def compute_ndcg(ranking: list[tuple[float, str, str]], stats: dict[str, set[str]]) -> float:
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
        if tlsf in seen:
            continue
        seen.add(tlsf)
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


def process_run_directory(run_dir: Path, genuine_dir: Path) -> tuple[str, float] | None:
    """Process a single run directory and return (name, ndcg) or None if directory is invalid."""
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
    seen: set[str] = set()
    rank = 1
    print(f"\n{run_dir.name}:")
    print("-" * 60)
    for _syntactic_score, file_name, tlsf in scores:
        if tlsf in seen:
            continue
        seen.add(tlsf)
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
    # Compute NDCG
    ndcg = compute_ndcg(scores, stats)
    print(f"\nNDCG: {ndcg:.4f}")
    return (run_dir.name, ndcg)


def main():
    ap = argparse.ArgumentParser(description="Rank runs and compute NDCG")
    ap.add_argument("results_dir", help="Directory containing run subdirectories with maximal-specs.txt")
    ap.add_argument("--genuine-dir", help="Directory containing genuine solutions", required=True)
    args = ap.parse_args()
    results_dir = Path(args.results_dir)
    genuine_dir = Path(args.genuine_dir)
    if not results_dir.is_dir():
        print(f"Error: {results_dir} is not a directory")
        return
    # Process each subdirectory
    ndcg_scores = []
    for run_dir in sorted(results_dir.iterdir()):
        result = process_run_directory(run_dir, genuine_dir)
        if result is not None:
            ndcg_scores.append(result)
    # Summary
    if ndcg_scores:
        print("\n" + "=" * 60)
        print("NDCG Summary:")
        print("=" * 60)
        for name, ndcg in sorted(ndcg_scores, key=lambda x: -x[1]):
            print(f"{name:>20}: {ndcg:.4f}")


if __name__ == "__main__":
    main()
