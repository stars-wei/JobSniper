from mcp.server.fastmcp import FastMCP
from mcp.client.session import SessionMessage
from mcp import types
import anyio
import os
import json
import base64
import re
import shutil
import subprocess
import sys
import queue
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# 初始化 FastMCP
mcp = FastMCP("JobSniper")

# 基础路径配置
BASE_DIR = Path("/home/xstars/programs/JobSniper")
SANDBOX_DIR = Path("/home/xstars/zhilian_intelligence_sandbox")
STORAGE_PATH = BASE_DIR / "storage_layer"
PERSONA_PATH = STORAGE_PATH / "personas" / "current_user.json"
POSITIONS_PATH = STORAGE_PATH / "positions"
VAULT_PATH = POSITIONS_PATH / "zhilian_intelligence_vault"
BOSS_VAULT_PATH = POSITIONS_PATH / "boss_intelligence_vault"
TASKS_PATH = POSITIONS_PATH / "zhilian_master_tasks.json"
JOBLENS_PATH = BASE_DIR / "integrations" / "joblens"
JOBLENS_DIST_PATH = JOBLENS_PATH / "dist"
DOWNLOADS_PATH = "/mnt/d/Downloads"
WINDOWS_CHROME_PATH = "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"

# ----------------------------------------------------------------
# Resources: 暴露本地情报数据
# ----------------------------------------------------------------

@mcp.resource("jobsniper://persona")
def get_persona() -> str:
    """获取当前求职者的动态画像及其技能置信度"""
    if not PERSONA_PATH.exists():
        # 如果文件不存在，返回一个默认骨架
        default_persona = {
            "name": "User",
            "goals": [],
            "skills": {},
            "audit_log": []
        }
        return json.dumps(default_persona, indent=2, ensure_ascii=False)
    
    with open(PERSONA_PATH, "r", encoding="utf-8") as f:
        return f.read()

def _platform_vault_path(platform: str) -> Path:
    normalized = platform.strip().lower()
    aliases = {
        "zhilian": VAULT_PATH,
        "智联": VAULT_PATH,
        "智联招聘": VAULT_PATH,
        "boss": BOSS_VAULT_PATH,
        "boss直聘": BOSS_VAULT_PATH,
    }
    if normalized not in aliases:
        raise ValueError("platform must be one of: zhilian, boss")
    return aliases[normalized]

def _safe_relative_path(value: str) -> Path:
    relative = Path(value.strip().strip("/"))
    if not str(relative) or relative.is_absolute() or ".." in relative.parts:
        raise ValueError("path_to_job must be a relative path inside the platform vault")
    return relative

def _read_text_file(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def _find_job_files(vault_path: Path, keyword: str, company: str | None = None) -> list[Path]:
    normalized_keyword = keyword.strip().lower()
    normalized_company = company.strip().lower() if company else None
    if not normalized_keyword:
        return []

    matches: list[Path] = []
    for file_path in vault_path.rglob("*.md"):
        name = file_path.name
        if name.startswith("_"):
            continue
        normalized_name = name.lower()
        if normalized_keyword not in normalized_name:
            continue
        if normalized_company and normalized_company not in normalized_name:
            continue
        matches.append(file_path)
    return sorted(matches)

@mcp.resource("jobsniper://vault/positions/{platform}/{path_to_job}")
def get_position_detail(platform: str, path_to_job: str) -> str:
    """按自然嵌套路径读取岗位详情 Markdown。"""
    try:
        vault_path = _platform_vault_path(platform)
        relative_path = _safe_relative_path(path_to_job)
    except ValueError as exc:
        return str(exc)

    file_path = vault_path / relative_path
    if file_path.suffix != ".md":
        file_path = file_path.with_suffix(".md")
    try:
        file_path.resolve().relative_to(vault_path.resolve())
    except ValueError:
        return "path_to_job must stay inside the platform vault"

    if not file_path.exists():
        return f"未找到岗位详情文件: {file_path}"
    return _read_text_file(file_path)

# ----------------------------------------------------------------
# Tools: 暴露操作指令
# ----------------------------------------------------------------

@mcp.tool()
def find_job_detail(platform: str, keyword: str, company: str | None = None, limit: int = 5) -> str:
    """
    在自然嵌套岗位库中按文件名搜索岗位详情。
    参数:
    - platform: zhilian 或 boss
    - keyword: 岗位名或文件名关键词
    - company: 可选公司名关键词
    - limit: 最多返回的匹配数量
    """
    try:
        vault_path = _platform_vault_path(platform)
    except ValueError as exc:
        return _json_response({"ok": False, "error": str(exc)})

    if limit <= 0:
        return _json_response({"ok": False, "error": "limit must be greater than 0"})

    matches = _find_job_files(vault_path, keyword, company)[:limit]
    return _json_response({
        "ok": True,
        "platform": platform,
        "keyword": keyword,
        "company": company,
        "count": len(matches),
        "matches": [
            {
                "path": str(path),
                "relative_path": str(path.relative_to(vault_path)),
                "resource_uri": f"jobsniper://vault/positions/{platform}/{path.relative_to(vault_path)}",
            }
            for path in matches
        ],
    })

def _json_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)

