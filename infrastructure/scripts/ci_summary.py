"""Evaluate CI reports, write GitHub job summaries and enforce the quality gate.

Subcommands (stdlib only):
    junit <title> <xml>        counts; fails on missing report, failures, errors, skips, 0 tests
    coverage <xml>             total coverage of the combined report
    bandit|pip-audit|gitleaks|trivy <json...>   number of findings in scanner reports
    gate                       checks NEEDS_JSON (toJSON(needs)) and all mandatory test reports

Reports never contain document contents: tests use synthetic data only and scanners redact.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses CI-generated reports only
from pathlib import Path


def emit(markdown: str) -> None:
    print(markdown)
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(markdown + "\n")


def junit_counts(path: Path) -> dict[str, int]:
    root = ET.parse(path).getroot()  # nosec B314 - trusted, self-generated file
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    keys = ("tests", "failures", "errors", "skipped")
    counts = {key: sum(int(s.get(key, 0)) for s in suites) for key in keys}
    counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    return counts


def junit_problems(path: Path) -> tuple[dict[str, int] | None, list[str]]:
    if not path.is_file():
        return None, [f"{path.as_posix()}: report missing"]
    counts = junit_counts(path)
    problems = []
    if counts["tests"] == 0:
        problems.append(f"{path.name}: no tests collected")
    if counts["failures"] or counts["errors"]:
        problems.append(f"{path.name}: {counts['failures'] + counts['errors']} failed")
    if counts["skipped"]:
        problems.append(f"{path.name}: {counts['skipped']} skipped (not allowed in CI)")
    return counts, problems


def cmd_junit(title: str, report: str) -> int:
    counts, problems = junit_problems(Path(report))
    if counts:
        emit(
            f"### {title}\n\n| Passed | Failed | Errors | Skipped | Total |\n"
            "|---|---|---|---|---|\n"
            f"| {counts['passed']} | {counts['failures']} | {counts['errors']} "
            f"| {counts['skipped']} | {counts['tests']} |\n"
        )
    for problem in problems:
        emit(f"- :x: {problem}")
    return 1 if problems else 0


def coverage_percent(path: Path) -> float:
    # Same metric as `coverage report` / fail_under: (lines + branches) covered / valid.
    root = ET.parse(path).getroot()  # nosec B314 - trusted, self-generated file
    covered = int(root.get("lines-covered", 0)) + int(root.get("branches-covered", 0))
    valid = int(root.get("lines-valid", 0)) + int(root.get("branches-valid", 0))
    return round(100 * covered / valid, 1) if valid else 0.0


def cmd_coverage(report: str) -> int:
    path = Path(report)
    if not path.is_file():
        emit("### Coverage\n\n:x: coverage.xml missing")
        return 1
    emit(
        f"### Coverage\n\nCoverage (lines + branches, all suites): **{coverage_percent(path)} %**\n"
    )
    return 0


def count_findings(kind: str, path: Path) -> int:
    data = json.loads(path.read_text("utf-8") or "null")
    if kind == "bandit":
        return len(data.get("results", []))
    if kind == "pip-audit":
        return sum(len(dep.get("vulns", [])) for dep in data.get("dependencies", []))
    if kind == "gitleaks":
        return len(data or [])
    if kind == "trivy":
        return sum(len(r.get("Vulnerabilities") or []) for r in data.get("Results", []))
    raise ValueError(kind)


def finding_details(kind: str, path: Path) -> str:
    data = json.loads(path.read_text("utf-8") or "null")
    if kind == "pip-audit":
        return "<br>".join(
            f"{dep['name']} {dep['version']}: {vuln['id']} (fix: {', '.join(vuln['fix_versions'])})"
            for dep in data.get("dependencies", [])
            for vuln in dep.get("vulns", [])
        )
    if kind == "trivy":
        severities: dict[str, int] = {}
        for result in data.get("Results", []):
            for vuln in result.get("Vulnerabilities") or []:
                severity = vuln.get("Severity", "UNKNOWN")
                severities[severity] = severities.get(severity, 0) + 1
        return ", ".join(f"{key}: {value}" for key, value in sorted(severities.items()))
    if kind == "bandit":
        return ", ".join(
            f"{key.removeprefix('SEVERITY.')}: {int(value)}"
            for key, value in data.get("metrics", {}).get("_totals", {}).items()
            if key.startswith("SEVERITY.") and value
        )
    return ""


def cmd_scanner(kind: str, reports: list[str]) -> int:
    rows = []
    for report in reports:
        path = Path(report)
        if path.is_file():
            found, details = count_findings(kind, path), finding_details(kind, path)
        else:
            found, details = "report missing", ""
        rows.append(f"| {path.name} | {found} | {details} |")
    emit(f"### {kind}\n\n| Report | Findings | Details |\n|---|---|---|\n" + "\n".join(rows) + "\n")
    return 0


def cmd_gate() -> int:
    needs = json.loads(os.environ.get("NEEDS_JSON", "{}"))
    reports = Path(os.environ.get("REPORTS_DIR", "reports"))
    expected = [name for name in os.environ.get("MANDATORY_JOBS", "").split() if name]
    problems = [] if expected else ["MANDATORY_JOBS is empty: nothing would be enforced"]
    rows = []
    for job in expected:
        result = needs.get(job, {}).get("result", "missing")
        rows.append(f"| {job} | {'✅' if result == 'success' else '❌'} {result} |")
        if result != "success":
            problems.append(f"job '{job}' result is '{result}'")
    unexpected = set(needs) - set(expected)
    if unexpected:
        problems.append(f"jobs not declared mandatory: {sorted(unexpected)}")
    tests = []
    for suite in ("unit", "integration", "security"):
        counts, suite_problems = junit_problems(reports / f"junit-{suite}.xml")
        problems += suite_problems
        if counts:
            tests.append(
                f"| {suite} | {counts['passed']} | {counts['failures'] + counts['errors']} "
                f"| {counts['skipped']} |"
            )
    coverage_file = reports / "coverage.xml"
    coverage = f"{coverage_percent(coverage_file)} %" if coverage_file.is_file() else "missing"
    if coverage == "missing":
        problems.append("combined coverage report missing")
    verdict = "❌ FAILED" if problems else "✅ PASSED"
    emit(
        f"## ThesisHounds CI Quality Gate: {verdict}\n\n| Job | Result |\n|---|---|\n"
        + "\n".join(rows)
        + "\n\n| Suite | Passed | Failed | Skipped |\n|---|---|---|---|\n"
        + "\n".join(tests)
        + f"\n\n**Coverage:** {coverage}\n"
    )
    for problem in problems:
        emit(f"- :x: {problem}")
    return 1 if problems else 0


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not argv:
        print(__doc__)
        return 2
    command, *args = argv
    if command == "junit" and len(args) == 2:
        return cmd_junit(*args)
    if command == "coverage" and len(args) == 1:
        return cmd_coverage(args[0])
    if command in {"bandit", "pip-audit", "gitleaks", "trivy"} and args:
        return cmd_scanner(command, args)
    if command == "gate" and not args:
        return cmd_gate()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
