import subprocess
import json
import sys
from pathlib import Path

# ANSI color codes
RESET   = "\033[0m"
BOLD    = "\033[1m"
YELLOW  = "\033[33m"
GREEN   = "\033[32m"
RED     = "\033[31m"
CYAN    = "\033[36m"
GRAY    = "\033[90m"

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def try_get_name(filename):
    for i, c in enumerate(filename):
        if c.isupper():
            start = i
            end = filename.find('.', start)
            if end == -1:
                return filename[start:]
            else:
                return filename[start:end]
    return filename

def get_current_benchmark(benchmark_script, target_dir=None):
    cmd = [sys.executable, benchmark_script, "--json"]
    if target_dir:
        cmd.extend(["--dir", target_dir])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"{RED}Error running benchmark script:\n{proc.stderr}{RESET}")
        sys.exit(1)
    return json.loads(proc.stdout)

def print_diff(old, new):
    print(f"\n{BOLD}{CYAN}--- BYTECODE SIZE (felts) ---{RESET}")
    compare_subdicts(old.get("bytecode", {}), new.get("bytecode", {}), "felts")

    print(f"\n{BOLD}{CYAN}--- SIERRA CONTRACT CLASS SIZE (bytes) ---{RESET}")
    compare_subdicts(old.get("contract_class", {}), new.get("contract_class", {}), "bytes")

def color_name(name):
    return f"{BOLD}{YELLOW}{name}{RESET}"

def compare_subdicts(old, new, metric):
    all_files = set(old.keys()) | set(new.keys())
    for file in sorted(all_files):
        old_val = old.get(file, {}).get(metric)
        new_val = new.get(file, {}).get(metric)
        file_name = color_name(try_get_name(file))
        if old_val is None and new_val is not None:
            value = f"{GREEN}{metric} = {new_val}{RESET}"
            print(f"{GREEN}+ {file_name}: {value} (NEW){RESET}")
        elif old_val is not None and new_val is None:
            value = f"{RED}{metric} = {old_val}{RESET}"
            print(f"{RED}- {file_name}: {value} (REMOVED){RESET}")
        elif old_val is not None and new_val is not None:
            if old_val == new_val:
                value = f"{GRAY}{metric} = {new_val} (no change){RESET}"
                print(f"{GRAY}= {file_name}: {value}")
            else:
                diff = new_val - old_val
                if diff > 0:
                    arrow = f"{GREEN}↑{RESET}"
                    old_s = f"{RED}{old_val}{RESET}"
                    new_s = f"{GREEN}{new_val}{RESET}"
                else:
                    arrow = f"{RED}↓{RESET}"
                    old_s = f"{RED}{old_val}{RESET}"
                    new_s = f"{RED}{new_val}{RESET}"
                print(f"* {file_name}: {old_s} → {new_s} ({arrow}{abs(diff)})")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Diff Cairo contract benchmarks.")
    parser.add_argument("benchmark_script", help="Path to benchmark.py")
    parser.add_argument("previous_json", help="Path to previous JSON benchmark file")
    parser.add_argument("--dir", type=str, help="Target directory for new benchmark (optional)")
    args = parser.parse_args()

    prev = load_json(args.previous_json)
    current = get_current_benchmark(args.benchmark_script, args.dir)
    print_diff(prev, current)
