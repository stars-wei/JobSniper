# JobSniper 项目开发日志

## 记录规则
*   日志按时间倒序排列，最新记录在上。
*   新记录插入到“日志时间线”下方、现有最新记录上方。
*   每条记录必须包含时间戳、执行人或署名。
*   不删除其他人的原始记录；如需修正，通过新增记录说明。
*   开发日志记录人工/Agent 的开发过程。

---

## 日志时间线

## [2026-05-04] - 删除 trigger_clipper 占位工具 (Codex)

### 会话纪要
`trigger_clipper` 只是早期模拟采集启动的占位工具，没有真实采集行为。为保持 MCP Server 工具面简洁，本次将其从 MCP Tools 中删除。

### 主要变更

#### 1. 工具删除
- 删除 `trigger_clipper(url, job_title)`。
- MCP Server 采集入口只保留 job menu、job list、job detail 三个正式工具。

#### 2. 文档更新
- README 移除 `trigger_clipper` 段落和占位说明。

#### 3. 测试约束
- smoke test 增加 `trigger_clipper` 不应出现在 `list_tools` 中的反向断言。
- smoke test 将工具数量收紧为 6 个。

### 验证
- `venv/bin/python -m py_compile mcp_server.py scripts/smoke_mcp_server.py`：通过。
- `venv/bin/python scripts/smoke_mcp_server.py`：通过。
- `venv/bin/python scripts/smoke_mcp_server.py --stdio --timeout 8`：通过。
- 直接 `list_tools` 确认当前仅暴露 6 个工具，`trigger_clipper` 已消失。

### 署名
**Codex**
*Timestamp: 2026-05-04 13:01 (Asia/Shanghai)*

---

## [2026-05-04] - 移除智联采集旧兼容入口 (Codex)

### 会话纪要
为保持 MCP Server 工具面简洁，本次移除旧的智联采集兼容入口，只保留三类 canonical 采集工具：

- `launch_zhilian_job_menu_collection()`
- `launch_zhilian_job_list_collection()`
- `launch_zhilian_job_detail_collection()`

### 主要变更

#### 1. 删除旧工具
- 删除 `launch_zhilian_collection()`。
- 删除 `launch_zhilian_keyword_discovery()`。
- 不再通过 `detail_test` 暴露“列表后抽样详情采集”语义。

#### 2. 测试约束
- smoke test 增加反向断言，确保旧工具不再出现在 `list_tools` 中。

#### 3. 文档更新
- README 移除兼容入口章节。
- 采集说明只保留 job menu、job list、job detail 三类入口。

### 验证
- `venv/bin/python -m py_compile mcp_server.py scripts/smoke_mcp_server.py`：通过。
- `venv/bin/python scripts/smoke_mcp_server.py`：通过。
- `venv/bin/python scripts/smoke_mcp_server.py --stdio --timeout 8`：通过。
- 直接 `list_tools` 确认当前仅暴露 7 个工具，旧入口 `launch_zhilian_collection` 与 `launch_zhilian_keyword_discovery` 已消失。

### 署名
**Codex**
*Timestamp: 2026-05-04 12:56 (Asia/Shanghai)*

---

## [2026-05-04] - 智联采集接口按三类数据分型 (Codex)

### 会话纪要
本次将 JobSniper 的智联采集能力明确拆成三种数据类型：

- job menu：平台岗位菜单，按行业-职能-职业组织。
- job list：某个职业关键词下的岗位列表。
- job detail：某个具体岗位的招聘详情页。

这样可以避免继续把“详情采集”隐藏在列表采集的 `detail_test` 参数里，也让 MCP Client 能按目标数据层级选择工具。

### 主要变更

#### 1. MCP 工具分型
- 新增 `launch_zhilian_job_menu_collection()`，作为智联 job menu 的主入口。
- 新增 `launch_zhilian_job_list_collection()`，作为智联 job list 的主入口。
- 新增 `launch_zhilian_job_detail_collection()`，作为智联 job detail 的主入口。
- 最初曾保留 `launch_zhilian_collection()` 和 `launch_zhilian_keyword_discovery()` 作为兼容入口；后续已通过新增日志记录移除。

