# GitCraft

Git and GitHub fleet repository craft workstation.

## Verbs
- `gitcraft status --repo <dir>`: Non-mutating repository status, branch, and tracking telemetry
- `gitcraft log --repo <dir>`: Structured commit history and author metadata
- `gitcraft diff --repo <dir>`: Patch diff inspection across working tree and index
- `gitcraft pr-list --repo <owner/name>`: GitHub pull request querying via gh CLI
- `gitcraft pr-view --repo <owner/name> --pr <number>`: Pull request inspection and details
- `gitcraft fleet-dirty --root <dir>`: Fleet-wide scan for dirty or uncommitted repositories
- `gitcraft mcp`: FastMCP stdio server

## Lineage — the Storytold craft-app pattern

Storytold ArtCraft ([storytold/artcraft](https://github.com/storytold/artcraft) — "the IDE for artists") was the starting point. The 16 craft apps in the Storytold stable each ship one binary that is both the human CLI and the agent MCP server (stdio), headless-first, with `run.json` + report artifacts. That modus operandi and harness is what this repo implements; the code here is independent, the pattern is shared.
