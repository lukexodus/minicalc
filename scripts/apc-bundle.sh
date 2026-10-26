#!/usr/bin/env bash
# apc-bundle.sh — Package repository files into a self-describing, verifiable APC archive.
# Run from the minicalc repo root.

set -euo pipefail

# --- Profiles ---
# Customize or comment out lines inside these arrays to tune your upload set.

PROFILE_CORE=(
  AGENTS.md
  docs/context/complete-context.md
  docs/context/language-spec.md
  docs/context/interface-contract.md
  docs/context/apc-handoff-template.md
  docs/context/apc-bundle-quickref.md
  docs/context/repo-tree.txt
  docs/decisions/decision-log.md
  docs/tasks/status.md
  docs/tasks/high-level-tasks.md
  docs/prompts/*.md
  docs/guide/COLLABORATOR-GUIDE.md
)

PROFILE_DEV=(
  "${PROFILE_CORE[@]}"
  # Source, tests, and patches so the auditor can rebuild and run the suite.
  minicalc/*.py
  main.py
  pytest.ini
  tests/*.py
  tests/golden/*
  patch/*.patch
  scripts/*.sh
  scripts/*.py
)

# full: union of all profiles, de-duplicated during resolution
PROFILE_FULL=(
  "${PROFILE_CORE[@]}"
  "${PROFILE_DEV[@]}"
)

# Optional reports: included only with --with-reports flag
OPTIONAL_REPORTS=(
  # docs/reports/CORE-001-report.md
)

show_help() {
  cat <<'EOF'
Usage: ./scripts/apc-bundle.sh [PROFILE] [OPTIONS]

Profiles:
  core          Governance, tracking, and architectural context (default)
  dev           Core implementation modules, interfaces, and test fixtures
  full          Complete project snapshot (union of all profiles)

Options:
  --exclude GLOB    Drop any resolved path matching the glob (repeatable)
  --add PATH        Add an ad hoc file (repeatable)
  --with-reports    Include active entries from OPTIONAL_REPORTS
  --list            Print resolved file list with byte sizes and exit 0
  --tokens          Estimate token count (~4 chars/token heuristic) and exit 0
  --discover        Search minicalc for core classes/functions and exit 0
  -h, --help        Show this help message and exit
EOF
}

# --- Secret Guard & Forbidden Directory Filter ---
is_secret_or_forbidden() {
  local p="${1#./}"
  local base
  base="$(basename "$p")"
  local lower_p
  lower_p="$(echo "$p" | tr '[:upper:]' '[:lower:]')"

  # Forbidden build, dependency, and storage directories
  case "$p" in
  results | results/* | */results/* | \
    data/raw | data/raw/* | */data/raw/* | \
    .git | .git/* | */.git/* | \
    .venv | .venv/* | */.venv/* | \
    venv | venv/* | */venv/* | \
    __pycache__ | __pycache__/* | */__pycache__/* | \
    node_modules | node_modules/* | */node_modules/* | \
    dist | dist/* | */dist/* | \
    build | build/* | */build/*)
    return 0
    ;;
  esac

  # Forbidden filename prefixes or credential extensions
  case "$base" in
  .env* | *.key | *.pem | *.p12 | *.pfx)
    return 0
    ;;
  esac

  # Forbidden sensitive keywords anywhere in the path
  case "$lower_p" in
  *secret* | *token* | *credential* | *id_rsa* | *password*)
    # Project source whose name merely contains "token": the lexer's token
    # type definitions, not a credential.
    case "$p" in
    minicalc/tokens.py | tests/test_tokens.py | tests/test_vocabulary.py)
      return 1
      ;;
    esac
    return 0
    ;;
  esac

  return 1
}

# --- CLI Parsing ---
PROFILE=""
WITH_REPORTS=0
LIST_ONLY=0
TOKENS_ONLY=0
DISCOVER_ONLY=0
EXCLUDES=()
ADDS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
  -h | --help)
    show_help
    exit 0
    ;;
  --list)
    LIST_ONLY=1
    shift
    ;;
  --tokens)
    TOKENS_ONLY=1
    shift
    ;;
  --discover)
    DISCOVER_ONLY=1
    shift
    ;;
  --with-reports)
    WITH_REPORTS=1
    shift
    ;;
  --exclude)
    if [[ $# -lt 2 ]]; then
      echo "ERROR: --exclude requires a glob argument" >&2
      exit 2
    fi
    EXCLUDES+=("$2")
    shift 2
    ;;
  --add)
    if [[ $# -lt 2 ]]; then
      echo "ERROR: --add requires a path argument" >&2
      exit 2
    fi
    ADDS+=("$2")
    shift 2
    ;;
  -*)
    echo "ERROR: Unknown option: $1" >&2
    exit 2
    ;;
  *)
    if [[ -z "$PROFILE" ]]; then
      PROFILE="$1"
      shift
    else
      echo "ERROR: Unexpected argument: $1" >&2
      exit 2
    fi
    ;;
  esac
done

if [[ $DISCOVER_ONLY -eq 1 ]]; then
  echo "Discovered core source files in minicalc:"
  find "minicalc" -type f \( -name "*.py" -o -name "*.ts" -o -name "*.go" -o -name "*.rs" \) 2>/dev/null | sort -u
  exit 0
fi

PROFILE="${PROFILE:-core}"

# Auto-update docs/context/repo-tree.txt if tree is available
if command -v tree >/dev/null 2>&1; then
  mkdir -p docs/context
  tree -I ".git|.venv|venv|__pycache__|*.egg-info|node_modules|dist|build|*.tar.gz|*.log" --dirsfirst --noreport > docs/context/repo-tree.txt
fi

# Select profile array
RAW_PROFILE_ITEMS=()
case "$PROFILE" in
core)
  RAW_PROFILE_ITEMS=("${PROFILE_CORE[@]}")
  ;;
dev)
  RAW_PROFILE_ITEMS=("${PROFILE_DEV[@]}")
  ;;
full)
  RAW_PROFILE_ITEMS=("${PROFILE_FULL[@]}")
  ;;
*)
  echo "ERROR: Unknown profile '$PROFILE'. Valid options: core, dev, full." >&2
  exit 2
  ;;
esac

# Resolve globs in profile items
RESOLVED_RAW=()
for item in "${RAW_PROFILE_ITEMS[@]}"; do
  if [[ "$item" == *"*"* || "$item" == *"?"* || "$item" == *"["* ]]; then
    shopt -s nullglob
    # shellcheck disable=SC2206
    matches=($item)
    shopt -u nullglob
    if [[ ${#matches[@]} -lt 1 ]]; then
      echo "ERROR: Glob '$item' matched no files." >&2
      exit 1
    fi
    RESOLVED_RAW+=("${matches[@]}")
  else
    RESOLVED_RAW+=("$item")
  fi
done

# Add optional reports if requested
if [[ $WITH_REPORTS -eq 1 ]]; then
  for rep in "${OPTIONAL_REPORTS[@]}"; do
    RESOLVED_RAW+=("$rep")
  done
fi

# Add ad hoc files from --add
for ad in "${ADDS[@]}"; do
  RESOLVED_RAW+=("$ad")
done

# De-duplicate while preserving order
DEDUPED=()
declare -A SEEN=()
for path in "${RESOLVED_RAW[@]}"; do
  norm_path="${path#./}"
  if [[ -z "${SEEN[$norm_path]:-}" ]]; then
    SEEN["$norm_path"]=1
    DEDUPED+=("$norm_path")
  fi
done

# Apply --exclude
FILTERED=()
for path in "${DEDUPED[@]}"; do
  base="$(basename "$path")"
  excluded=0
  for ex in "${EXCLUDES[@]}"; do
    # shellcheck disable=SC2053
    if [[ "$path" == $ex || "$base" == $ex ]]; then
      excluded=1
      break
    fi
  done
  if [[ $excluded -eq 0 ]]; then
    FILTERED+=("$path")
  fi
done

RESOLVED_FILES=("${FILTERED[@]}")

# Validate paths and secrets
validation_failed=0
for f in "${RESOLVED_FILES[@]}"; do
  if is_secret_or_forbidden "$f"; then
    echo "ERROR: Security guard triggered! Path '$f' matches secret or forbidden pattern." >&2
    validation_failed=1
    continue
  fi

  if [[ ! -e "$f" ]]; then
    echo "MISSING FILE: $f" >&2
    validation_failed=1
  elif [[ ! -f "$f" ]]; then
    echo "NOT A REGULAR FILE: $f" >&2
    validation_failed=1
  fi
done

if [[ $validation_failed -ne 0 ]]; then
  exit 1
fi

# --list mode
if [[ $LIST_ONLY -eq 1 ]]; then
  echo "Files in profile '$PROFILE' (${#RESOLVED_FILES[@]} total):"
  total_bytes=0
  for f in "${RESOLVED_FILES[@]}"; do
    sz=$(wc -c <"$f" | tr -d ' ')
    total_bytes=$((total_bytes + sz))
    printf "%10d  %s\n" "$sz" "$f"
  done
  echo "---"
  printf "Total: %d bytes (approx %d KB)\n" "$total_bytes" "$((total_bytes / 1024))"
  exit 0
fi

# --tokens mode (Rough heuristic ~4 chars per token for code/markdown)
if [[ $TOKENS_ONLY -eq 1 ]]; then
  total_chars=0
  for f in "${RESOLVED_FILES[@]}"; do
    chars=$(wc -m <"$f" | tr -d ' ')
    total_chars=$((total_chars + chars))
  done
  est_tokens=$((total_chars / 4))
  echo "Estimated token count for profile '$PROFILE': ~${est_tokens} tokens (${total_chars} characters across ${#RESOLVED_FILES[@]} files)."
  exit 0
fi

# Create archive
OUT="apc-bundle-${PROFILE}-$(date +%Y%m%d-%H%M).tar.gz"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM

# Stage into temp directory preserving repo-relative paths
cp --parents "${RESOLVED_FILES[@]}" "$TMP_DIR/"

# Generate MANIFEST.txt
MANIFEST="$TMP_DIR/MANIFEST.txt"
{
  echo "Profile: $PROFILE"
  echo "Timestamp (UTC): $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo "Git commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'uncommitted')"
  echo "Git status:"
  git status --porcelain -- "${RESOLVED_FILES[@]}" 2>/dev/null || true
  echo ""
  echo "Paths are repo-relative. Extract with: tar -xzf <archive>."
  echo ""
  echo "Files (SHA256, Size in bytes, Path):"
  for f in "${RESOLVED_FILES[@]}"; do
    sha=$(sha256sum "$f" | awk '{print $1}')
    sz=$(wc -c <"$f" | tr -d ' ')
    echo "$sha  $sz  $f"
  done
} >"$MANIFEST"

tar -czf "$OUT" -C "$TMP_DIR" MANIFEST.txt "${RESOLVED_FILES[@]}"

archive_sz=$(wc -c <"$OUT" | tr -d ' ')
file_cnt=$((${#RESOLVED_FILES[@]} + 1))

echo "=================================================="
echo "APC Bundle Created Successfully!"
echo "Archive:    $OUT"
echo "Size:       $archive_sz bytes"
echo "Files:      $file_cnt (including MANIFEST.txt)"
echo "Verify with: tar -xzf $OUT && awk '/^[0-9a-f]{64}/ {print \$1 \"  \" \$3}' MANIFEST.txt | sha256sum -c -"
echo "=================================================="
