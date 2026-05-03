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
- MCP resource for reading L5 job detail Markdown files by job id
- MCP tool stub for triggering a clipper collection task
- MCP tool for launching Zhilian collection through the embedded Joblens Chrome extension
- MCP tool for archiving Joblens outputs from `D:\Downloads` into the knowledge vault
- MCP tool for updating persona skill confidence scores

Not implemented yet:

- Real collection scripts under `collection_layer`
- Session orchestration under `session_layer`
- L1-L5 knowledge material population
- Full recommendation or consulting workflow

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

The current `trigger_clipper` MCP tool is still a stub for single-page collection. Zhilian list/detail harvesting is handled by `launch_zhilian_collection` and `archive_joblens_outputs`.

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

## MCP Tools

### `trigger_clipper(url: str, job_title: str)`

Current behavior:

- returns a simulated collection-start message

Intended behavior:

- trigger Joblens or a platform-specific collector
- collect a job detail page
- save the result into the storage layer

### `launch_zhilian_collection(keyword: str, city_id: str = "538", pages: str = "auto", test: bool = false, detail_test: bool = false, detail_limit: int = 5, debug: bool = true)`

Launches Windows Chrome with the embedded Joblens extension and opens a Zhilian collection URL.

The generated URL includes:
- `clipper_auto=1`
- `jl={city_id}`
- `clipper_pages={pages}`
- `clipper_keyword_b64u={base64url(keyword)}`
- optional `clipper_test=1`, `clipper_detail_test=1`, and `clipper_debug=1`

The tool returns the collection URL, Chrome command, expected download directory, and suggested archive call.

### `archive_joblens_outputs(keyword: str, since_minutes: int = 60, dry_run: bool = false, include_test: bool = false)`

Scans `D:\Downloads` through `/mnt/d/Downloads` for recent `ZHILIAN_*` files and moves matching outputs into the JobSniper storage layer (`storage_layer/positions/zhilian_intelligence_vault/`).

The tool resolves the nested path using industry and function mappings from the master task list.

Routing convention (Internal):
- `ZHILIAN_KEYWORDS_*.md` -> Root of platform vault as Platform Index (`_Platform Index_[Platform Name].md`).
- `ZHILIAN_<keyword>_*.md` -> Occupation folder as Job Index (`_Job Index_[Occupation Name].md`).
- `ZHILIAN_RAW_<keyword>_*.json/html` -> `raw/` subdirectory within the Occupation folder.
- `ZHILIAN_DETAIL_*_<keyword>_*.md` -> Final leaf in the tree structure (`{Company Name}_{Job Title}.md`).

Recommended operating flow:

1. Launch collection:
```text
launch_zhilian_collection(keyword="AI产品经理", test=true, debug=true)
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

From the project directory:

```bash
cd /home/xstars/programs/JobSniper
source venv/bin/activate
python mcp_server.py
```