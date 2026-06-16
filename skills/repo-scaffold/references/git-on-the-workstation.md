# Git on the workstation — cross-OS cheat-sheet (+ the Cowork wrinkle)

## Why git runs on the machine, not in the Cowork sandbox

The Cowork sandbox sees your folder through a mount that **cannot delete files**. Git constantly
creates and removes small lock/temp files (`.git/index.lock`, `HEAD.lock`, packing temporaries).
Run git *inside the sandbox* and those locks can't be cleaned up — the commit's objects are written
but the leftover `index.lock` makes the **next** git command fail with "Unable to create
'.../index.lock': File exists."

So the rule: **the skills write files; git runs on the workstation** — through Desktop Commander
(which executes on the real machine) or a terminal. The file edits a skill makes are visible to git
either way, because the sandbox mount and the workstation folder are the same physical files.

## The everyday cycle (identical on both OSes)

```bash
# macOS / Linux
git switch -c feat/<short-topic>
# ... skill writes its files ...
git add -A
git commit -m "<area>: <imperative summary>"
git push -u origin feat/<short-topic>     # open a PR for review
```
```powershell
# Windows (PowerShell)
git switch -c feat/<short-topic>
git add -A
git commit -m "<area>: <imperative summary>"
git push -u origin feat/<short-topic>
```

`git switch -c` needs Git 2.23+. On older Git use `git checkout -b`.

## Commit message convention (pack-wide)

`<area>: <imperative summary>` — area is the repo zone touched:

- `chore: scaffold platform repo`
- `dbt: add int_taxpayer__master with join contract`
- `catalogue: add BOP semantic enrichment (DRAFT)`
- `quality: add completeness gate to mart_debt__aged_balances`
- `ingestion: onboard ARS accounting source (Hot tier)`

## First-time identity (once per machine)

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.org"
```

## If an in-sandbox git ever stranded lock files

Symptoms: `fatal: Unable to create '.../index.lock': File exists`, or warnings like
`unable to unlink '.git/objects/.../tmp_obj_*': Operation not permitted`. Fix it **on the
workstation** (Desktop Commander / terminal), then carry on:

```bash
# macOS / Linux
cd "/path/to/repo"
rm -f .git/index.lock .git/HEAD.lock .git/objects/maintenance.lock
find .git/objects -name 'tmp_obj_*' -delete
git status        # should be clean; the commit itself was fine
```
```powershell
# Windows (PowerShell)
cd "C:\path\to\repo"
Remove-Item .git\index.lock,.git\HEAD.lock,.git\objects\maintenance.lock -ErrorAction SilentlyContinue
Get-ChildItem .git\objects -Recurse -Filter 'tmp_obj_*' | Remove-Item
git status
```

The stranded locks are harmless leftovers — the committed objects are intact (`git log` / `git
fsck` confirm it). Removing them just unblocks the next commit.
