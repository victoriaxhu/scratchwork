"""Build site/data/index.json from the repository's branches.

Usage: python tools/build_index.py [--out _site/data/index.json]

Reads problems from main and every attempt/* branch. When GITHUB_TOKEN and
GITHUB_REPOSITORY are set (in CI), it also looks up the "Lean check" result
for each branch head, so the site only shows a step as verified when Lean
actually accepted it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scratch.cli import list_attempts, list_problems, main_ref, now_iso, repo_root  # noqa: E402

LEAN_CHECK_NAME = "Lean check"


def lean_status(sha: str) -> str:
    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not (token and repo):
        return "unknown"
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/commits/{sha}/check-runs?check_name={LEAN_CHECK_NAME.replace(' ', '%20')}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            runs = json.load(r).get("check_runs", [])
    except Exception as e:  # network errors should not break the site build
        print(f"warning: check-runs lookup failed for {sha[:7]}: {e}", file=sys.stderr)
        return "unknown"
    if not runs:
        return "pending"
    run = max(runs, key=lambda x: x.get("started_at") or "")
    if run.get("status") != "completed":
        return "pending"
    return {"success": "pass", "failure": "fail", "skipped": "none"}.get(run.get("conclusion"), run.get("conclusion") or "unknown")


def build() -> dict:
    root = repo_root()
    problems = list_problems(root)
    attempts = list_attempts(root)
    for a in attempts:
        a["lean"] = lean_status(a["head"]) if a["lean_files"] else "none"
        # A "verified" claim only stands if Lean accepted the branch head.
        for c in a["commits"]:
            c["verified"] = c["status"] == "verified" and a["lean"] == "pass"
    by_problem: dict[str, list] = {}
    for a in attempts:
        by_problem.setdefault(a["problem"], []).append(a)
    for p in problems:
        p["attempts"] = sorted(by_problem.get(p["slug"], []), key=lambda a: a["fork_date"] or "")
    recent = sorted(
        ({**c, "branch": a["branch"], "problem": a["problem"]} for a in attempts for c in a["commits"]),
        key=lambda c: c["date"], reverse=True,
    )[:50]
    repo = os.environ.get("GITHUB_REPOSITORY", "victoriaxhu/scratchwork")
    return {
        "generated": now_iso(),
        "repo": repo,
        "repo_url": f"https://github.com/{repo}",
        "main": main_ref(root),
        "problems": problems,
        "recent": recent,
        "totals": {
            "problems": len(problems),
            "attempts": len(attempts),
            "refuted": sum(a["status"] == "refuted" for a in attempts),
            "commits": sum(len(a["commits"]) for a in attempts),
        },
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site/data/index.json")
    out = Path(ap.parse_args().out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build()
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    t = data["totals"]
    print(f"Wrote {out}: {t['problems']} problems, {t['attempts']} attempts, {t['commits']} commits")