#### 2. 详情页直接采集
- 在 Joblens content script 中新增 `clipper_job_detail=1` 自动模式。
- 直接详情采集会导出 `ZHILIAN_DETAIL_{公司名称}_{岗位名称}_{timestamp}.md`、Raw HTML 和 manifest。
- 归档时将传输前缀剥离，最终落为 `{公司名称}_{岗位名称}.md`。

#### 3. 归档修正
- `archive_joblens_outputs()` 现在能识别小写的 `zhilian_keyword_discovery_*.md`。
- `ZHILIAN_DETAIL_RAW_*` 和 `ZHILIAN_DETAIL_MANIFEST_*` 归入职业目录下的 `raw/`。

### 验证
- `venv/bin/python -m py_compile mcp_server.py scripts/smoke_mcp_server.py`：通过。
- `venv/bin/python scripts/smoke_mcp_server.py`：通过。
- `venv/bin/python scripts/smoke_mcp_server.py --stdio --timeout 8`：通过，MCP Client 可完成 `initialize`、`list_tools` 和 `list_resources`，并能看到三类采集工具。
- `npm run build:chrome`：通过，已重新生成 `integrations/joblens/dist/content.js` 和 Chrome zip。

### 署名
**Codex**
*Timestamp: 2026-05-04 03:24 (Asia/Shanghai)*

---

## [2026-05-04] - 旧关键词前缀归档语义更正 (Codex)

### 会话纪要
历史上 `ZHILIAN_KEYWORDS_*.md` 曾被描述成归入 `_行业索引表_智联招聘.md`，但当前 JobSniper 的实际语义已经拆开：

- `zhilian_keyword_discovery_{timestamp}.md` 是关键词发现产物，归档到 `storage_layer/positions/` 根目录。
- `_行业索引表_智联招聘.md` 是平台索引表，保留在 `storage_layer/positions/zhilian_intelligence_vault/` 内。
- 旧的 `ZHILIAN_KEYWORDS_*.md` 仅作为历史前缀保留兼容识别，不再代表平台索引表产物。

### 主要变更

#### 1. 语义更正
- 明确把旧前缀从“平台索引表产物”语义中剥离出来。
- 现行归档逻辑不再把关键词发现结果写入 `_行业索引表_智联招聘.md`。

### 署名
**Codex**
*Timestamp: 2026-05-04 03:02 (Asia/Shanghai)*

---

## [2026-05-04] - 关键词发现产物与平台索引表拆分说明 (Codex)

### 会话纪要
本次把智联“关键词发现产物”和“平台索引表”明确拆成两个不同概念：

- 关键词发现产物是 `zhilian_keyword_discovery_{timestamp}.md`，存放在 `storage_layer/positions/` 根目录。
- 平台索引表是 `_行业索引表_智联招聘.md`，存放在 `storage_layer/positions/zhilian_intelligence_vault/` 根目录。

这样做是为了避免把“发现了什么”与“仓库树如何组织”混为一谈。前者属于平台级外部发现结果，后者属于 JobSniper 内部导航结构。

### 主要变更

#### 1. 文档拆分
- 在中英文 README 中新增“概念区分 / Concept split”段落。
- 明确关键词发现产物和平台索引表的职责、文件名和落点都不同。

#### 2. 归档说明补全
- 在归档规则里同时标注：
  - `zhilian_keyword_discovery_*.md` -> `storage_layer/positions/`
  - `_行业索引表_智联招聘.md` -> `storage_layer/positions/zhilian_intelligence_vault/`

### 验证结果
- 文档检索结果显示，两类概念已分别出现在 README 和开发日志中，不再共用同一条描述。

### 署名
**Codex**
*Timestamp: 2026-05-04 03:02 (Asia/Shanghai)*

---

## [2026-05-04] - 智联关键词发现产物落点修正 (Codex)

### 会话纪要
在命名统一为 `{platform}_keyword_discovery_{timestamp}.md` 之后，进一步将其归档落点修正为 `storage_layer/positions/` 根目录，而不是 `zhilian_intelligence_vault` 内部的行业索引表文件。这样可以把关键词发现产物明确为平台级根文件，避免和岗位详情库混在一起。

