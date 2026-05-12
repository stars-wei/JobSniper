# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

JobSniper is a FastMCP stdio server that turns a local job-hunting workspace into MCP-accessible tools and resources. It bridges Chrome-based web scraping (via the Joblens extension), a local filesystem vault of job postings, and a user persona for skill tracking — all exposed through the MCP protocol so AI coding assistants can search, collect, and archive recruitment data.

Current focus: **智联招聘 (Zhilian)**. BOSS直聘 scaffolding exists but is not yet wired.

## Common commands

```bash
# Install Python deps (Python 3.12+)
python3 -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/pip install -r requirements-dev.txt  # for pytest

# Import-level smoke test (no MCP protocol)
venv/bin/python scraping_layer/scripts/smoke_mcp_server.py

# Full protocol-level smoke test (launches stdio MCP client against the server)
venv/bin/python scraping_layer/scripts/smoke_mcp_server.py --stdio

# Run Python tests (tests/ directory)
venv/bin/python -m pytest tests/ -v

# Build Chrome extension (after changing scraping_layer/joblens/src/)
cd scraping_layer/joblens && npm install && npm run build:chrome

# Run Chrome extension tests
cd scraping_layer/joblens && npm test
```

## Architecture

Three layers, all local filesystem-based:

**`mcp_server.py`** — Single-file FastMCP server (~750 lines). Exposes 2 resources and 6 tools. Uses `anyio` for manual stdio transport (not the FastMCP built-in). Paths are hardcoded for this machine (`/home/xstars/programs/JobSniper`, `/mnt/d/Downloads`, Windows Chrome at `/mnt/c/Program Files/Google/Chrome/Application/chrome.exe`).

**`storage_layer/`** — The knowledge base:
- `personas/current_user.json` — User profile with skill confidence scores (0-100) and audit log. Read via `jobsniper://persona` resource, mutated by `update_persona` tool.
- `positions/zhilian_intelligence_vault/` — Natural nesting tree: Industry → Domain → Keyword → job detail `.md` files. Index files are `_`-prefixed (e.g. `_行业索引表_智联招聘.md`). Job detail files are `{公司}_{岗位}.md`.
- `positions/zhilian_master_tasks.json` — Keyword→industry/domain mapping array used to route archived files to the correct vault subdirectory.

**`session_layer/`** — User-generated artifacts (resumes, meeting notes, reports). Not accessed by the MCP server directly; downstream consumers read from here.

**`scraping_layer/`** — Browser-based scraping and collection tooling:
- `joblens/` — Chrome extension (TypeScript, Webpack). Forked from Obsidian Web Clipper. The extension reads queue files written by the MCP server, scrapes Zhilian pages in the background via alarm polling, and writes results back to `D:\Downloads\`.
- `scripts/` — Collection support scripts: archive helper, queue parser, and MCP smoke tests.

## Collection flow (queue-based)

The MCP server does **not** scrape directly. Instead:

1. MCP tool writes a task line to a JSONL file in `D:\Downloads\` (`zhilian_list_tasks.jsonl` or `zhilian_detail_tasks.jsonl`)
2. Optionally launches Chrome with a wake URL parameter (debounced per queue type via `/tmp/` lock files) that alerts the extension's alarm polling
3. Joblens extension picks up the task, navigates, scrapes, writes results to the corresponding `*_results.jsonl`
4. A bash monitor script (`watch_downloads.sh` / `watch_job_list.sh`) watches results files and invokes `scraping_layer/scripts/archive_outputs.py` to move files into the vault

Key implication: the MCP server and the browser run in **different OS environments** (WSL vs Windows). Files pass through `/mnt/d/Downloads` which is the Windows `D:\Downloads` mounted into WSL. This mount may be read-only from the WSL side, so the archive tool falls back to copy when move fails.

## MCP resources and tools

**Resources:**
- `jobsniper://persona` — raw JSON of `current_user.json`
- `jobsniper://vault/positions/{platform}/{path_to_job}` — read a job detail markdown by relative path within the vault

**Tools:**
- `find_job_detail` — filename substring search across the vault (excludes `_`-prefixed index files)
- `launch_zhilian_job_menu_collection` — discover industry/domain/keyword taxonomy
- `launch_zhilian_job_list_collection` — enqueue a job list scrape for a keyword
- `launch_zhilian_job_detail_collection` — enqueue a single job detail scrape
- `archive_joblens_outputs` — move/copy files from `D:\Downloads` into the vault tree
- `update_persona` — adjust skill confidence scores

## File naming conventions

- Index files: `_{type}索引表_{name}.md` (e.g. `_岗位索引表_AI产品经理.md`)
- Job details: `{公司名称}_{岗位名称}.md`
- Keyword discovery: `zhilian_keyword_discovery_{timestamp}.md` (archived to `storage_layer/positions/` root)
- Joblens transport files: `ZHILIAN_DETAIL_{公司}_{岗位}_{YYYYMMDD}_{HHMMSS}.md`

Full naming rules in `docs/CODING_GUIDELINES.md`.

## Key constraints

- The `D:\Downloads` ↔ `/mnt/d/Downloads` bridge is fragile. WSL may mount it read-only, in which case `shutil.move` fails and the archiver falls back to `shutil.copy2`. The standalone `scraping_layer/scripts/archive_outputs.py` has more robust fallback logic than the in-server version.
- Captcha detection: the Joblens extension detects security verification pages and pauses the detail queue, writing `failed` with reason `captcha detected`. Manual intervention is required before resuming.
- This codebase assumes a specific machine setup (WSL with Windows Chrome at a fixed path, Downloads at `D:\`). Paths are hardcoded in `mcp_server.py` constants.

## /job-recommend skill

A Claude Code custom skill (`.claude/skills/job-recommend.md`) that traverses the vault to match jobs against the user persona. It explicitly must NOT use `find_job_detail` (which only does filename substring matching) — instead it walks the vault directory tree and reads full file contents for scoring.
