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

ASSUMPTIONS_START = "ASSUMPTIONS {\n"
GUARANTEES_START = "GUARANTEES {\n"


def normalise_tlsf(contents: str) -> str:
    contents = "\n".join([line for line in contents.splitlines() if not line.startswith("//")])
    front = ""
    rest = contents
    if ASSUMPTIONS_START in contents:
        prefix, assumptions = contents.split(ASSUMPTIONS_START, maxsplit=1)
        assumptions, rest = assumptions.split("}\n", maxsplit=1)
        sorted_assumptions = "\n".join(sorted(assumptions.splitlines())[1:])
        front = prefix + ASSUMPTIONS_START + sorted_assumptions + "\n  }\n"
    middle, guarantees = rest.split(GUARANTEES_START, maxsplit=1)
    guarantees, rest = guarantees.split("}\n", maxsplit=1)
    sorted_guarantees = "\n".join(sorted(guarantees.splitlines())[1:])
    return front + middle + GUARANTEES_START + sorted_guarantees + "\n" + rest + "}\n"


def add_repair(repair_map: dict[str, RepairRecord], contents: str, score: float, run_name: str, file_name: str):
    tlsf = normalise_tlsf(contents)
    if tlsf in repair_map:
        repair_map[tlsf].runs.append((run_name, file_name))
    else:
        repair_map[tlsf] = RepairRecord(score, [(run_name, file_name)])


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


case_study_dir = Path("case-studies")
original_spec = normalise_tlsf((case_study_dir / "arbiter" / "arbiter.tlsf").read_text()).splitlines()
original_spec = [line.strip() for line in original_spec]

START_RANK = 0
N_RANKS = 1

def main():
    ap = argparse.ArgumentParser(description="Rank runs")
    ap.add_argument("specs_file", help="File containing paths of specs to compare")
    # Read the specs from the provided file
    with open(ap.parse_args().specs_file) as f:
        specs_to_compare = [line.strip() for line in f if line.strip()]
    scores: list[tuple[float, float, float, str, str, str]] = []
    repair_map: dict[str, RepairRecord] = {}
    for spec_path in specs_to_compare:
        spec_file = Path(spec_path)
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
            assert fitness_score is not None and syntactic_score is not None and semantic_score is not None, f"Missing scores in {spec_path}"
            bisect.insort(scores, (fitness_score, syntactic_score, semantic_score, spec_path, "", contents), key=lambda x: -x[1])
            add_repair(repair_map, contents, fitness_score, spec_path, spec_file.name)
    # print("Overall ranking:")
    rank = 1
    seen: set[str] = set()
    for fitness_score, syntactic_score, semantic_score, _run_name, _file_name, contents in scores:
        if rank > START_RANK + N_RANKS:
            break
        tlsf = normalise_tlsf(contents)
        if tlsf in seen:
            continue
        seen.add(tlsf)
        if rank <= START_RANK:
            rank += 1
            continue
        # print(f"{rank}: fitness {fitness_score:.4f}, syntactic {syntactic_score:.4f}, semantic {semantic_score:.4f}")
        rank += 1
        lines = tlsf.splitlines()
        lines = [line for line in lines if not line.startswith("//")]
        lines = [line.strip() for line in lines]
        for line in difflib.unified_diff(original_spec, lines, n=1):
            if line.startswith('---') or line.startswith('+++') or line.startswith('@@') or line.isspace():
                continue
            print(color_diff(line))
        print()


if __name__ == "__main__":
    main()
