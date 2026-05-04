# JobSniper 中文说明

JobSniper 是一个本地 MCP 服务原型，用于承载求职情报、岗位知识库和求职者画像。

它位于智联情报采集沙盒旁边，目标是把已采集的招聘数据、用户画像数据，以及后续的采集指令，通过 MCP Resources 和 MCP Tools 暴露给 Agent 使用。

## 当前状态

当前项目还是一个轻量骨架，不是完整产品。

已实现：

- MCP 服务入口：`mcp_server.py`
- 当前用户画像存储：`storage_layer/personas/current_user.json`
- 分层招聘情报知识库目录结构
- 内置 Joblens 集成副本：`integrations/joblens`
- 用于读取当前用户画像的 MCP Resource
- 用于按自然嵌套路径读取岗位详情 Markdown 的 MCP Resource
- 用于搜索岗位详情文件的 MCP Tool
- 用于触发采集任务的 MCP Tool 占位实现
- 通过内置 Joblens Chrome 扩展启动智联采集的 MCP Tool
- 将 `D:\Downloads` 中 Joblens 输出归档入知识库的 MCP Tool
- 用于更新用户画像技能置信度的 MCP Tool

尚未实现：

- `collection_layer` 下的真实采集脚本
- `session_layer` 下的会话编排
- 完整的求职建议或招聘咨询工作流
- 稳定的协议级 stdio MCP smoke test；当前默认 smoke test 覆盖函数级行为

## 目录结构

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

预留给采集命令和平台适配器。

智联采集入口按 job menu、job list 和 job detail 三类工具拆分，归档由 `archive_joblens_outputs` 负责。

### `integrations/joblens`

JobSniper 内置的轻量 Joblens 副本。

上游源码 `/home/xstars/programs/joblens` 在本集成中视为只读，不直接修改。JobSniper 从下面路径加载 Chrome 扩展产物：

```text
integrations/joblens/dist
```

该副本排除了 `node_modules`，保留源码、docs、scripts、`dist`、`builds` 和配置文件。

### `session_layer`

预留给用户交互会话、审计轨迹和求职建议工作流。

### `storage_layer/personas`

用于存储求职者画像数据。

当前画像文件是：

```text
storage_layer/personas/current_user.json
```

它包含：

- 求职者姓名
- 目标岗位
- 技能置信度分数
- 分数调整的审计说明

### `storage_layer/positions`（原 `knowledge_vault`）

用于存储按平台和**自然嵌套（树形聚合）**结构组织的招聘情报。

每个平台文件夹（如 `zhilian_intelligence_vault`）遵循以下层级：
- **平台层**：包含 `_行业索引表_智联招聘.md` 和行业文件夹。
- **行业层**：包含 `_职能索引表_[行业名称].md` 和职能文件夹。
- **职能层**：包含 `_职业索引表_[职能名称].md` 和职业文件夹。
- **职业层**：包含 `_岗位索引表_[职业名称].md` 和具体的岗位详情文件。

岗位详情文件遵循命名规范：`[公司名称]_[岗位名称].md`。

## MCP Resources

### `jobsniper://persona`

返回当前求职者画像 JSON。

如果 `current_user.json` 不存在，服务会返回一个默认的空画像骨架。

### `jobsniper://vault/positions/{platform}/{path_to_job}`

从嵌套存储层读取一个岗位详情 Markdown 文件。

示例：

```text
jobsniper://vault/positions/zhilian/产品/互联网产品经理/AI产品经理/上海倍通医药科技咨询有限公司_AI产品经理.md
```

## MCP Tools

### `find_job_detail(platform: str, keyword: str, company: str | None = null, limit: int = 5)`

按文件名搜索岗位详情 Markdown。

参数：

- `platform`: `zhilian` 或 `boss`
- `keyword`: 岗位名或文件名关键词
- `company`: 可选公司名关键词
- `limit`: 最多返回的匹配数量

返回内容包含匹配文件的绝对路径、相对路径和可读取的 Resource URI。

### 采集接口分型

JobSniper 的采集能力按数据层级拆成三种：

- **job menu**：平台岗位菜单，通常是行业-职能-职业三级结构。
- **job list**：某个职业关键词下的岗位列表。
- **job detail**：某个具体岗位的招聘详情页。

### `launch_zhilian_job_menu_collection(city_id: str = "538", debug: bool = true)`

采集智联平台 job menu，用于提取行业-职能-职业三级结构和关键词池。

该工具打开：

```text
https://www.zhaopin.com/?jl={city_id}&clipper_keyword_discovery=1&clipper_debug=1
```

产物为：

```text
zhilian_keyword_discovery_{timestamp}.md
```

### `launch_zhilian_job_list_collection(keyword: str, city_id: str = "538", pages: str = "auto", test: bool = false, debug: bool = true)`

采集智联某个职业关键词下的岗位列表。工具会启动 Windows Chrome，加载 JobSniper 内置的 Joblens 扩展，并打开智联搜索 URL。

生成的 URL 包含：

