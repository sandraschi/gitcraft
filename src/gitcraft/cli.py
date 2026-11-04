"""GitCraft CLI: Headless verbs for Git repository telemetry, PR inspection, and fleet dirty analysis."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def get_git_status(repo_dir: Path) -> dict[str, Any]:
    """Parse git repository status without mutating state."""
    if not (repo_dir / ".git").exists():
        raise ValueError(f"Not a git repository: {repo_dir}")

    proc = subprocess.run(
        ["git", "-C", str(repo_dir), "status", "--porcelain=v1", "-b"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    lines = proc.stdout.splitlines()
    branch = "unknown"
    upstream = None
    ahead = 0
    behind = 0
    staged: list[str] = []
    unstaged: list[str] = []
    untracked: list[str] = []

    if lines:
        header = lines[0]
        if header.startswith("## "):
            branch_info = header[3:]
            if "..." in branch_info:
                parts = branch_info.split("...")
                branch = parts[0]
                rest = parts[1]
                if " [" in rest:
                    up_part, track_part = rest.split(" [", 1)
                    upstream = up_part
                    track_part = track_part.rstrip("]")
                    for item in track_part.split(", "):
                        if item.startswith("ahead "):
                            ahead = int(item.replace("ahead ", ""))
                        elif item.startswith("behind "):
                            behind = int(item.replace("behind ", ""))
                else:
                    upstream = rest
            else:
                branch = branch_info

        for line in lines[1:]:
            if not line:
                continue
            x = line[0]
            y = line[1]
            path = line[3:]
            if x == "?" and y == "?":
                untracked.append(path)
            else:
                if x in "MADRC":
                    staged.append(path)
                if y in "MADU":
                    unstaged.append(path)

    is_clean = len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0

    return {
        "repo": str(repo_dir.resolve()),
        "branch": branch,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "is_clean": is_clean,
        "staged_count": len(staged),
        "unstaged_count": len(unstaged),
        "untracked_count": len(untracked),
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
    }


def get_git_log(repo_dir: Path, count: int = 10) -> dict[str, Any]:
    """Parse recent git commits."""
    if not (repo_dir / ".git").exists():
        raise ValueError(f"Not a git repository: {repo_dir}")

    delim = "\x1f"
    fmt = f"%H{delim}%h{delim}%an{delim}%ae{delim}%ad{delim}%s"
    proc = subprocess.run(
        ["git", "-C", str(repo_dir), "log", f"-n{count}", f"--format={fmt}"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    commits: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split(delim)
        if len(parts) >= 6:
            commits.append({
                "hash": parts[0],
                "short_hash": parts[1],
                "author": parts[2],
                "email": parts[3],
                "date": parts[4],
                "subject": parts[5],
            })

    return {
        "repo": str(repo_dir.resolve()),
        "commit_count": len(commits),
        "commits": commits,
    }


def get_git_diff(repo_dir: Path, staged: bool = False) -> dict[str, Any]:
    """Inspect working tree or staged diff without modifying index."""
    if not (repo_dir / ".git").exists():
        raise ValueError(f"Not a git repository: {repo_dir}")

    cmd = ["git", "-C", str(repo_dir), "diff"]
    if staged:
        cmd.append("--staged")

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    diff_text = proc.stdout

    # Summarize stats
    stat_cmd = ["git", "-C", str(repo_dir), "diff", "--stat"]
    if staged:
        stat_cmd.append("--staged")
    stat_proc = subprocess.run(stat_cmd, capture_output=True, text=True, timeout=30, check=False)

    return {
        "repo": str(repo_dir.resolve()),
        "staged": staged,
        "diff_bytes": len(diff_text),
        "diff": diff_text[:5000],
        "stat": stat_proc.stdout.strip(),
    }


def list_github_prs(
    repo_name: str,
    state: str = "open",
    limit: int = 20,
) -> dict[str, Any]:
    """Query GitHub pull requests using gh CLI if available."""
    gh_bin = shutil.which("gh") or shutil.which("gh.exe")
    if not gh_bin:
        return {
            "status": "down",
            "available": False,
            "tool": "gh",
            "message": "gh CLI not found in PATH",
            "prs": [],
        }

    cmd = [
        gh_bin,
        "pr",
        "list",
        "--repo",
        repo_name,
        "--state",
        state,
        f"--limit={limit}",
        "--json",
        "number,title,author,state,createdAt,url,headRefName",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        if proc.returncode == 0:
            prs = json.loads(proc.stdout)
            return {
                "status": "ok",
                "available": True,
                "repo": repo_name,
                "count": len(prs),
                "prs": prs,
            }
        return {
            "status": "unauthenticated" if "auth" in proc.stderr.lower() else "error",
            "available": True,
            "error": proc.stderr.strip(),
            "prs": [],
        }
    except Exception as e:
        return {"status": "error", "available": True, "error": str(e), "prs": []}


def view_github_pr(repo_name: str, pr_number: int) -> dict[str, Any]:
    """Inspect specific GitHub pull request."""
    gh_bin = shutil.which("gh") or shutil.which("gh.exe")
    if not gh_bin:
        return {"status": "down", "available": False, "message": "gh CLI not found in PATH"}

    cmd = [
        gh_bin,
        "pr",
        "view",
        str(pr_number),
        "--repo",
        repo_name,
        "--json",
        "number,title,body,author,state,commits,additions,deletions,url",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        if proc.returncode == 0:
            return {"status": "ok", "available": True, "pr": json.loads(proc.stdout)}
        return {"status": "error", "available": True, "error": proc.stderr.strip()}
    except Exception as e:
        return {"status": "error", "available": True, "error": str(e)}


def scan_fleet_dirty(root_dir: Path) -> dict[str, Any]:
    """Scan root directory across fleet repos for dirty or uncommitted state."""
    if not root_dir.is_dir():
        raise NotADirectoryError(f"Root is not a directory: {root_dir}")

    clean_repos: list[str] = []
    dirty_repos: list[dict[str, Any]] = []

    for entry in os.scandir(root_dir):
        if entry.is_dir(follow_symlinks=False):
            p = Path(entry.path)
            if (p / ".git").exists():
                try:
                    proc = subprocess.run(
                        ["git", "-C", str(p), "status", "--porcelain"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False,
                    )
                    changes = [line for line in proc.stdout.splitlines() if line.strip()]
                    if changes:
                        dirty_repos.append({
                            "name": entry.name,
                            "path": str(p.resolve()),
                            "modified_count": len(changes),
                            "changes_sample": changes[:10],
                        })
                    else:
                        clean_repos.append(entry.name)
                except Exception:
                    continue

    return {
        "root": str(root_dir.resolve()),
        "total_scanned": len(clean_repos) + len(dirty_repos),
        "clean_count": len(clean_repos),
        "dirty_count": len(dirty_repos),
        "dirty_repos": dirty_repos,
        "clean_repos": clean_repos,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitcraft",
        description="GitCraft: Git and GitHub fleet repository craft workstation",
    )
    parser.add_argument("--version", action="version", version="gitcraft 0.1.0")

    sub = parser.add_subparsers(dest="verb", required=True)

    # status
    p_st = sub.add_parser("status", help="Get git repository status")
    p_st.add_argument("--repo", required=True, type=Path, help="Target git repository")
    p_st.add_argument("--json", action="store_true", help="Output JSON")

    # log
    p_log = sub.add_parser("log", help="Get commit history")
    p_log.add_argument("--repo", required=True, type=Path, help="Target git repository")
    p_log.add_argument("--count", type=int, default=10, help="Number of commits")
    p_log.add_argument("--json", action="store_true", help="Output JSON")

    # diff
    p_diff = sub.add_parser("diff", help="Inspect git diff")
    p_diff.add_argument("--repo", required=True, type=Path, help="Target git repository")
    p_diff.add_argument("--staged", action="store_true", help="Staged diff")
    p_diff.add_argument("--json", action="store_true", help="Output JSON")

    # pr-list
    p_prl = sub.add_parser("pr-list", help="Query GitHub pull requests")
    p_prl.add_argument("--repo", required=True, help="GitHub repo (owner/name)")
    p_prl.add_argument("--state", default="open", choices=["open", "closed", "all"], help="PR state")
    p_prl.add_argument("--limit", type=int, default=20, help="Max PRs")
    p_prl.add_argument("--json", action="store_true", help="Output JSON")

    # pr-view
    p_prv = sub.add_parser("pr-view", help="View pull request details")
    p_prv.add_argument("--repo", required=True, help="GitHub repo (owner/name)")
    p_prv.add_argument("--pr", required=True, type=int, help="PR number")
    p_prv.add_argument("--json", action="store_true", help="Output JSON")

    # fleet-dirty
    p_fleet = sub.add_parser("fleet-dirty", help="Scan fleet directories for dirty repos")
    p_fleet.add_argument("--root", type=Path, default=Path(r"D:\Dev\repos"), help="Root directory")
    p_fleet.add_argument("--json", action="store_true", help="Output JSON")

    # mcp
    sub.add_parser("mcp", help="Run FastMCP stdio server")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.verb == "status":
            res = get_git_status(args.repo)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                clean_str = "CLEAN" if res["is_clean"] else "DIRTY"
                print(f"Branch: {res['branch']} ({clean_str})")
                print(f"Ahead: {res['ahead']} | Behind: {res['behind']}")
                print(f"Staged: {res['staged_count']} | Unstaged: {res['unstaged_count']} | Untracked: {res['untracked_count']}")
            return 0

        if args.verb == "log":
            res = get_git_log(args.repo, count=args.count)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                for c in res["commits"]:
                    print(f"{c['short_hash']}  {c['date'][:10]}  {c['author']:<20}  {c['subject']}")
            return 0

        if args.verb == "diff":
            res = get_git_diff(args.repo, staged=args.staged)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(res["stat"] or "No diff.")
            return 0

        if args.verb == "pr-list":
            res = list_github_prs(args.repo, state=args.state, limit=args.limit)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                if res["status"] != "ok":
                    print(f"GitHub PR list ({res['status']}): {res.get('message') or res.get('error')}")
                else:
                    for pr in res.get("prs", []):
                        print(f"#{pr['number']}  {pr['title']} ({pr.get('headRefName')})")
            return 0

        if args.verb == "pr-view":
            res = view_github_pr(args.repo, args.pr)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                if res["status"] != "ok":
                    print(f"GitHub PR view ({res['status']}): {res.get('message') or res.get('error')}")
                else:
                    pr = res["pr"]
                    print(f"#{pr['number']}  {pr['title']}")
                    print(f"URL: {pr.get('url')}")
            return 0

        if args.verb == "fleet-dirty":
            res = scan_fleet_dirty(args.root)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"Fleet Scan: {res['total_scanned']} repos ({res['clean_count']} clean, {res['dirty_count']} dirty)")
                for d in res["dirty_repos"]:
                    print(f"  [DIRTY] {d['name']} ({d['modified_count']} files)")
            return 0

        if args.verb == "mcp":
            from .mcp_server import mcp

            mcp.run()
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
