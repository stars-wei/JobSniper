#!/usr/bin/env python3
"""
Parse JobSniper Zhilian detail queue status from:
- D:\\Downloads\\zhilian_detail_tasks.jsonl
- D:\\Downloads\\zhilian_detail_results.jsonl

Outputs shell-friendly `key=value` lines for `eval $(parse_results)`.
"""

import json
import re
import sys
from urllib.parse import urlsplit, urlunsplit

results_file = sys.argv[1]
tasks_file = sys.argv[2]


def normalize_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        return urlunsplit(("https", (parsed.netloc or "").lower(), parsed.path, "", ""))
    except Exception:
        return str(value or "").split("?")[0].replace("http://", "https://")


def identity(row: dict) -> str:
    job_id = row.get("job_id")
    url = row.get("normalized_url") or row.get("url")
    if not job_id and url:
        m = re.search(r"/jobdetail/([^/?#]+)\.htm", normalize_url(url), re.I)
        if m:
            job_id = m.group(1)
    if job_id:
        return f"job:{job_id}"
    if url:
        return f"url:{normalize_url(url)}"
    return ""


def sh_quote(value: str) -> str:
    # Single-quote for safe `eval`, with standard bash escaping for embedded quotes.
    return "'" + (value or "").replace("'", "'\\''") + "'"


keyword = ""
task_identities: list[str] = []
task_identity_set: set[str] = set()
try:
    with open(tasks_file, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            ident = identity(d)
            if ident and ident not in task_identity_set:
                task_identity_set.add(ident)
                task_identities.append(ident)
            if not keyword:
                keyword = d.get("keyword", "") or ""
except Exception:
    pass

task_status: dict[str, str] = {}
task_error: dict[str, str] = {}
try:
    with open(results_file, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            ident = identity(r)
            if not ident:
                continue
            # Latest record wins (results is append-only).
            task_status[ident] = (r.get("status") or "") if isinstance(r.get("status"), str) else ""
            task_error[ident] = (r.get("error") or "") if isinstance(r.get("error"), str) else ""
except Exception:
    pass

total = len(task_identities)
done = sum(1 for ident in task_identities if task_status.get(ident) == "done")
failed = sum(1 for ident in task_identities if task_status.get(ident) == "failed")

captcha_re = re.compile(r"(captcha|验证码|人机验证|安全验证|verification|challenge|edgeone)", re.I)
captcha_failed = sum(
    1
    for ident in task_identities
    if task_status.get(ident) == "failed"
    and captcha_re.search(task_error.get(ident, "") or "")
)

print(f"total={total}")
print(f"done={done}")
print(f"failed={failed}")
print(f"captcha_failed={captcha_failed}")
print(f"has_captcha={1 if captcha_failed > 0 else 0}")
print(f"keyword={sh_quote(keyword)}")