### 主要变更

#### 1. 归档目标修正
- `archive_joblens_outputs()` 中的关键词发现文件目标由 `_行业索引表_智联招聘.md` 改为 `storage_layer/positions/{file_name}`。
- 新命名与历史命名都可以被识别，归档时直接落在 `storage_layer/positions/` 根目录。

#### 2. 文档同步
- 更新中英文 README，明确 `zhilian_keyword_discovery_*.md` 是 `storage_layer/positions/` 根目录下的平台级发现产物。

### 验证结果
- `rg -n "zhilian_keyword_discovery_" mcp_server.py README.md README.zh-CN.md docs/DEV_LOG.md`：确认命名与落点说明已对齐。

### 署名
**Codex**
*Timestamp: 2026-05-04 02:47 (Asia/Shanghai)*

---

## [2026-05-04] - 智联关键词发现产物命名收敛 (Codex)

### 会话纪要
本次将智联“关键词发现”的产物命名统一收敛为 `{platform}_keyword_discovery_{timestamp}.md`，其中平台当前固定为 `zhilian`。这一步同时对齐了源码、运行时构建产物与归档映射，避免源代码与浏览器导出文件继续使用旧的 `ZHILIAN_KEYWORDS_*.md` 形式。

### 主要变更

#### 1. 关键词发现导出命名
- 将 `integrations/joblens/src/content.ts` 中的关键词发现导出文件名改为 `zhilian_keyword_discovery_{timestamp}.md`。
- 保留正文中的分类与来源信息，文件名只承担平台、产物类型和时间戳三项职责。

#### 2. 运行时构建产物同步
- 同步更新 `integrations/joblens/dist/content.js`，确保浏览器实际执行的打包产物也输出新文件名。
- 避免只改源码、不改 `dist` 导致的运行时偏差。

#### 3. 归档映射兼容
- `archive_joblens_outputs()` 已接收新前缀 `zhilian_keyword_discovery_`。
- 旧前缀 `ZHILIAN_KEYWORDS_` 仍可被识别，用于历史文件归档，不影响新产物落点。

### 验证结果
- `rg -n "zhilian_keyword_discovery_" integrations/joblens/src/content.ts integrations/joblens/dist/content.js mcp_server.py README.md README.zh-CN.md`：确认源码、运行时构建产物、归档路由与文档已对齐。

### 署名
**Codex**
*Timestamp: 2026-05-04 02:45 (Asia/Shanghai)*

---

## [2026-05-04] - 智联关键词发现工具拆分 (Codex)

### 会话纪要
根据 Joblens 的现有自动化指南，智联“关键词发现”与普通岗位列表采集是两个不同入口。本次将其从 `launch_zhilian_collection()` 中拆分出来，新增独立 MCP Tool `launch_zhilian_keyword_discovery()`，使 Agent 可以直接选择岗位分级/关键词树的发现流程，而不必携带普通搜索参数。

### 主要变更

#### 1. 新增专用 Tool
- 新增 `launch_zhilian_keyword_discovery(city_id="538", debug=true)`。
- 该工具固定打开 `https://www.zhaopin.com/?jl={city_id}&clipper_keyword_discovery=1&clipper_debug=1`。
- 与普通列表采集工具分离，避免参数膨胀和语义混淆。

#### 2. 复用启动逻辑
- 抽出私有 helper 统一封装 Chrome 启动、扩展挂载和返回结果结构。
- `launch_zhilian_collection()` 保持原有普通采集语义不变。

#### 3. 验证与文档
- 更新 smoke test，确认 MCP 工具列表中可见 `launch_zhilian_keyword_discovery`。
- 更新中英文 README，补充新工具的用途和 URL 模式。

### 验证结果
- `venv/bin/python -m py_compile mcp_server.py scripts/smoke_mcp_server.py`：通过。
- `venv/bin/python scripts/smoke_mcp_server.py`：通过。
- `venv/bin/python scripts/smoke_mcp_server.py --stdio --timeout 8`：通过。
- `venv/bin/python -c "import mcp_server; print(mcp_server.launch_zhilian_keyword_discovery(debug=True))"`：返回关键词发现 URL 和 Chrome 启动命令。

