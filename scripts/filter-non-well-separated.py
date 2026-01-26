
import argparse
from pathlib import Path
import os
import subprocess
import shutil


def main():
    ap = argparse.ArgumentParser(description="Plot fitness scores with histogram.")
    ap.add_argument("data_dir", type=str, 
                    help="Folder containing run_* subfolders. Pass a parent directory to plot all subdirectories.")
    args = ap.parse_args()
    parent_dir = Path(args.data_dir)
    subdirs = sorted([d for d in parent_dir.iterdir() if d.is_dir()])
    for data_dir in subdirs:
        for run_dir in data_dir.iterdir():
            for tlsf in run_dir.glob("spec*.tlsf"):
                absolute_path = tlsf.resolve()
                suffix = os.sep.join(str(tlsf).split(os.sep)[-3:])
                # print("data/25-10-30-original-arbiter-filter-well-separated/" + suffix)
                output = subprocess.run(["bash", "scripts/is-well-separated.sh", f"-f={str(absolute_path)}"], stdout=subprocess.PIPE).stdout.decode('utf-8')
                print(output, end="")
                if "Well-separated" in output:
                    os.makedirs(f"data/25-10-30-original-arbiter-filter-well-separated/{os.path.dirname(suffix)}", exist_ok=True)
                    shutil.copy(absolute_path, f"data/25-10-30-original-arbiter-filter-well-separated/{suffix}")


if __name__ == "__main__":
    main()
