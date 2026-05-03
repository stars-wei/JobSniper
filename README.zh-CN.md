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
- 用于按岗位 ID 读取 L5 岗位详情 Markdown 的 MCP Resource
- 用于触发采集任务的 MCP Tool 占位实现
- 通过内置 Joblens Chrome 扩展启动智联采集的 MCP Tool
- 将 `D:\Downloads` 中 Joblens 输出归档入知识库的 MCP Tool
- 用于更新用户画像技能置信度的 MCP Tool

尚未实现：

- `collection_layer` 下的真实采集脚本
- `session_layer` 下的会话编排
- L1 到 L5 知识库内容填充
- 完整的求职建议或招聘咨询工作流

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

当前 `trigger_clipper` MCP 工具仍是单页采集占位实现。智联列表和详情采集由 `launch_zhilian_collection` 与 `archive_joblens_outputs` 负责。

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
- **平台层**：包含 `_平台索引表_[平台名称].md` 和行业文件夹。
- **行业层**：包含 `_职能索引表_[行业名称].md` 和职能文件夹。
- **职能层**：包含 `_职业索引表_[职能名称].md` 和职业文件夹。
- **职业层**：包含 `_岗位索引表_[职业名称].md` 和具体的岗位详情文件。

岗位详情文件遵循命名规范：`{公司名称}_{岗位名称}.md`。

## MCP Resources

### `jobsniper://persona`

返回当前求职者画像 JSON。

如果 `current_user.json` 不存在，服务会返回一个默认的空画像骨架。

### `jobsniper://vault/positions/{platform}/{path_to_job}`

从嵌套存储层读取一个岗位详情 Markdown 文件。

## MCP Tools

### `trigger_clipper(url: str, job_title: str)`

当前行为：

- 返回一条模拟的采集任务启动消息

预期行为：

- 触发 Joblens 或某个平台专用采集器
- 采集岗位详情页
- 将结果保存到存储层

### `launch_zhilian_collection(keyword: str, city_id: str = "538", pages: str = "auto", test: bool = false, detail_test: bool = false, detail_limit: int = 5, debug: bool = true)`

启动 Windows Chrome，加载 JobSniper 内置的 Joblens 扩展，并打开智联采集 URL。

生成的 URL 包含：

- `clipper_auto=1`
- `jl={city_id}`
- `clipper_pages={pages}`
- `clipper_keyword_b64u={base64url(keyword)}`
- 可选的 `clipper_test=1`、`clipper_detail_test=1` 和 `clipper_debug=1`

工具会返回采集 URL、Chrome 启动命令、预期下载目录和建议归档调用。

### `archive_joblens_outputs(keyword: str, since_minutes: int = 60, dry_run: bool = false, include_test: bool = false)`

通过 `/mnt/d/Downloads` 扫描 `D:\Downloads` 中最近生成的 `ZHILIAN_*` 文件，并将匹配输出移动到 JobSniper 存储层（`storage_layer/positions/zhilian_intelligence_vault/`）。

工具会根据主任务列表中的行业和职能映射关系，解析出嵌套的入库路径。

入库路径约定（内部）：
- `ZHILIAN_KEYWORDS_*.md` -> 平台 Vault 根目录，作为平台索引表（`_平台索引表_[平台名称].md`）。
- `ZHILIAN_<keyword>_*.md` -> 职业文件夹下，作为岗位索引表（`_岗位索引表_[职业名称].md`）。
- `ZHILIAN_RAW_<keyword>_*.json/html` -> 职业文件夹下的 `raw/` 子目录。
- `ZHILIAN_DETAIL_*_<keyword>_*.md` -> 树形结构的最终叶子节点（`{公司名称}_{岗位名称}.md`）。

标准操作流程：

1. 启动采集：

```text
launch_zhilian_collection(keyword="AI产品经理", test=true, debug=true)
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

## 与 Joblens 的关系

Joblens 是浏览器扩展，负责从招聘平台采集招聘情报。

JobSniper 是更高一层的本地服务原型。它的预期职责是：

- 读取 Joblens 的采集输出
- 将招聘情报整理进分层知识库
- 维护求职者画像
- 通过 MCP 向 Agent 暴露画像和岗位情报
- 支持后续求职建议工作流

在本集成中，`/home/xstars/programs/joblens` 保持为上游来源，不做修改。JobSniper 使用 `integrations/joblens` 下的独立副本。

## 下一步

- 定义 L5 岗位详情文档的稳定命名规则。
- 为 `L1`、`L2`、`L3`、`L4`、`L5` 填充真实样例。
- 将通用 `trigger_clipper` 从占位实现替换为真实单详情采集命令。
- 为画像分数范围和必填字段增加基础校验。
