"""FastMCP server for GitCraft."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from .cli import (
    get_git_diff,
    get_git_log,
    get_git_status,
    list_github_prs,
    scan_fleet_dirty,
    view_github_pr,
)

mcp = FastMCP("GitCraft", version="0.1.0")


@mcp.tool()
def git_status(repo_path: str) -> dict[str, Any]:
    """Inspect git repository status, branch, ahead/behind counts, and modified files."""
    return get_git_status(Path(repo_path))


@mcp.tool()
def git_log(repo_path: str, count: int = 10) -> dict[str, Any]:
    """Inspect structured git commit history."""
    return get_git_log(Path(repo_path), count=count)


@mcp.tool()
def git_diff(repo_path: str, staged: bool = False) -> dict[str, Any]:
    """Inspect working tree or staged diff."""
    return get_git_diff(Path(repo_path), staged=staged)


@mcp.tool()
def github_pr_list(repo: str, state: str = "open", limit: int = 20) -> dict[str, Any]:
    """Query GitHub pull requests for a repository."""
    return list_github_prs(repo, state=state, limit=limit)


@mcp.tool()
def github_pr_view(repo: str, pr_number: int) -> dict[str, Any]:
    """View details of a specific GitHub pull request."""
    return view_github_pr(repo, pr_number)


@mcp.tool()
def fleet_dirty_check(root_dir: str = r"D:\Dev\repos") -> dict[str, Any]:
    """Perform fleet-wide audit of dirty or uncommitted repositories."""
    return scan_fleet_dirty(Path(root_dir))


def main():
    mcp.run()


if __name__ == "__main__":
    main()
