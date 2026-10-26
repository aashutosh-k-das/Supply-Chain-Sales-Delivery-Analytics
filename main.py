#!/usr/bin/env python3
"""
main.py
=======
Unified Master Pipeline Runner for Supply Chain Sales, Profitability & Delivery Performance Analytics.

Runs all pipeline phases in sequence:
  1. Data Cleaning (src/clean_data.py)
  2. Data Validation (src/validate_data.py)
  3. Business Analysis & Chart Generation (src/analyze_data.py)
  4. Machine Learning Delivery Risk Model (src/train_model.py)
  5. Automated Test Suite (pytest tests/test_pipeline.py)

Usage:
    python main.py
    python main.py --skip-tests
    python main.py --skip-ml
"""

import sys
import os
import time
import argparse
import subprocess
from pathlib import Path

# ANSI styling for clean terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

ROOT_DIR = Path(__file__).resolve().parent
PYTHON_BIN = sys.executable

def print_header(title: str):
    print(f"\n{CYAN}{BOLD}{'=' * 70}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * 70}{RESET}")

def run_step(step_name: str, cmd: list) -> bool:
    print(f"\n{YELLOW}▶ Running: {step_name}...{RESET}")
    print(f"  Command: {' '.join(cmd)}")
    start_time = time.time()
    result = subprocess.run(cmd, cwd=str(ROOT_DIR))
    elapsed = time.time() - start_time
    if result.returncode == 0:
        print(f"{GREEN}✓ {step_name} completed successfully ({elapsed:.2f}s){RESET}")
        return True
    else:
        print(f"{RED}✗ {step_name} failed with exit code {result.returncode} ({elapsed:.2f}s){RESET}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Supply Chain Analytics – Master Pipeline Runner")
    parser.add_argument("--skip-ml", action="store_true", help="Skip machine learning model training")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest test suite")
    parser.add_argument("--raw-data", default="data/raw/DataCoSupplyChainDataset.csv", help="Path to raw dataset")
    args = parser.parse_args()

    raw_path = ROOT_DIR / args.raw_data
    if not raw_path.exists():
        print(f"{RED}Error: Dataset not found at: {raw_path}{RESET}")
        print("Please place DataCoSupplyChainDataset.csv in data/raw/ before running.")
        sys.exit(1)

    print_header("SUPPLY CHAIN SALES & DELIVERY ANALYTICS — PIPELINE RUNNER")
    print(f"Project root : {ROOT_DIR}")
    print(f"Python binary: {PYTHON_BIN}")
    print(f"Raw dataset  : {raw_path}")

    total_start = time.time()
    steps_passed = 0
    total_steps = 3 + (0 if args.skip_ml else 1) + (0 if args.skip_tests else 1)

    # 1. Data Cleaning
    cmd_clean = [
        PYTHON_BIN, "src/clean_data.py",
        "--input", str(args.raw_data),
        "--output", "data/processed/supply_chain_clean.csv",
        "--report", "data/processed/cleaning_report.csv",
    ]
    if run_step("Phase 1: Data Cleaning", cmd_clean):
        steps_passed += 1
    else:
        sys.exit(1)

    # 2. Validation
    cmd_val = [
        PYTHON_BIN, "src/validate_data.py",
        "--input", "data/processed/supply_chain_clean.csv",
        "--report", "data/processed/validation_report.csv",
    ]
    if run_step("Phase 2: Post-Clean Validation", cmd_val):
        steps_passed += 1
    else:
        sys.exit(1)

    # 3. Business Analysis & Charts
    cmd_analysis = [
        PYTHON_BIN, "src/analyze_data.py",
        "--input", "data/processed/supply_chain_clean.csv",
        "--output-dir", "outputs",
    ]
    if run_step("Phase 3: Business Analytics & Visualization", cmd_analysis):
        steps_passed += 1
    else:
        sys.exit(1)

    # 4. Machine Learning Model
    if not args.skip_ml:
        cmd_ml = [PYTHON_BIN, "src/train_model.py"]
        if run_step("Phase 4: Late Delivery Risk ML Model", cmd_ml):
            steps_passed += 1
        else:
            sys.exit(1)

    # 5. Tests
    if not args.skip_tests:
        cmd_tests = [PYTHON_BIN, "-m", "pytest", "tests/test_pipeline.py", "-v"]
        if run_step("Phase 5: Automated Unit Tests (pytest)", cmd_tests):
            steps_passed += 1
        else:
            sys.exit(1)

    total_elapsed = time.time() - total_start
    print_header(f"ALL {steps_passed}/{total_steps} PHASES COMPLETED SUCCESSFULLY ({total_elapsed:.2f}s)")
    print(f"{GREEN}✓ Outputs available in: {ROOT_DIR / 'outputs'}{RESET}")
    print(f"{GREEN}✓ Visualizations in   : {ROOT_DIR / 'outputs' / 'charts'}{RESET}")
    print(f"{GREEN}✓ Model saved in      : {ROOT_DIR / 'models'}{RESET}")
    print(f"{GREEN}✓ Business report in  : {ROOT_DIR / 'reports' / 'insights_report.md'}{RESET}\n")

if __name__ == "__main__":
    main()