- `clipper_auto=1`
- `jl={city_id}`
- `clipper_pages={pages}`
- `clipper_keyword_b64u={base64url(keyword)}`
- 可选的 `clipper_test=1` 和 `clipper_debug=1`

工具会返回采集 URL、Chrome 启动命令、预期下载目录和建议归档调用。

### `launch_zhilian_job_detail_collection(job_url: str, keyword: str = "", debug: bool = true)`

采集智联单个岗位详情页。该工具会打开指定岗位 URL，并追加：

- `clipper_job_detail=1`
- 可选的 `clipper_keyword={keyword}`
- 可选的 `clipper_debug=1`

产物包括单岗位详情 Markdown、详情 Raw HTML 和详情 manifest。归档时 Markdown 会落为岗位详情叶子文件：

```text
{公司名称}_{岗位名称}.md
```

### 概念区分

JobSniper 里这两类内容是分开的：

- **关键词发现产物**：`zhilian_keyword_discovery_{timestamp}.md`
  - 来源于智联“关键词发现”页。
  - 作用是记录平台级岗位分类、关键词池和发现时间。
  - 存放在 `storage_layer/positions/` 根目录。
- **平台索引表**：`_行业索引表_智联招聘.md`
  - 位于 `storage_layer/positions/zhilian_intelligence_vault/`。
  - 作用是作为平台内部分层导航入口，连接行业、职能、职业和岗位详情。
  - 它不是关键词发现工具的直接产物。

简单说：

- 发现产物回答“智联上能发现哪些关键词和分组”。
- 平台索引表回答“这些关键词和分组如何挂到仓库树里”。

### `archive_joblens_outputs(keyword: str, since_minutes: int = 60, dry_run: bool = false, include_test: bool = false)`

通过 `/mnt/d/Downloads` 扫描 `D:\Downloads` 中最近生成的 `ZHILIAN_*` 文件，并将匹配输出移动到 JobSniper 存储层（`storage_layer/positions/zhilian_intelligence_vault/`）。

工具会根据主任务列表中的行业和职能映射关系，解析出嵌套的入库路径。

入库路径约定（内部）：
- `zhilian_keyword_discovery_*.md` -> `storage_layer/positions/` 根目录，作为平台级关键词发现产物。
- `_行业索引表_智联招聘.md` -> `storage_layer/positions/zhilian_intelligence_vault/` 根目录，作为平台索引表。
- `ZHILIAN_<keyword>_*.md` -> 职业文件夹下，作为岗位索引表（`_岗位索引表_[职业名称].md`）。
- `ZHILIAN_RAW_<keyword>_*.json/html` -> 职业文件夹下的 `raw/` 子目录。
- `ZHILIAN_DETAIL_{公司名称}_{岗位名称}_{timestamp}.md` -> 树形结构的最终叶子节点（`{公司名称}_{岗位名称}.md`）。
- `ZHILIAN_DETAIL_RAW_*` 和 `ZHILIAN_DETAIL_MANIFEST_*` -> 职业文件夹下的 `raw/` 子目录。

标准操作流程：

1. 启动采集：

```text
launch_zhilian_job_list_collection(keyword="AI产品经理", test=true, debug=true)
```

2. 等待 Joblens 完成下载写入。

3. 预览归档移动计划：

```text
archive_joblens_outputs(keyword="AI产品经理", dry_run=true)
```

4. 执行归档：

```text
archive_joblens_outputs(keyword="AI产品经理", dry_run=false)
```

### `update_persona(skill_name: str, confidence_score: int, reasoning: str)`

更新当前画像中的技能置信度。

写入 `current_user.json` 的字段示例：

```json
{
  "skills": {
    "RAG/AI Engineering": {
      "score": 30,
      "last_audit_reason": "完成了一个可运行的 RAG Demo 项目。"
    }
  }
}
```

## 运行方式

安装依赖：

```bash
cd /home/xstars/programs/JobSniper
python -m pip install -r requirements.txt
```

在项目目录下执行：

```bash
cd /home/xstars/programs/JobSniper
source venv/bin/activate
python mcp_server.py
```

服务名称为：

```text
FastMCP("JobSniper")
```

## 验证方式

默认 smoke test 覆盖 Python 导入、画像读取、岗位详情读取、岗位搜索和归档 dry-run：

```bash
cd /home/xstars/programs/JobSniper
venv/bin/python scripts/smoke_mcp_server.py
```

协议级 stdio smoke test 入口：

```bash
venv/bin/python scripts/smoke_mcp_server.py --stdio --timeout 8
```

当前环境下该协议级测试已通过，可验证 `initialize`、`list_tools` 和 `list_resources`。

## 与 Joblens 的关系

Joblens 是浏览器扩展，负责从招聘平台采集招聘情报。

JobSniper 是更高一层的本地服务原型。它的预期职责是：

- 读取 Joblens 的采集输出
- 将招聘情报整理进分层知识库
- 维护求职者画像
- 通过 MCP 向 Agent 暴露画像和岗位情报
- 支持后续求职建议工作流

在本集成中，`/home/xstars/programs/joblens` 保持为上游来源，不做修改。JobSniper 使用 `integrations/joblens` 下的独立副本。
