# APC Bundle Quick Reference

For the APC AI: `./scripts/apc-bundle.sh` packages repository files into one self-describing `.tar.gz` archive for upload. Because the APC AI has no direct filesystem access, when a task requires inspecting live file contents across multiple modules, request lukexodus to run the appropriate profile command below and upload the resulting archive.

## Basic Usage

Run from the repository root:

```bash
./scripts/apc-bundle.sh [PROFILE] [OPTIONS]
```

Default profile is `core`.

## Standard Profiles

| Profile | Purpose | Included Files |
| :--- | :--- | :--- |
| `core` | Governance & operational tracking | `AGENTS.md`, `docs/context/*`, `docs/decisions/decision-log.md`, `docs/tasks/status.md`, project config files |
| `dev` | Core development context | All of `core`, plus key source code modules and interface tests |
| `full` | Complete project snapshot | Union of all profiles, excluding build artifacts and secrets |

Profiles can be customized by editing the bash arrays directly inside `./scripts/apc-bundle.sh`.

## Options

- `--list` — Preview resolved file list and sizes in bytes without creating an archive.
- `--add PATH` — Include an ad hoc file (repeatable).
- `--exclude GLOB` — Exclude files matching a glob or filename (repeatable).
- `--with-reports` — Include recent completed reports from `docs/reports/`.
- `-h, --help` — Show help.

### Examples

```bash
# Preview what is in the core profile
./scripts/apc-bundle.sh --list

# Bundle core context plus a specific implementation file
./scripts/apc-bundle.sh core --add minicalc/app.py

# Bundle everything except large binaries
./scripts/apc-bundle.sh full --exclude '*.bin'
```

## Archive Contents & Audit Manifest

The tool creates `apc-bundle-<profile>-<YYYYmmdd-HHMM>.tar.gz` in the repo root.
All paths are stored repo-relative. A root `MANIFEST.txt` records:
- Bundle profile name
- UTC timestamp
- Short git commit hash
- Git status of bundled files
- SHA256 checksum, byte size, and path for every file

## Safety Guards

The script aborts immediately (exit 1) if:
- Any file is missing or not a regular file.
- Any file matches secret patterns (`.env*`, `*.key`, `*.pem`, `*secret*`, `*token*`, `*credential*`).
- Any path lives in forbidden build/data directories (`.git/`, `.venv/`, `node_modules/`, `dist/`, `build/`).

## How to Extract & Verify

```bash
tar -xzf <archive-name>.tar.gz
awk '/^[0-9a-f]{64}/ {print $1 "  " $3}' MANIFEST.txt | sha256sum -c -
```