### 署名
**Codex**
*Timestamp: 2026-05-04 01:49 (Asia/Shanghai)*

---

## [2026-05-04] - FastMCP stdio 握手修复 (Codex)

### 会话纪要
本次执行定位并修复了 FastMCP stdio 握手超时问题。根因不在业务工具注册，而在默认 `stdio_server()` 的输入适配在当前环境下无法稳定把 stdin 请求推进到 MCP session，导致客户端在 `initialize` 阶段一直等不到响应。

### 定位过程

#### 1. 逐段验证 MCP 生命周期
- 函数级 smoke test 可通过，说明资源与工具实现本身没有语法或注册问题。
- 协议级 stdio smoke test 卡在 `initialize()`，说明问题出在传输层，而不是 `list_tools` 或 `list_resources`。

#### 2. 验证默认 stdio transport
- 通过直接运行 `stdio_server()` 复现了“上下文可进入，但请求未被消费”的现象。
- 进一步对比原生 `sys.stdin.readline()` 与线程读取后确认，问题集中在默认 async/file wrapper 的 stdin 适配，而不是 MCP 业务逻辑。

#### 3. 替换为显式 stdin/stdout 适配器
- 在 `mcp_server.py` 中移除对 `mcp.run()` 默认 stdio transport 的依赖。
- 改为自建 stdio 入口：独立线程同步读取 stdin，每行解析成 JSON-RPC 消息后送入 FastMCP 内部 session；stdout 侧直接写回 JSON-RPC 响应并 flush。
- 保留 FastMCP 的工具、资源与会话管理，仅替换传输层。

### 验证结果
- `venv/bin/python scripts/smoke_mcp_server.py`：通过。
- `venv/bin/python scripts/smoke_mcp_server.py --stdio --timeout 8`：通过。
- 客户端已可完成 `initialize`、`list_tools`、`list_resources`。

### 影响范围
- MCP 行为层未改动，仍保持 `jobsniper://persona`、`jobsniper://vault/positions/{platform}/{path_to_job}` 和 `find_job_detail()` 的现有语义。
- 仅变更 stdio 传输实现，提升了本地 CLI 客户端的可用性。

### 署名
**Codex**
*Timestamp: 2026-05-04 00:45 (Asia/Shanghai)*

---

## [2026-05-04] - MCP Server 存储规范对齐执行记录 (Codex)

### 会话纪要
本次执行根据上一条修复计划，对 `mcp_server.py`、README 和依赖说明进行了第一轮落地修复。重点是把 MCP 暴露层从旧 `L1-L5` 假设迁移到 `storage_layer/positions/{platform}_intelligence_vault` 自然嵌套结构，并补充可重复的 smoke test 入口。

### 主要变更

#### 1. MCP 路径与 Resource 对齐
- 将智联和 BOSS Vault 路径统一到 `storage_layer/positions/zhilian_intelligence_vault` 与 `storage_layer/positions/boss_intelligence_vault`。
- 新增 `jobsniper://vault/positions/{platform}/{path_to_job}` Resource，用于按自然嵌套路径读取岗位详情 Markdown。
- 不再保留 `jobsniper://vault/L5/{job_id}` 入口，避免旧 `L1-L5` 假设继续向外暴露。

#### 2. 岗位搜索 Tool
- 新增 `find_job_detail(platform, keyword, company=None, limit=5)`，用于在 Agent 不知道完整目录路径时搜索岗位详情。
- 返回匹配文件的绝对路径、相对路径和可读取的 Resource URI。

#### 3. Joblens 归档目标路径修正
- `archive_joblens_outputs()` 不再生成 `L1` / `L4` / `L5` 目录。
- 归档目标改为 `storage_layer/positions/zhilian_intelligence_vault/{行业}/{职能}/{职业}/`。
- `ZHILIAN_KEYWORDS_*.md` 路由到 `_行业索引表_智联招聘.md`。
- `ZHILIAN_<keyword>_*.md` 路由到 `_岗位索引表_{keyword}.md`。
- raw 输出进入职业目录下的 `raw/` 子目录。

