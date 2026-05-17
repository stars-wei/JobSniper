#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_import_smoke() -> None:
    import mcp_server

    persona = mcp_server.get_persona()
    _assert('"skills"' in persona, "persona resource should include skills")

    relative_path = "产品/互联网产品经理/AI产品经理/上海倍通医药科技咨询有限公司_AI产品经理.md"
    detail = mcp_server.get_position_detail("zhilian", relative_path)
    _assert("上海倍通医药科技咨询有限公司" in detail, "position resource should read an existing job file")

    search = json.loads(mcp_server.find_job_detail("zhilian", "AI产品经理", "上海倍通"))
    _assert(search["ok"] is True, "find_job_detail should succeed")
    _assert(search["count"] >= 1, "find_job_detail should return at least one match")

    keyword_discovery_target = mcp_server._target_for_joblens_output(  # type: ignore[attr-defined]
        Path("/mnt/d/Downloads/zhilian_keyword_discovery_20260504_024700.md"),
        "AI产品经理",
        {"industry": "产品", "domain": "互联网产品经理"},
        mcp_server.VAULT_PATH,  # type: ignore[attr-defined]
        "zhilian",
    )
    _assert(keyword_discovery_target is not None, "keyword discovery target should resolve")
    _assert(
        keyword_discovery_target.parent == mcp_server.POSITIONS_PATH,  # type: ignore[attr-defined]
        "keyword discovery should be archived to storage_layer/positions root",
    )
    _assert(
        keyword_discovery_target.name == "zhilian_keyword_discovery_20260504_024700.md",
        "keyword discovery filename should be preserved",
    )

    direct_detail_target = mcp_server._target_for_joblens_output(  # type: ignore[attr-defined]
        Path("/mnt/d/Downloads/ZHILIAN_DETAIL_测试公司_AI产品经理_20260504_031500.md"),
        "AI产品经理",
        {"industry": "产品", "domain": "互联网产品经理"},
        mcp_server.VAULT_PATH,  # type: ignore[attr-defined]
        "zhilian",
    )
    _assert(direct_detail_target is not None, "direct detail target should resolve")
    _assert(
        direct_detail_target.name == "测试公司_AI产品经理.md",
        "direct detail archive should strip transport prefix",
    )

    original_downloads_path = mcp_server.DOWNLOADS_PATH  # type: ignore[attr-defined]
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            discovery_file = tmp_path / "zhilian_keyword_discovery_20260504_031600.md"
            discovery_file.write_text("# discovery\n", encoding="utf-8")
            mcp_server.DOWNLOADS_PATH = str(tmp_path)  # type: ignore[attr-defined]
            archive_discovery = json.loads(
                mcp_server.archive_joblens_outputs("AI产品经理", since_minutes=10000, dry_run=True)
            )
            _assert(archive_discovery["planned_count"] == 1, "archive should detect lowercase keyword discovery files")
            _assert(
                Path(archive_discovery["planned"][0]["target"]).parent == mcp_server.POSITIONS_PATH,  # type: ignore[attr-defined]
                "archive should route keyword discovery files to storage_layer/positions root",
            )
    finally:
        mcp_server.DOWNLOADS_PATH = original_downloads_path  # type: ignore[attr-defined]

    archive = json.loads(mcp_server.archive_joblens_outputs("AI产品经理", since_minutes=10000, dry_run=True))
    _assert(archive["ok"] is True, "archive dry-run should succeed")

    print("import smoke passed")


async def run_stdio_smoke(timeout_seconds: float) -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=str(PROJECT_ROOT / "venv" / "bin" / "python"),
        args=[str(PROJECT_ROOT / "mcp_server.py")],
        cwd=str(PROJECT_ROOT),
    )

    async def _run() -> None:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                resources = await session.list_resources()
                tool_names = {tool.name for tool in tools.tools}
                resource_uris = {str(resource.uri) for resource in resources.resources}
                _assert(len(tool_names) == 6, f"MCP tool list should expose exactly 6 tools, got {len(tool_names)}")
                _assert("find_job_detail" in tool_names, "MCP tool list should include find_job_detail")
                _assert("launch_job_list_collection" in tool_names, "MCP tool list should include unified job list collection")
                _assert("launch_job_menu_collection" in tool_names, "MCP tool list should include unified job menu collection")
                _assert("launch_job_detail_collection" in tool_names, "MCP tool list should include unified job detail collection")
                _assert("launch_zhilian_job_list_collection" not in tool_names, "MCP should not expose deprecated wrappers")
                _assert("trigger_clipper" not in tool_names, "MCP tool list should not include trigger_clipper stub")
                _assert("launch_zhilian_collection" not in tool_names, "MCP tool list should not include legacy collection entrypoint")
                _assert("launch_zhilian_keyword_discovery" not in tool_names, "MCP tool list should not include legacy keyword-discovery entrypoint")
                _assert("jobsniper://persona" in resource_uris, "MCP resource list should include persona")

    await asyncio.wait_for(_run(), timeout=timeout_seconds)
    print("stdio smoke passed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test JobSniper MCP server behavior.")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Also run the protocol-level stdio MCP client smoke test.",
    )
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()

    try:
        run_import_smoke()
        if args.stdio:
            asyncio.run(run_stdio_smoke(args.timeout))
    except Exception as exc:
        print(f"smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
