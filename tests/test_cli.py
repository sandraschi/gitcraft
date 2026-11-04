"""Unit and integration tests for GitCraft CLI verbs."""

import json
import subprocess
from pathlib import Path

import pytest
from gitcraft import cli


@pytest.fixture
def test_repo(tmp_path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@storytold.dev"], cwd=repo, check=True)

    f = repo / "README.md"
    f.write_text("# Test Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)
    return repo


def test_git_status(test_repo):
    st = cli.get_git_status(test_repo)
    assert st["branch"] == "main"
    assert st["is_clean"] is True
    assert st["staged_count"] == 0

    # Add untracked file
    (test_repo / "new.txt").write_text("untracked", encoding="utf-8")
    st2 = cli.get_git_status(test_repo)
    assert st2["is_clean"] is False
    assert st2["untracked_count"] == 1


def test_git_log(test_repo):
    log = cli.get_git_log(test_repo, count=5)
    assert log["commit_count"] >= 1
    assert log["commits"][0]["subject"] == "Initial commit"
    assert log["commits"][0]["author"] == "Test User"


def test_git_diff(test_repo):
    # Modify existing file
    f = test_repo / "README.md"
    f.write_text("# Modified Repo Content\n", encoding="utf-8")

    diff = cli.get_git_diff(test_repo)
    assert diff["diff_bytes"] > 0
    assert "Modified Repo Content" in diff["diff"]


def test_pr_list_smoke():
    # Calling gh pr list should safely return a status dict, never raise
    res = cli.list_github_prs("sandraschi/democraft-mcp", limit=1)
    assert isinstance(res, dict)
    assert "status" in res


def test_fleet_dirty_scan(tmp_path, test_repo):
    res = cli.scan_fleet_dirty(tmp_path)
    assert res["total_scanned"] >= 1
    assert "repo" in res["clean_repos"] or any(d["name"] == "repo" for d in res["dirty_repos"])


def test_cli_runner(test_repo, capsys):
    rc = cli.main(["status", "--repo", str(test_repo), "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    st = json.loads(captured.out)
    assert st["branch"] == "main"

    rc = cli.main(["log", "--repo", str(test_repo), "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    log = json.loads(captured.out)
    assert len(log["commits"]) >= 1
