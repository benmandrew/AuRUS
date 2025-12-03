from pathlib import Path
import bisect
from dataclasses import dataclass
import difflib
from termcolor import colored
import argparse


@dataclass
class RepairRecord:
    score: float
    runs: list[tuple[str, str]]
    

def add_repair(repair_map: dict[str, RepairRecord], contents: str, score: float, run_name: str, file_name: str):
    if contents in repair_map:
        repair_map[contents].runs.append((run_name, file_name))
    else:
        repair_map[contents] = RepairRecord(score, [(run_name, file_name)])

case_study_dir = Path("case-studies")
original_spec = (case_study_dir / "arbiter" / "arbiter.tlsf").read_text().splitlines()
original_spec = [line.strip() for line in original_spec]

seen: set[str] = set()


def color_diff(line: str) -> str:
    if line.startswith(' '):
        return line
    if line.startswith('-'):
        color = 'red'
    elif line.startswith('+'):
        color = 'green'
    else:
        color = 'white'
    return colored(line, color)


START_RANK = 0
N_RANKS = 20

def main():
    ap = argparse.ArgumentParser(description="Rank runs")
    ap.add_argument("data_dir", nargs="?", default="25-10-30-original-arbiter/arbiter-70-10-10-10",
                    help="Root folder containing run_* subfolders")
    data_directory = Path(ap.parse_args().data_dir)
    runs = list(data_directory.glob("run_*"))
    n_runs = len(runs)
    scores: list[tuple[float, float, float, str, str, str]] = []

    repair_map: dict[str, RepairRecord] = {}
    for i, run in enumerate(runs, start=1):
        # print(f"Run {i}/{n_runs}: {run.name}")
        for spec_file in run.glob("spec*.tlsf"):
            file_name = spec_file.name
            with open(spec_file) as f:
                contents = f.read()
                fitness_score = None
                syntactic_score = None
                semantic_score = None
                for line in contents.splitlines():
                    if line.startswith("//fitness: "):
                        fitness_score = float(line.split()[1])
                    if line.startswith("//syntactic: "):
                        syntactic_score = float(line.split()[1])
                    if line.startswith("//semantic: "):
                        semantic_score = float(line.split()[1])
                assert fitness_score is not None and syntactic_score is not None and semantic_score is not None, f"Missing scores in {run.name}/{file_name}"
                bisect.insort(scores, (fitness_score, syntactic_score, semantic_score, run.name, file_name, contents), key=lambda x: -x[0])
                add_repair(repair_map, contents, fitness_score, run.name, file_name)

    print("Overall ranking:")
    rank = 1
    for fitness_score, syntactic_score, semantic_score, run_name, file_name, contents in scores:
        if rank > START_RANK + N_RANKS:
            break
        if contents in seen:
            continue
        seen.add(contents)
        if rank <= START_RANK:
            rank += 1
            continue
        print(f"{rank}: fitness {fitness_score:.4f}, syntactic {syntactic_score:.4f}, semantic {semantic_score:.4f} - {len(repair_map[contents].runs)} runs - e.g. {run_name}/{file_name}")
        rank += 1
        
        lines = contents.splitlines()
        lines = [line for line in lines if not line.startswith("//")]
        lines = [line.strip() for line in lines]
        
        for line in difflib.unified_diff(original_spec, lines, n=1):
            if line.startswith('---') or line.startswith('+++') or line.startswith('@@') or line.isspace():
                continue
            print(color_diff(line))
        print()


if __name__ == "__main__":
    main()
