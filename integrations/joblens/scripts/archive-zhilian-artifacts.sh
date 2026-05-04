#!/usr/bin/env bash
set -euo pipefail

downloads_dir="/mnt/d/Downloads"
artifacts_dir="/home/xstars/zhilian_intelligence_sandbox/artifacts"
since_minutes=""
keyword_filter=""
dry_run=0

usage() {
  cat <<'USAGE'
Usage:
  scripts/archive-zhilian-artifacts.sh --keyword KEYWORD [--since-minutes N] [--dry-run]

Purpose:
  Move formal Zhilian collection outputs from D:\Downloads into artifacts.

Rules:
  - Move only files whose names start with ZHILIAN_.
  - Skip any file whose name contains TEST.
  - .html -> artifacts/raw/html
  - .json -> artifacts/preprocessed/json
  - .md   -> artifacts/presentation/md

Examples:
  scripts/archive-zhilian-artifacts.sh --keyword "C++培训讲师" --dry-run --since-minutes 30
  scripts/archive-zhilian-artifacts.sh --keyword "C++培训讲师" --since-minutes 30
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since-minutes)
      since_minutes="${2:-}"
      if [[ -z "$since_minutes" || ! "$since_minutes" =~ ^[0-9]+$ ]]; then
        echo "ERROR: --since-minutes requires a non-negative integer" >&2
        exit 2
      fi
      shift 2
      ;;
    --keyword)
      keyword_filter="${2:-}"
      if [[ -z "$keyword_filter" ]]; then
        echo "ERROR: --keyword requires a non-empty value" >&2
        exit 2
      fi
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$keyword_filter" ]]; then
  echo "ERROR: --keyword is required to avoid archiving unrelated formal files" >&2
  usage >&2
  exit 2
fi

if [[ ! -d "$downloads_dir" ]]; then
  echo "ERROR: downloads directory not found: $downloads_dir" >&2
  exit 1
fi

mkdir -p \
  "$artifacts_dir/raw/html" \
  "$artifacts_dir/preprocessed/json" \
  "$artifacts_dir/presentation/md"

find_args=("$downloads_dir" -maxdepth 1 -type f -name 'ZHILIAN_*' ! -name '*TEST*')
if [[ -n "$since_minutes" ]]; then
  find_args+=(-mmin "-$since_minutes")
fi

moved_count=0
skipped_count=0

while IFS= read -r -d '' file_path; do
  file_name="$(basename "$file_path")"
  target_dir=""

  if [[ "$file_name" != *"$keyword_filter"* ]]; then
    skipped_count=$((skipped_count + 1))
    continue
  fi

  case "$file_name" in
    *.html|*.htm)
      target_dir="$artifacts_dir/raw/html"
      ;;
    *.json)
      target_dir="$artifacts_dir/preprocessed/json"
      ;;
    *.md)
      target_dir="$artifacts_dir/presentation/md"
      ;;
    *)
      echo "SKIP unsupported extension: $file_name"
      skipped_count=$((skipped_count + 1))
      continue
      ;;
  esac

  target_path="$target_dir/$file_name"
  if [[ -e "$target_path" ]]; then
    echo "SKIP already exists: $target_path"
    skipped_count=$((skipped_count + 1))
    continue
  fi

  if [[ "$dry_run" -eq 1 ]]; then
    echo "MOVE $file_path -> $target_path"
  else
    mv "$file_path" "$target_path"
    echo "MOVED $file_name -> $target_dir"
  fi
  moved_count=$((moved_count + 1))
done < <(find "${find_args[@]}" -print0 | sort -z)

if [[ "$dry_run" -eq 1 ]]; then
  echo "Dry run complete. Planned moves: $moved_count, skipped: $skipped_count"
else
  echo "Archive complete. Moved: $moved_count, skipped: $skipped_count"
fi
