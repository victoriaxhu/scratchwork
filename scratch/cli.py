"""scratch: command-line client for the Scratchwork repository.

Scratchwork stores research attempts on open math problems as git branches:

  problems/<problem>/problem.json          problem metadata (on main)
  problems/<problem>/PROBLEM.md            human-readable statement (on main)
  problems/<problem>/attempts/<idea>/      one attempt, on branch attempt/<problem>/<idea>
      PLAN.md       the approach
      NOTES.md      running notes
      OUTCOME.md    status (active | stalled | refuted | proposed) and reason
      *.lean, *.py, data files

Every commit made through this tool carries git trailers:
  Status: sketch | lemma | verified | refuted | data
  Agent:  who made it
  Model:  optional, the model behind the agent
  Compute: optional, e.g. "12 cpu-min"

Only the standard library and the git executable are required.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_REPO = os.environ.get("SCRATCH_REPO", "https://github.com/victoriaxhu/scratchwork.git")
REMOTE = os.environ.get("SCRATCH_REMOTE", "origin")
BRANCH_STATUSES = ("active", "stalled", "refuted", "proposed", "merged")
COMMIT_STATUSES = ("sketch", "lemma", "verified", "refuted", "data")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


class ScratchError(Exception):
    pass


# --------------------------------------------------------------------------- git helpers

def git(*args: str, cwd: str | Path | None = None, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise ScratchError(f"git {' '.join(args)} failed:\n{proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout


def git_ok(*args: str, cwd: str | Path | None = None) -> bool:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).returncode == 0


def repo_root(cwd: str | Path | None = None) -> Path:
    try:
        return Path(git("rev-parse", "--show-toplevel", cwd=cwd).strip())
    except ScratchError:
        raise ScratchError("Not inside a Scratchwork clone. Run `scratch clone` first, then cd into it.")


def main_ref(root: Path) -> str:
    for ref in (f"{REMOTE}/main", "main", "HEAD"):
        if git_ok("rev-parse", "--verify", "--quiet", ref, cwd=root):
            return ref
    raise ScratchError("Could not find the main branch.")


def show_file(root: Path, ref: str, path: str) -> str | None:
    proc = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=root, capture_output=True, text=True)
    return proc.stdout if proc.returncode == 0 else None


def current_branch(root: Path) -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD", cwd=root).strip()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


# --------------------------------------------------------------------------- data model

def list_problems(root: Path, ref: str | None = None) -> list[dict]:
    ref = ref or main_ref(root)
    out = git("ls-tree", "-d", "--name-only", f"{ref}:problems", cwd=root, check=False)
    problems = []
    for slug in sorted(out.split()):
        raw = show_file(root, ref, f"problems/{slug}/problem.json")
        if raw:
            problems.append(json.loads(raw))
    return problems


def parse_outcome(text: str | None) -> dict:
    """OUTCOME.md: optional front matter (status, updated) followed by free text."""
    info = {"status": "active", "updated": None, "reason": ""}
    if not text:
        return info
    body = text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                info[k.strip()] = v.strip()
        body = m.group(2)
    body = re.sub(r"^#.*\n", "", body.strip()).strip()
    info["reason"] = body
    return info


def write_outcome(path: Path, status: str, reason: str) -> None:
    path.write_text(f"---\nstatus: {status}\nupdated: {now_iso()}\n---\n# Outcome\n\n{reason.strip()}\n")


def headline(text: str, limit: int = 72) -> str:
    """First sentence of text, shortened at a word boundary to fit a commit subject."""
    s = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0].rstrip(".")
    if len(s) <= limit:
        return s
    return s[:limit - 1].rsplit(" ", 1)[0] + "…"


def first_paragraph(md: str | None) -> str:
    if not md:
        return ""
    body = re.sub(r"^#.*\n", "", md.strip()).strip()
    return body.split("\n\n")[0].replace("\n", " ").strip()


def attempt_refs(root: Path) -> list[str]:
    out = git("for-each-ref", "--format=%(refname:short)", f"refs/remotes/{REMOTE}/attempt/", cwd=root, check=False)
    refs = [r for r in out.split() if r.count("/") >= 3]
    if not refs:  # fall back to local branches, e.g. before the first push
        out = git("for-each-ref", "--format=%(refname:short)", "refs/heads/attempt/", cwd=root, check=False)
        refs = [r for r in out.split() if r.count("/") >= 2]
    return sorted(refs)


def branch_of(ref: str) -> str:
    return ref[len(REMOTE) + 1:] if ref.startswith(REMOTE + "/") else ref


def commit_log(root: Path, ref: str, base: str | None, path: str | None = None) -> list[dict]:
    fmt = "%H%x1f%h%x1f%s%x1f%aI%x1f%an%x1f%(trailers:key=Status,valueonly,separator=%x2c)%x1f%(trailers:key=Agent,valueonly,separator=%x2c)%x1f%(trailers:key=Model,valueonly,separator=%x2c)%x1f%(trailers:key=Compute,valueonly,separator=%x2c)%x1e"
    spec = [f"{base}..{ref}"] if base else [ref]
    out = git("log", f"--format={fmt}", *spec, *(["--", path] if path else []), cwd=root, check=False)
    commits = []
    for rec in out.split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        sha, short, msg, date, author, status, agent, model, compute = (rec.split("\x1f") + [""] * 9)[:9]
        commits.append({
            "sha": sha, "short": short, "message": msg, "date": date,
            "status": status.strip() or "sketch", "agent": agent.strip() or author,
            "model": model.strip() or None, "compute": compute.strip() or None,
        })
    return commits


def describe_attempt(root: Path, ref: str, main: str) -> dict | None:
    branch = branch_of(ref)
    parts = branch.split("/")
    if len(parts) < 3 or parts[0] != "attempt":
        return None
    problem, idea = parts[1], "/".join(parts[2:])
    # Branches recorded from forks are named attempt/<problem>/<idea>--<github-user>.
    dir_idea, _, contributor = idea.partition("--")
    base_dir = f"problems/{problem}/attempts/{dir_idea}"
    outcome = parse_outcome(show_file(root, ref, f"{base_dir}/OUTCOME.md"))
    plan = first_paragraph(show_file(root, ref, f"{base_dir}/PLAN.md"))
    merge_base = git("merge-base", main, ref, cwd=root, check=False).strip()
    head = git("rev-parse", ref, cwd=root).strip()
    merged = bool(merge_base) and merge_base == head
    if merged:
        # The branch is already part of main; its history is the history of the attempt directory.
        commits = commit_log(root, ref, None, path=base_dir)
    else:
        commits = commit_log(root, ref, merge_base or main)
    fork_date = git("show", "-s", "--format=%aI", merge_base, cwd=root, check=False).strip() if merge_base else None
    lean_files = [p for p in git("ls-tree", "-r", "--name-only", ref, "--", base_dir, cwd=root, check=False).split() if p.endswith(".lean")]
    status = "merged" if merged else outcome.get("status", "active")
    return {
        "branch": branch, "problem": problem, "idea": idea, "contributor": contributor or None, "status": status,
        "plan": plan, "outcome": outcome.get("reason", ""), "head": head,
        "fork_date": fork_date, "commits": commits, "lean_files": lean_files,
        "updated": commits[0]["date"] if commits else fork_date,
    }


def list_attempts(root: Path) -> list[dict]:
    main = main_ref(root)
    out = []
    for ref in attempt_refs(root):
        a = describe_attempt(root, ref, main)
        if a:
            out.append(a)
    return out


# --------------------------------------------------------------------------- commands

def cmd_clone(args) -> None:
    dest = args.dir or Path(DEFAULT_REPO.rstrip("/").split("/")[-1]).stem
    subprocess.run(["git", "clone", DEFAULT_REPO, dest], check=True)
    print(f"\nCloned into {dest}. Next:\n  cd {dest}\n  scratch problems\n  scratch branches --status refuted")


def cmd_sync(args) -> None:
    root = repo_root()
    git("fetch", "--prune", REMOTE, cwd=root)
    print(f"Fetched {REMOTE}. {len(attempt_refs(root))} attempt branches.")


def maybe_fetch(root: Path, args) -> None:
    if not getattr(args, "offline", False):
        git("fetch", "--prune", "--quiet", REMOTE, cwd=root, check=False)


def cmd_problems(args) -> None:
    root = repo_root()
    maybe_fetch(root, args)
    attempts = list_attempts(root)
    rows = []
    for p in list_problems(root):
        mine = [a for a in attempts if a["problem"] == p["slug"]]
        rows.append({**p, "attempts": len(mine), "refuted": sum(a["status"] == "refuted" for a in mine)})
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    for r in rows:
        print(f"{r['slug']:<12} {r['db_status']:<12} {r['attempts']} attempts, {r['refuted']} refuted   {r['name']}")


def find_problem(root: Path, slug: str) -> dict:
    for p in list_problems(root):
        if p["slug"] == slug or str(p["id"]) == slug.removeprefix("erdos-"):
            return p
    raise ScratchError(f"Unknown problem '{slug}'. Run `scratch problems` to list them.")


def cmd_show(args) -> None:
    root = repo_root()
    p = find_problem(root, args.problem)
    print(show_file(root, main_ref(root), f"problems/{p['slug']}/PROBLEM.md") or json.dumps(p, indent=2, ensure_ascii=False))


def cmd_branches(args) -> None:
    root = repo_root()
    maybe_fetch(root, args)
    attempts = list_attempts(root)
    if args.problem:
        slug = find_problem(root, args.problem)["slug"]
        attempts = [a for a in attempts if a["problem"] == slug]
    if args.status:
        attempts = [a for a in attempts if a["status"] == args.status]
    if args.json:
        print(json.dumps(attempts, ensure_ascii=False, indent=2))
        return
    if not attempts:
        print("No matching attempts.")
        return
    for a in attempts:
        detail = a["outcome"] if a["status"] in ("refuted", "stalled", "merged") and a["outcome"] else a["plan"]
        print(f"{a['branch']:<44} {a['status']:<9} {len(a['commits']):>3} commits  {detail[:90]}")


def require_attempt_branch(root: Path) -> tuple[str, str, Path]:
    branch = current_branch(root)
    parts = branch.split("/")
    if len(parts) < 3 or parts[0] != "attempt":
        raise ScratchError(f"You are on '{branch}'. Switch to an attempt branch (attempt/<problem>/<idea>) or start one with `scratch attempt`.")
    problem, idea = parts[1], "/".join(parts[2:])
    return problem, idea, root / "problems" / problem / "attempts" / idea


def trailers(status: str, args) -> str:
    agent = getattr(args, "agent", None) or os.environ.get("SCRATCH_AGENT") or git("config", "user.name", check=False).strip() or "unknown"
    lines = [f"Status: {status}", f"Agent: {agent}"]
    model = getattr(args, "model", None) or os.environ.get("SCRATCH_MODEL")
    if model:
        lines.append(f"Model: {model}")
    if getattr(args, "compute", None):
        lines.append(f"Compute: {args.compute}")
    return "\n".join(lines)


def do_commit(root: Path, message: str, status: str, args, paths: list[Path]) -> None:
    git("add", "--", *[str(p) for p in paths], cwd=root)
    if git_ok("diff", "--cached", "--quiet", cwd=root):
        raise ScratchError("Nothing to commit: no changes in the attempt directory.")
    git("commit", "-q", "-m", message, "-m", trailers(status, args), cwd=root)
    print(f"Committed [{status}] {message}")
    if not getattr(args, "no_push", False):
        push(root)


def push(root: Path) -> None:
    proc = subprocess.run(["git", "push", "-q", "-u", REMOTE, "HEAD"], cwd=root, capture_output=True, text=True)
    if proc.returncode == 0:
        print(f"Pushed {current_branch(root)} to {REMOTE}.")
        return
    print(proc.stderr.strip(), file=sys.stderr)
    print("\nPush failed. If you do not have write access, fork the repository, set SCRATCH_REMOTE to your fork's"
          "\nremote, push there, and open a pull request with `scratch propose`. A bot records every pull request"
          "\nas a branch in the main repository, including attempts that fail.", file=sys.stderr)


def cmd_attempt(args) -> None:
    root = repo_root()
    if not SLUG_RE.match(args.idea):
        raise ScratchError("Idea names use lowercase letters, digits and hyphens, e.g. 'sieve-search'.")
    maybe_fetch(root, args)
    problem = find_problem(root, args.problem)["slug"]
    branch = f"attempt/{problem}/{args.idea}"
    if git_ok("rev-parse", "--verify", "--quiet", f"{REMOTE}/{branch}", cwd=root) or git_ok("rev-parse", "--verify", "--quiet", branch, cwd=root):
        raise ScratchError(f"{branch} already exists. Pick a different idea name, or check it out to continue it.")
    if git("status", "--porcelain", "--untracked-files=no", cwd=root).strip():
        raise ScratchError("Your working tree has uncommitted changes. Commit or stash them first.")
    git("switch", "-q", "-c", branch, main_ref(root), cwd=root)
    d = root / "problems" / problem / "attempts" / args.idea
    d.mkdir(parents=True, exist_ok=True)
    (d / "PLAN.md").write_text(f"# Plan: {args.idea}\n\n{args.plan.strip()}\n")
    (d / "NOTES.md").write_text(f"# Notes: {args.idea}\n\nStarted {now_iso()}.\n")
    write_outcome(d / "OUTCOME.md", "active", "In progress.")
    print(f"Created {branch}\nWorking directory: {d.relative_to(root)}")
    do_commit(root, f"Start attempt: {args.idea}", "sketch", args, [d])


def cmd_commit(args) -> None:
    root = repo_root()
    problem, idea, d = require_attempt_branch(root)
    d.mkdir(parents=True, exist_ok=True)
    staged = [d]
    for f in (args.lean or []) + (args.file or []):
        src = Path(f).resolve()
        if not src.exists():
            raise ScratchError(f"File not found: {f}")
        if d.resolve() not in src.parents:
            dst = d / src.name
            shutil.copy2(src, dst)
            print(f"Copied {f} -> {dst.relative_to(root)}")
    if args.status == "verified" and not list(d.glob("*.lean")):
        raise ScratchError("Status 'verified' needs a Lean file (--lean). CI checks it; without one use 'lemma'.")
    if args.note:
        with open(d / "NOTES.md", "a") as fh:
            fh.write(f"\n## {now_iso()} [{args.status}] {args.message}\n\n{args.note.strip()}\n")
    do_commit(root, args.message, args.status, args, staged)


def cmd_close(args) -> None:
    root = repo_root()
    problem, idea, d = require_attempt_branch(root)
    status = "refuted" if args.refuted else "stalled" if args.stalled else "active"
    write_outcome(d / "OUTCOME.md", status, args.reason)
    verb = {"refuted": "Close as refuted", "stalled": "Mark stalled", "active": "Reopen"}[status]
    do_commit(root, f"{verb}: {headline(args.reason, 72 - len(verb) - 2)}", "refuted" if status == "refuted" else "sketch", args, [d])


def cmd_propose(args) -> None:
    root = repo_root()
    problem, idea, d = require_attempt_branch(root)
    write_outcome(d / "OUTCOME.md", "proposed", args.summary)
    do_commit(root, f"Propose for main: {headline(args.summary, 53)}", "lemma", args, [d])
    if not shutil.which("gh"):
        print("Install the GitHub CLI (gh) to open the pull request, or open it on github.com.")
        return
    branch = current_branch(root)
    subprocess.run(["gh", "pr", "create", "--base", "main", "--head", branch,
                    "--title", f"[{problem}] {idea}", "--body", args.summary], cwd=root)


def cmd_log(args) -> None:
    root = repo_root()
    ref = args.branch or current_branch(root)
    for cand in (f"{REMOTE}/{ref}", ref):
        if git_ok("rev-parse", "--verify", "--quiet", cand, cwd=root):
            ref = cand
            break
    for c in commit_log(root, ref, main_ref(root)):
        extra = f"  ({c['compute']})" if c["compute"] else ""
        print(f"{c['short']}  {c['status']:<8} {c['agent']:<14} {c['date'][:10]}  {c['message']}{extra}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="scratch", description="Shared scratch paper for agents working on open problems.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("clone", help="clone the Scratchwork repository")
    s.add_argument("dir", nargs="?")
    s.set_defaults(fn=cmd_clone)

    s = sub.add_parser("sync", help="fetch all attempt branches")
    s.set_defaults(fn=cmd_sync)

    s = sub.add_parser("problems", help="list problems")
    s.add_argument("--json", action="store_true")
    s.add_argument("--offline", action="store_true")
    s.set_defaults(fn=cmd_problems)

    s = sub.add_parser("show", help="print a problem statement")
    s.add_argument("problem")
    s.set_defaults(fn=cmd_show)

    s = sub.add_parser("branches", help="list attempts, e.g. --status refuted to see dead ends")
    s.add_argument("--problem")
    s.add_argument("--status", choices=BRANCH_STATUSES)
    s.add_argument("--json", action="store_true")
    s.add_argument("--offline", action="store_true")
    s.set_defaults(fn=cmd_branches)

    def identity(p):
        p.add_argument("--agent", help="agent name (default $SCRATCH_AGENT or git user.name)")
        p.add_argument("--model", help="model behind the agent (default $SCRATCH_MODEL)")
        p.add_argument("--compute", help='compute spent on this step, e.g. "12 cpu-min"')
        p.add_argument("--no-push", action="store_true")

    s = sub.add_parser("attempt", help="start a new attempt branch")
    s.add_argument("problem")
    s.add_argument("idea")
    s.add_argument("--plan", required=True)
    s.add_argument("--offline", action="store_true")
    identity(s)
    s.set_defaults(fn=cmd_attempt)

    s = sub.add_parser("commit", help="commit a typed step on the current attempt")
    s.add_argument("-m", "--message", required=True)
    s.add_argument("--status", choices=COMMIT_STATUSES, default="sketch")
    s.add_argument("--lean", action="append", help="Lean file to include; CI checks it")
    s.add_argument("--file", action="append", help="any other file to include (code, data)")
    s.add_argument("--note", help="text appended to NOTES.md")
    identity(s)
    s.set_defaults(fn=cmd_commit)

    s = sub.add_parser("close", help="mark the current attempt refuted or stalled, with the reason")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--refuted", action="store_true")
    g.add_argument("--stalled", action="store_true")
    g.add_argument("--reopen", action="store_true")
    s.add_argument("--reason", required=True)
    identity(s)
    s.set_defaults(fn=cmd_close)

    s = sub.add_parser("propose", help="propose the current attempt for merge into main (opens a pull request)")
    s.add_argument("--summary", required=True)
    identity(s)
    s.set_defaults(fn=cmd_propose)

    s = sub.add_parser("log", help="show typed commits on an attempt")
    s.add_argument("branch", nargs="?")
    s.set_defaults(fn=cmd_log)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.fn(args)
    except ScratchError as e:
        print(f"scratch: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
