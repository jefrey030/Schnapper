#!/usr/bin/env python3
"""Cost-free unit-test evidence. PASS_UNIT_ONLY is never a production release approval."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import tempfile


def run_suite(root: pathlib.Path, name: str, cmd: list[str], count_pattern: str, report_dir: pathlib.Path) -> dict:
    try:
        completed = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=180, check=False)
        output = completed.stdout + "\n" + completed.stderr
        exit_code = completed.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        output, exit_code = f"UNABLE TO RUN: {type(exc).__name__}: {exc}\n", -1
    (report_dir / f"{name}.log").write_text(output, encoding="utf-8")
    counts = re.findall(count_pattern, output, flags=re.MULTILINE)
    tests = int(counts[-1]) if counts else 0
    # A runner that merely skips tests is not a passed acceptance run.
    if name == "python":
        skipped = bool(re.search(r"\b(?:skipped|expected failures|unexpected successes)\s*=\s*[1-9]", output))
    else:
        skipped = any(int(v) > 0 for key in ("skipped", "todo", "cancelled", "fail")
                      for v in re.findall(rf"^# {key} (\d+)\s*$", output, re.MULTILINE))
        passed = re.findall(r"^# pass (\d+)\s*$", output, re.MULTILINE)
        if not passed or int(passed[-1]) != tests:
            skipped = True
    return {"suite": name, "status": "PASS" if exit_code == 0 and tests > 0 and not skipped else "FAIL",
            "exit_code": exit_code, "tests_reported": tests, "skipped_or_incomplete": skipped,
            "log": f"{name}.log"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SCHNAPPER: offline Python+Node unit acceptance (not E2E)")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("--report-dir", type=pathlib.Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    reports = (args.report_dir or pathlib.Path(tempfile.mkdtemp(prefix="schnapper-unit-"))).resolve()
    reports.mkdir(parents=True, exist_ok=True)
    sha = "UNKNOWN"
    try:
        git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                             text=True, timeout=5, check=False)
        if git.returncode == 0 and re.fullmatch(r"[0-9a-f]{40,64}", git.stdout.strip()):
            sha = git.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    python_files = list((root / "tests").glob("test_*.py"))
    node_files = sorted((root / "cloudflare" / "test").glob("*.test.mjs"))
    suites = []
    if python_files:
        suites.append(run_suite(root, "python", [sys.executable, "-X", "dev", "-W", "error", "-m", "unittest",
                                                 "discover", "-s", "tests", "-v"], r"^Ran (\d+) tests? in ", reports))
    else:
        suites.append({"suite": "python", "status": "FAIL", "tests_reported": 0, "error": "No Python test files"})
    if node_files:
        suites.append(run_suite(root, "node", ["node", "--test", *(str(p) for p in node_files)],
                                r"^# tests (\d+)\s*$", reports))
    else:
        suites.append({"suite": "node", "status": "FAIL", "tests_reported": 0, "error": "No Node test files"})
    ok = sha != "UNKNOWN" and all(s["status"] == "PASS" for s in suites)
    summary = {"scope": "offline_unit_only", "production_release_approved": False,
               "e2e_verified": False, "github_ci_verified": False, "commit": sha,
               "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "result": "PASS_UNIT_ONLY" if ok else "FAIL", "suites": suites}
    (reports / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report_dir": str(reports), **summary}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
