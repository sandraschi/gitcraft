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