#### 4. 依赖与验证入口
- 新增 `requirements.txt`，声明 MCP Server 当前最小依赖 `mcp==1.27.0`。
- 新增 `scripts/smoke_mcp_server.py`。
- 默认 smoke test 覆盖 Python 导入、画像读取、自然路径岗位详情读取、岗位搜索和归档 dry-run。
- 保留 `--stdio` 参数用于协议级 MCP stdio 验证。

#### 5. README 同步
- 更新中英文 README 的当前状态、Resource、Tool、归档规则、依赖安装和验证方式。
- 明确协议级 stdio smoke test 当前仍可能超时，作为后续定位目标。

### 验证结果
- `venv/bin/python -m py_compile mcp_server.py scripts/smoke_mcp_server.py`：通过。
- `venv/bin/python scripts/smoke_mcp_server.py`：通过。
- `venv/bin/python scripts/smoke_mcp_server.py --stdio --timeout 8`：通过。
- 已验证 `上海倍通医药科技咨询有限公司_AI产品经理.md` 可通过新 Resource 读取。

### 后续事项
- 继续定位 FastMCP stdio 握手超时问题，目标是让 MCP 客户端完成 `initialize`、`list_tools` 和 `list_resources`。
- 对 `archive_joblens_outputs()` 做带样例文件的 dry-run 单元测试，确认文件名路由和重名策略符合预期。
- 根据实际客户端能力确认 `jobsniper://vault/positions/{platform}/{path_to_job}` 是否需要 URL 编码或改为只通过搜索 Tool 暴露。

### 署名
**Codex**
*Timestamp: 2026-05-04 00:27 (Asia/Shanghai)*

---

## [2026-05-04] - MCP Server 完备性修复计划 (Codex)

### 会话纪要
本会话对 JobSniper 的 MCP Server 当前状态进行了复核。结论是：项目已经具备本地 MCP 服务骨架、用户画像读取、Joblens 集成产物和智联任务配置，但 `mcp_server.py` 仍沿用旧版 `L1-L5` 存储路径，与 `docs/CODING_GUIDELINES.md` 中确立的 `storage_layer/positions/{platform}` 自然嵌套结构不一致，导致岗位详情 Resource 和归档工具无法可靠使用。

### 当前问题

#### 1. MCP 暴露层与存储规范不一致
- `VAULT_PATH` 仍指向 `storage_layer/zhilian_intelligence_vault`，实际数据位于 `storage_layer/positions/zhilian_intelligence_vault`。
- `get_l5_detail()` 仍按 `L5` / `L5_Details` 目录检索岗位详情，已不符合当前树形聚合结构。
- README、编码规范和代码中的 Resource URI 设计存在偏差，需要统一。

#### 2. 归档逻辑仍使用旧层级
- `archive_joblens_outputs()` 的目标路径仍生成 `L1` / `L4` / `L5`。
- 新规范要求按平台、行业、职能、职业逐层入库，并使用 `_行业索引表_`、`_职能索引表_`、`_职业索引表_`、`_岗位索引表_` 命名规则。

#### 3. MCP 可运行性缺少自动化验证
- Python 语法检查和直接函数导入可用。
- 但 stdio MCP 客户端端到端握手未形成稳定 smoke test，需要补充最小化验证脚本或测试说明，覆盖 `initialize`、`list_tools`、`list_resources`、`read_resource`、`call_tool`。

#### 4. 环境与依赖不可复现
- 仓库缺少 `requirements.txt` 或 `pyproject.toml`。
- 当前 `venv/bin/pip` shebang 指向旧路径，说明虚拟环境曾被迁移，不适合作为长期交付依据。

### 执行计划

#### Phase 1: 对齐路径与 Resource 语义
- 将平台 Vault 根目录统一为 `storage_layer/positions/{platform}_intelligence_vault`。
- 保留 `jobsniper://persona` Resource。
- 新增或替换岗位读取 Resource，使其支持自然嵌套路径，例如：
  - `jobsniper://vault/positions/{platform}/{path_to_job}`
  - 或提供搜索式工具 `find_job_detail(platform, keyword, company=None)` 以降低 URI 编码复杂度。
