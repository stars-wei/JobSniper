#!/usr/bin/env python3
"""Parse Jobsniper queue tasks/results JSONL and print shell assignments.

Usage:
  python3 scraping_layer/scripts/parse_queue_results.py <results.jsonl> <tasks.jsonl>

Output (one per line):
  total=<int>
  done=<int>
  failed=<int>
  keyword='<shell-escaped string>'
"""

from __future__ import annotations

import json
import re
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def _sh_single_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def _normalize_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        scheme = "https"
        netloc = (parsed.netloc or "").lower()
        path = parsed.path or ""
        query = parsed.query or ""

        # Detail URLs: query is volatile, strip it.
        if re.search(r"/jobdetail/[^/?#]+\.htm$", path, re.I):
            query = ""
        else:
            # Non-detail URLs: keep query, but sort for stability.
            params = parse_qsl(query, keep_blank_values=True)
            query = urlencode(sorted(params))

        return urlunsplit((scheme, netloc, path, query, ""))
    except Exception:
        return str(value or "").split("#")[0].replace("http://", "https://")


def _identity(row: dict) -> str:
    task_id = row.get("task_id") or row.get("taskId")
    if task_id:
        return f"task:{task_id}"

    job_id = row.get("job_id")
    url = row.get("normalized_url") or row.get("url")
    if not job_id and url:
        match = re.search(r"/jobdetail/([^/?#]+)\.htm", _normalize_url(url), re.I)
        if match:
            job_id = match.group(1)
    if job_id:
        return f"job:{job_id}"
    if url:
        return f"url:{_normalize_url(url)}"
    return ""


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: parse_queue_results.py <results.jsonl> <tasks.jsonl>", file=sys.stderr)
        return 2

    results_file = sys.argv[1]
    tasks_file = sys.argv[2]

    keyword = ""
    task_identities: list[str] = []
    task_identity_set: set[str] = set()

    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                ident = _identity(row)
                if ident and ident not in task_identity_set:
                    task_identity_set.add(ident)
                    task_identities.append(ident)
                if not keyword:
                    keyword = str(row.get("keyword") or "")
    except Exception:
        pass

    task_status: dict[str, str] = {}
    try:
        with open(results_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                ident = _identity(row)
                if ident:
                    task_status[ident] = str(row.get("status") or "")
    except Exception:
        pass

    total = len(task_identities)
    done = sum(1 for ident in task_identities if task_status.get(ident) == "done")
    failed = sum(1 for ident in task_identities if task_status.get(ident) == "failed")

    print(f"total={total}")
    print(f"done={done}")
    print(f"failed={failed}")
    print(f"keyword={_sh_single_quote(keyword)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