def _base64url_utf8(value: str) -> str:
    encoded = base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")

def _windows_path(path: str) -> str:
    try:
        result = subprocess.run(
            ["wslpath", "-w", path],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return path

def _safe_keyword_dir(keyword: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", keyword).strip()
    return cleaned or "Unknown"

def _job_category_dir(keyword: str, task: dict[str, str], vault_path: Path) -> Path:
    industry_dir = _safe_keyword_dir(task["industry"])
    domain_dir = _safe_keyword_dir(task["domain"])
    keyword_dir = _safe_keyword_dir(keyword)
    return vault_path / industry_dir / domain_dir / keyword_dir

def _platform_task_prefix(platform: str) -> str:
    return "ZHILIAN" if platform == "zhilian" else "BOSS"

def _load_zhilian_task(keyword: str) -> dict[str, str]:
    fallback = {
        "keyword": keyword,
        "industry": "Unknown_Industry",
        "domain": "Unknown_Domain",
        "url": "",
    }
    try:
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    except Exception:
        return fallback

    for task in tasks:
        if task.get("keyword") == keyword:
            return {
                "keyword": task.get("keyword", keyword),
                "industry": task.get("industry") or fallback["industry"],
                "domain": task.get("domain") or fallback["domain"],
                "url": task.get("url") or "",
            }
    return fallback

def _parse_frontmatter_keyword(file_path: Path) -> str | None:
    """从 markdown 文件 YAML frontmatter 中提取 keyword 字段。"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, min(len(lines), 30)):
        line = lines[i].strip()
        if line == "---":
            break
        m = re.match(r"^keyword:\s*(.+)", line)
        if m:
            return m.group(1).strip()
    return None

def _contains_keyword(file_name: str, keyword: str) -> bool:
    normalized_name = file_name.lower()
    normalized_keyword = keyword.lower()
    if normalized_keyword in normalized_name:
        return True
    encoded_keyword = _base64url_utf8(keyword).lower()
    return encoded_keyword and encoded_keyword in normalized_name

def _target_for_joblens_output(file_path: Path, keyword: str, task: dict[str, str], vault_path: Path, platform: str) -> Path | None:
    name = file_path.name
    suffix = file_path.suffix.lower()
    pfx = _platform_task_prefix(platform)
    is_raw = suffix in {".json", ".html"} or "_RAW_" in name or name.startswith(f"{pfx}_RAW_")
    job_dir = _job_category_dir(keyword, task, vault_path)

    if (name.startswith("zhilian_keyword_discovery_") or name.startswith(f"{pfx}_KEYWORDS_")) and suffix == ".md":
        return POSITIONS_PATH / name

    if name.startswith(f"{pfx}_DETAIL_"):
        if is_raw:
            return job_dir / "raw" / name
        direct_detail_match = re.match(rf"{pfx}_DETAIL_(.+)_\d{{8}}_\d{{6}}\.md$", name)
        if direct_detail_match:
            return job_dir / f"{direct_detail_match.group(1)}.md"
        return job_dir / name

    if name.startswith(f"{pfx}_RAW_"):
        return job_dir / "raw" / name

    if name.startswith(f"{pfx}_") and suffix == ".md":
        return job_dir / f"_岗位索引表_{_safe_keyword_dir(keyword)}.md"

    if suffix == ".md":
        return job_dir / name

    return None

def _unique_target_path(target: Path) -> Path:
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    parent = target.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1

def _launch_zhilian_with_url(collection_url: str, keyword: str, launch_label: str) -> str:
    chrome_command = [
        WINDOWS_CHROME_PATH,
        collection_url,
    ]

    result: dict[str, Any] = {
        "ok": False,
        "url": collection_url,
        "chrome_command": chrome_command,
        "expected_download_dir": DOWNLOADS_PATH,
        "launch_label": launch_label,
        "suggested_archive_tool": (
            f'archive_joblens_outputs(keyword="{keyword}", platform="zhilian", since_minutes=60, '
            "dry_run=true, include_test=false)"
        ),
    }

    if not (JOBLENS_DIST_PATH / "manifest.json").exists():
        result["error"] = "Joblens dist/manifest.json not found"
        return _json_response(result)
    if not os.path.exists(WINDOWS_CHROME_PATH):
        result["error"] = "Windows Chrome executable not found"
        return _json_response(result)

    try:
        subprocess.Popen(chrome_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result["ok"] = True
        result["message"] = "Chrome launched with default profile."
    except Exception as exc:
        result["error"] = f"Failed to launch Chrome: {exc}"

    return _json_response(result)

@mcp.tool()
def launch_zhilian_job_list_collection(
    keyword: str,
    city_id: str = "538",
    pages: str = "auto",
    test: bool = False,
    debug: bool = True,
) -> str:
    """
    采集智联某个职业关键词下的岗位列表。
    """
    if not keyword.strip():
        return _json_response({"ok": False, "error": "keyword must not be empty"})

    params: dict[str, str] = {
        "kw": keyword,
        "jl": city_id,
        "cityId": city_id,
        "clipper_city": city_id,
        "clipper_auto": "1",
        "clipper_pages": str(pages),
        "clipper_keyword": keyword,
        "clipper_keyword_b64u": _base64url_utf8(keyword),
    }
    if test:
        params["clipper_test"] = "1"
    if debug:
        params["clipper_debug"] = "1"

    collection_url = f"https://sou.zhaopin.com/?{urlencode(params)}"
    return _launch_zhilian_with_url(collection_url, keyword, "zhilian_job_list")

@mcp.tool()
def launch_zhilian_job_menu_collection(
    city_id: str = "538",
    debug: bool = True,
) -> str:
    """
    采集智联平台 job menu，提取行业-职能-职业三级结构。
    """
    params: dict[str, str] = {
        "jl": city_id,
        "clipper_keyword_discovery": "1",
    }
    if debug:
        params["clipper_debug"] = "1"

    collection_url = f"https://www.zhaopin.com/?{urlencode(params)}"
    return _launch_zhilian_with_url(collection_url, "job_menu", "zhilian_job_menu")

@mcp.tool()
def launch_zhilian_job_detail_collection(
    job_url: str,
    keyword: str = "",
    debug: bool = True,
) -> str:
    """
    采集智联单个岗位详情页。通过写入任务文件，由 Chrome 扩展后台静默采集。
    """
    if not job_url.strip():
        return _json_response({"ok": False, "error": "job_url must not be empty"})
    try:
        parsed = urlparse(job_url)
    except Exception:
        return _json_response({"ok": False, "error": "job_url is invalid"})
    if parsed.scheme not in {"http", "https"} or "zhaopin.com" not in parsed.netloc:
        return _json_response({"ok": False, "error": "job_url must be a zhaopin.com http(s) URL"})

    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    params["clipper_job_detail"] = "1"
    if keyword.strip():
        params["clipper_keyword"] = keyword.strip()
        params["clipper_keyword_b64u"] = _base64url_utf8(keyword.strip())
    if debug:
        params["clipper_debug"] = "1"
    detail_url = urlunparse(parsed._replace(query=urlencode(params)))

    # Write to detail task queue file for the Chrome extension to pick up
    task_file = Path(DOWNLOADS_PATH) / "zhilian_detail_tasks.jsonl"
    task_line = json.dumps({"url": detail_url, "keyword": keyword.strip() or "job_detail"}) + "\n"
    try:
        with open(task_file, "a", encoding="utf-8") as f:
            f.write(task_line)
        return _json_response({
            "ok": True,
            "url": detail_url,
            "task_file": str(task_file),
            "message": "Task enqueued. Chrome extension will process it in background.",
        })
    except Exception as exc:
        return _json_response({"ok": False, "error": f"Failed to write task file: {exc}"})

@mcp.tool()
def archive_joblens_outputs(
    keyword: str,
    platform: str = "zhilian",
    since_minutes: int = 60,
    dry_run: bool = False,
    include_test: bool = False,
) -> str:
    """
    将 D:\\Downloads 中的 Joblens 输出归档到 storage_layer/positions/{platform}_intelligence_vault。
    - platform=zhilian → storage_layer/positions/zhilian_intelligence_vault
    - platform=boss    → storage_layer/positions/boss_intelligence_vault
    参数:
    - platform: zhilian 或 boss
    """
    if not keyword.strip():
        return _json_response({"ok": False, "error": "keyword must not be empty"})
    if since_minutes <= 0:
        return _json_response({"ok": False, "error": "since_minutes must be greater than 0"})

    try:
        vault_path = _platform_vault_path(platform)
    except ValueError as exc:
        return _json_response({"ok": False, "error": str(exc)})

    downloads = Path(DOWNLOADS_PATH)
    cutoff = datetime.now() - timedelta(minutes=since_minutes)
    task = _load_zhilian_task(keyword)
    pfx = _platform_task_prefix(platform)
    planned: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    if not downloads.exists():
        return _json_response({"ok": False, "error": f"downloads path not found: {DOWNLOADS_PATH}"})

    candidates = {
        path
        for pattern in (f"{pfx}_*", "zhilian_keyword_discovery_*.md")
        for path in downloads.glob(pattern)
    }
    for file_path in sorted(candidates):
        if not file_path.is_file():
            continue
        modified = datetime.fromtimestamp(file_path.stat().st_mtime)
        if modified < cutoff:
            skipped.append({"file": str(file_path), "reason": "outside since_minutes window"})
            continue
        if not include_test and "TEST" in file_path.name.upper():
            skipped.append({"file": str(file_path), "reason": "TEST output excluded"})
            continue
        if file_path.suffix.lower() != ".md":
            skipped.append({"file": str(file_path), "reason": "not a markdown file"})
            continue
        if file_path.name.startswith((f"{pfx}_DETAIL_RAW_", f"{pfx}_DETAIL_MANIFEST_", f"{pfx}_RAW_")):
            skipped.append({"file": str(file_path), "reason": "raw or manifest file"})
            continue

        # For detail files, try to read keyword from YAML frontmatter
        is_detail = file_path.name.startswith(f"{pfx}_DETAIL_") and not file_path.name.startswith((f"{pfx}_DETAIL_RAW_", f"{pfx}_DETAIL_MANIFEST_"))
        frontmatter_keyword = _parse_frontmatter_keyword(file_path) if (is_detail and file_path.suffix.lower() == ".md") else None

        if (
            not file_path.name.startswith((f"{pfx}_KEYWORDS_", "zhilian_keyword_discovery_", f"{pfx}_DETAIL_RAW_", f"{pfx}_DETAIL_MANIFEST_"))
            and not re.match(rf"{pfx}_DETAIL_.+_\d{{8}}_\d{{6}}\.md$", file_path.name)
            and not _contains_keyword(file_path.name, keyword)
        ):
            skipped.append({"file": str(file_path), "reason": "keyword mismatch"})
            continue

        file_task = _load_zhilian_task(frontmatter_keyword) if frontmatter_keyword else task
        file_keyword = frontmatter_keyword if frontmatter_keyword else keyword
        target = _target_for_joblens_output(file_path, file_keyword, file_task, vault_path, platform)
        if target is None:
            skipped.append({"file": str(file_path), "reason": "unrecognized Joblens output pattern"})
            continue
        final_target = _unique_target_path(target)
        planned.append({
            "source": str(file_path),
            "target": str(final_target),
            "modified": modified.isoformat(timespec="seconds"),
        })

    moved: list[dict[str, str]] = []
    if not dry_run:
        for item in planned:
            source = Path(item["source"])
            target = Path(item["target"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            moved.append({"source": str(source), "target": str(target)})

    return _json_response({
        "ok": True,
        "dry_run": dry_run,
        "platform": platform,
        "keyword": keyword,
        "task": task,
        "since_minutes": since_minutes,
        "include_test": include_test,
        "planned_count": len(planned),
        "moved_count": len(moved),
        "planned": planned,
        "moved": moved,
        "skipped_count": len(skipped),
        "skipped": skipped,
    })

@mcp.tool()
def update_persona(skill_name: str, confidence_score: int, reasoning: str) -> str:
    """
    更新用户画像中的技能置信度。
    参数:
    - skill_name: 技能名称 (如 'Python', 'RAG')
    - confidence_score: 调整后的分值 (0-100)
    - reasoning: 调整原因
    """
    # 简单的持久化逻辑
    data = {}
    if PERSONA_PATH.exists():
        with open(PERSONA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    
    if "skills" not in data: data["skills"] = {}
    data["skills"][skill_name] = {
        "score": confidence_score,
        "last_audit_reason": reasoning
    }
    
    # 确保目录存在
    PERSONA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PERSONA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    return f"[Spotter] 画像已更新：{skill_name} 置信度 -> {confidence_score}。原因：{reasoning}"

async def _run_stdio_transport() -> None:
    read_stream_writer, read_stream = anyio.create_memory_object_stream[SessionMessage | Exception](0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream[SessionMessage](0)
    stdin_queue: queue.Queue[SessionMessage | Exception | None] = queue.Queue()

    def stdin_reader() -> None:
        try:
            while True:
                line = sys.stdin.readline()
                if line == "":
                    stdin_queue.put(None)
                    return
                try:
                    message = types.JSONRPCMessage.model_validate_json(line)
                except Exception as exc:
                    stdin_queue.put(exc)
                    continue
                stdin_queue.put(SessionMessage(message))
        except Exception as exc:
            stdin_queue.put(exc)
        finally:
            stdin_queue.put(None)

    async def queue_pump() -> None:
        while True:
            try:
                item = stdin_queue.get_nowait()
            except queue.Empty:
                await anyio.sleep(0.01)
                continue
            if item is None:
                break
            await read_stream_writer.send(item)

    async def stdout_pump() -> None:
        async with write_stream_reader:
            async for session_message in write_stream_reader:
                payload = session_message.message.model_dump_json(by_alias=True, exclude_none=True)
                sys.stdout.write(payload + "\n")
                sys.stdout.flush()

    reader = threading.Thread(target=stdin_reader, daemon=True)
    reader.start()

    async with read_stream_writer, write_stream:
        async with anyio.create_task_group() as tg:
            tg.start_soon(queue_pump)
            tg.start_soon(stdout_pump)
            await mcp._mcp_server.run(
                read_stream,
                write_stream,
                mcp._mcp_server.create_initialization_options(),
            )

if __name__ == "__main__":
    anyio.run(_run_stdio_transport)