- 为旧 `jobsniper://vault/L5/{job_id}` 提供兼容层或明确废弃说明。

#### Phase 2: 重写归档目标路径
- 让 `archive_joblens_outputs()` 根据 `zhilian_master_tasks.json` 中的 `industry`、`domain` 和 `keyword` 生成新结构路径。
- 将岗位索引写入职业目录，将岗位详情写入职业目录叶子层。
- 保留 `dry_run` 作为默认验证入口，避免误移动下载目录文件。
- 对文件名进行平台非法字符清洗，确保 Windows / WSL 路径兼容。

#### Phase 3: 补齐 MCP smoke test
- 新增最小验证脚本或文档化命令，验证 MCP Server 可被 stdio 客户端初始化。
- 验证工具列表、资源列表、画像读取、岗位详情读取、归档 dry-run。
- 将 smoke test 结果作为后续修改的回归基线。

#### Phase 4: 补齐依赖与运行说明
- 新增 `requirements.txt` 或 `pyproject.toml`，锁定 MCP Server 的 Python 依赖。
- 更新 README 中的运行方式、资源 URI、工具说明和存储结构说明。
- 明确 WSL + Windows Chrome + Joblens 的环境前置条件。

### 验收标准
- `venv/bin/python -m py_compile mcp_server.py` 通过。
- MCP 客户端能完成 `initialize`，并能列出全部 tools/resources。
- `jobsniper://persona` 能读取当前用户画像。
- 至少一个已存在岗位详情能通过新 Resource 或搜索工具读取。
- `archive_joblens_outputs(keyword="AI产品经理", dry_run=true)` 输出的新目标路径符合 `docs/CODING_GUIDELINES.md`。
- README 与代码、编码规范三者对 MCP Resource、Tool、存储路径的描述一致。

### 风险与约束
- `launch_zhilian_collection()` 依赖本机 Windows Chrome、WSL 路径和 Joblens 扩展产物，短期内仍属于本地自动化能力，不宜承诺跨平台可用。
- 归档工具会移动 `D:\Downloads` 中的真实文件，修复时必须优先使用 `dry_run` 验证。
- 旧 `L1-L5` 结构已被清理，任何新代码不得重新写入旧目录。

### 署名
**Codex**
*Timestamp: 2026-05-04 00:00 (Asia/Shanghai)*

---

## [2026-05-03] - 存储结构重构与规范确立 (Gemini 3)

### 📝 会话纪要
本会话主要完成了项目数据存储层 (`storage_layer`) 的物理结构重构以及配套编码规范的制定，解决了原结构存在的冗余度高、维护困难及文件检索不便等痛点。

### 🚀 主要变更

#### 1. 规范文档更新 (`docs/CODING_GUIDELINES.md`)
- **存储模式变革**：由原先的 `L1-L5` 扁平层级结构全面切换为**自然嵌套（树形聚合）**结构。
- **命名规范确立**：制定了严格的索引表命名规则，并引入下划线 `_` 前缀，确保索引表在文件系统中置顶显示。
    - `_行业索引表_[平台名称].md`
    - `_职能索引表_[行业名称].md`
    - `_职业索引表_[职能名称].md`
    - `_岗位索引表_[职业名称].md`

#### 2. 存储层物理重构 (`storage_layer/`)
- **路径聚合**：创建 `positions/` 目录，将所有平台（BOSS、智联）的 Vault 统一收纳。
- **结构迁移**：将 `zhilian_intelligence_vault` 下的所有数据从 `L1-L5` 文件夹迁移至基于行业/职能/职业的嵌套目录。
- **批量重命名**：对所有的索引表文件执行了批量重命名，统一添加了 `_` 前缀。
- **清理**：删除了所有原有的空层级文件夹 (`L1`~`L5`)。

### 📌 关键决策
- **为何选择自然嵌套？** 减少重命名行业/职能时的联动成本，路径更符合人类逻辑。
- **为何使用下划线前缀？** 在 VS Code 等编辑器中强制索引文件置顶，解决索引表淹没在大量岗位详情文件中的问题。

### 👤 署名
** Gemini CLI Agent **
*Timestamp: 2026-05-03 03:00 (UTC/Local)*

---
