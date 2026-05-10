# JobSniper

JobSniper is a local MCP service prototype for job-search intelligence and candidate profiling.

It sits beside the Zhilian intelligence sandbox and is intended to expose collected recruitment data, user persona data, and later collection commands to an Agent through MCP resources and tools.

## Current Status

This project is currently a lightweight skeleton, not a complete product.

Implemented:

- MCP server entrypoint: `mcp_server.py`
- Current user persona storage: `storage_layer/personas/current_user.json`
- Knowledge vault directory layout for layered recruitment intelligence
- Embedded Joblens integration copy: `integrations/joblens`
- MCP resource for reading the current persona
- MCP resource for reading job detail Markdown files by nested path
- MCP tool for searching job detail files
- MCP tool for launching Zhilian collection through the embedded Joblens Chrome extension
- MCP tool for archiving Joblens outputs from `D:\Downloads` into the knowledge vault
- MCP tool for updating persona skill confidence scores

Not implemented yet:

- Real collection scripts under `collection_layer`
- Session orchestration under `session_layer`
- Full recommendation or consulting workflow
- Stable protocol-level stdio MCP smoke test; the default smoke test currently covers function-level behavior

## Directory Layout

```text
JobSniper/
  mcp_server.py
  collection_layer/
    scripts/
  integrations/
    joblens/
      dist/
        manifest.json
  session_layer/
  storage_layer/
    personas/
      current_user.json
    positions/
      boss_intelligence_vault/
      zhilian_intelligence_vault/
```

### `collection_layer`

Reserved for collection commands and adapters.

Zhilian collection is split into job menu, job list, and job detail tools; archive handling is done by `archive_joblens_outputs`.

### `integrations/joblens`

Lightweight copy of the upstream Joblens project used by JobSniper.

The upstream source at `/home/xstars/programs/joblens` is treated as read-only for this integration. JobSniper loads the Chrome extension artifact from:

```text
integrations/joblens/dist
```

The copy intentionally excludes `node_modules` but keeps source, docs, scripts, `dist`, `builds`, and configuration files.

### `session_layer`

Reserved for user interaction sessions, audit traces, and recommendation workflows.

### `storage_layer/personas`

Stores candidate profile data.

The current persona file is:

```text
storage_layer/personas/current_user.json
```

It contains:

- candidate name
- target roles
- skill confidence scores
- audit notes explaining score changes

### `storage_layer/positions` (formerly `knowledge_vault`)

Stores recruitment intelligence artifacts organized by platform and a **natural nested (tree-based)** structure.

Each platform folder (e.g., `zhilian_intelligence_vault`) follows this hierarchy:
- **Platform Level**: contains `_Platform Index_[Platform Name].md` and Industry folders.
- **Industry Level**: contains `_Function Index_[Industry Name].md` and Function folders.
- **Function Level**: contains `_Occupation Index_[Function Name].md` and Occupation folders.
- **Occupation Level**: contains `_Job Index_[Occupation Name].md` and Job Details files.

Job Detail files follow the naming convention: `{Company Name}_{Job Title}.md`.

## MCP Resources

### `jobsniper://persona`

Returns the current candidate persona JSON.

If `current_user.json` does not exist, the server returns a default empty persona skeleton.

### `jobsniper://vault/positions/{platform}/{path_to_job}`

Returns a job detail Markdown file from the nested storage layer.

Example:

```text
jobsniper://vault/positions/zhilian/产品/互联网产品经理/AI产品经理/上海倍通医药科技咨询有限公司_AI产品经理.md
```

## MCP Tools

### `find_job_detail(platform: str, keyword: str, company: str | None = null, limit: int = 5)`

Searches job detail Markdown files by filename.

Parameters:

- `platform`: `zhilian` or `boss`
- `keyword`: job title or filename keyword
- `company`: optional company-name keyword
- `limit`: maximum number of matches to return

The response includes each matching file's absolute path, relative path, and readable resource URI.

### Collection Interface Types

JobSniper collection is split by data layer:

- **job menu**: platform job menu, usually an industry-function-occupation tree.
- **job list**: jobs under one occupation keyword.
- **job detail**: one concrete job posting detail page.

### `launch_zhilian_job_menu_collection(city_id: str = "538", debug: bool = true)`

Collects the Zhilian platform job menu and extracts the industry-function-occupation tree and keyword pool.

The tool opens:

```text
https://www.zhaopin.com/?jl={city_id}&clipper_keyword_discovery=1&clipper_debug=1
```

Output:

```text
zhilian_keyword_discovery_{timestamp}.md
```

### `launch_zhilian_job_list_collection(keyword: str, city_id: str = "538", pages: str = "auto", test: bool = false, debug: bool = true, wake_browser: bool = false)`

Collects the Zhilian job list under one occupation keyword via the background queue. It appends a task to `D:\\Downloads\\zhilian_list_tasks.jsonl`, then the Joblens extension processes it in the background and the monitor script archives the output automatically.

The generated URL includes:
- `clipper_auto=1`
- `jl={city_id}`
- `clipper_pages={pages}`
- `clipper_keyword_b64u={base64url(keyword)}`
- optional `clipper_test=1` and `clipper_debug=1`
- `clipper_list_queue=1` (queue mode)

If `wake_browser=true`, it also opens a lightweight wake page (`clipper_list_queue_wake=1`) to trigger a queue run immediately.

### `launch_zhilian_job_detail_collection(job_url: str, keyword: str = "", debug: bool = true)`

Collects one Zhilian job detail page. The tool opens the given job URL and appends:

- `clipper_job_detail=1`
- optional `clipper_keyword={keyword}`
- optional `clipper_debug=1`

Outputs include one job detail Markdown file, raw detail HTML, and a detail manifest. After archive, the Markdown becomes the final job-detail leaf:

```text
{Company Name}_{Job Title}.md
```

### Concept split

These two artifacts are intentionally different:

- **Keyword discovery artifact**: `zhilian_keyword_discovery_{timestamp}.md`
  - Produced from the Zhilian keyword discovery page.
  - Captures platform-level categories, keyword groups, and discovery time.
  - Stored at the root of `storage_layer/positions/`.
- **Platform index table**: `_行业索引表_智联招聘.md`
  - Stored inside `storage_layer/positions/zhilian_intelligence_vault/`.
  - Serves as the internal navigation table that connects industry, function, occupation, and job detail files.
  - It is not the direct output of the keyword discovery tool.

In short:

- The discovery artifact answers "what keywords and groups exist on Zhilian".
- The platform index table answers "how those groups are organized inside the vault".

### `archive_joblens_outputs(keyword: str, since_minutes: int = 60, dry_run: bool = false, include_test: bool = false)`

Scans `D:\Downloads` through `/mnt/d/Downloads` for recent `ZHILIAN_*` files and moves matching outputs into the JobSniper storage layer.

The tool resolves the nested path using industry and function mappings from the master task list.

Routing convention (Internal):
- `zhilian_keyword_discovery_*.md` -> `storage_layer/positions/` root as platform-level discovery artifact.
- `_行业索引表_智联招聘.md` -> `storage_layer/positions/zhilian_intelligence_vault/` root as the platform index table.
- `ZHILIAN_<keyword>_*.md` -> Occupation folder as Job Index (`_Job Index_[Occupation Name].md`).
- `ZHILIAN_RAW_<keyword>_*.json/html` -> `raw/` subdirectory within the Occupation folder.
- `ZHILIAN_DETAIL_{Company Name}_{Job Title}_{timestamp}.md` -> Final leaf in the tree structure (`{Company Name}_{Job Title}.md`).
- `ZHILIAN_DETAIL_RAW_*` and `ZHILIAN_DETAIL_MANIFEST_*` -> `raw/` subdirectory within the Occupation folder.

Recommended operating flow:

1. Launch collection:
```text
launch_zhilian_job_list_collection(keyword="AI产品经理", test=true, debug=true)
```

2. Wait until Joblens finishes writing downloads.

3. Preview archive moves:
```text
archive_joblens_outputs(keyword="AI产品经理", dry_run=true)
```

4. Archive the files:
```text
archive_joblens_outputs(keyword="AI产品经理", dry_run=false)
```

### `update_persona(skill_name: str, confidence_score: int, reasoning: str)`

Updates the current persona's skill confidence score.

Example fields written to `current_user.json`:

```json
{
  "skills": {
    "RAG/AI Engineering": {
      "score": 30,
      "last_audit_reason": "Built a working RAG demo project."
    }
  }
}
```

## Run

Install dependencies:

```bash
cd /home/xstars/programs/JobSniper
python -m pip install -r requirements.txt
```

From the project directory:

```bash
cd /home/xstars/programs/JobSniper
source venv/bin/activate
python mcp_server.py
```

The MCP server name is:

```text
FastMCP("JobSniper")
```

## Verification

The default smoke test covers Python import, persona reads, nested job-detail reads, job search, and archive dry-run behavior:

```bash
cd /home/xstars/programs/JobSniper
venv/bin/python scripts/smoke_mcp_server.py
```

Protocol-level stdio smoke test entrypoint:

```bash
venv/bin/python scripts/smoke_mcp_server.py --stdio --timeout 8
```

In the current environment, the protocol-level test passes and verifies `initialize`, `list_tools`, and `list_resources`.
