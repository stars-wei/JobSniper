# JobSniper PRD

## 1. 产品概述

JobSniper 是一个面向本地求职情报工作的 MCP Server。它让 Codex、Claude Desktop 等 AI Client 可以通过统一 MCP 接口读取岗位知识库、启动招聘平台采集、归档采集产物、维护用户画像，并为后续简历、推荐和面试准备工作流提供本地数据基础。

当前版本重点支持智联招聘（Zhilian）情报链路：job menu 发现、职业关键词岗位列表采集、单岗位详情采集、Downloads 产物归档、岗位详情检索和用户画像更新。

## 2. 目标用户

- **求职者 / 操作者**：维护自己的岗位知识库、用户画像、简历和会话产物。
- **AI Agent**：通过 MCP 工具读取资料、启动采集、检索岗位、归档产物和更新画像。
- **后续求职工作流**：基于本地岗位库和用户画像生成岗位推荐、简历改写、面试准备和决策分析。

## 3. 当前 MVP 范围

### 已包含

- FastMCP stdio 服务入口。
- MCP Resource：读取当前用户画像。
- MCP Resource：按平台和自然嵌套路径读取岗位详情 Markdown。
- MCP Tool：按文件名搜索岗位详情。
- MCP Tool：启动智联 job menu、job list、job detail 三类采集。
- MCP Tool：归档 Joblens 下载产物到 `storage_layer/positions`。
- MCP Tool：更新用户画像技能置信度。
- Chrome 扩展 Joblens：负责浏览器内页面访问、队列消费和数据导出。
- 仓库内监视脚本：根据 results JSONL 判断完成、失败、重试和归档。

### 暂不包含

- BOSS 直聘完整采集闭环。
- 多平台统一采集抽象。
- 完整推荐报告、简历生成和面试准备流水线。
- 跨平台浏览器/下载目录自动配置。
- 远程托管、多用户账号体系或云端数据库。

## 4. 产品结构

JobSniper 当前采用本地三层目录结构：

```text
scraping_layer/   # 浏览器采集、Joblens 扩展、队列监视和归档辅助脚本
storage_layer/    # 用户画像、岗位知识库、平台岗位库
session_layer/    # 简历、会议记录、报告等会话产物
```

核心运行链路：

```text
AI Client -> MCP Server -> scraping_layer/Joblens -> Downloads 队列与产物
          -> monitor scripts -> storage_layer/positions
```

`scraping_layer/joblens/docs/PRD.md` 是 Joblens 扩展子项目 PRD；本文档是 JobSniper 项目级 PRD。

## 5. 当前限制

- 当前采集依赖本机 Chrome 或 Chromium 系浏览器。
- 当前 Joblens 扩展依赖浏览器登录态访问招聘平台。
- 当前队列和下载产物依赖本机 Downloads 目录。
- WSL 与 Windows 文件系统之间的 `/mnt/*` 挂载权限可能影响移动归档。
- 智联安全验证/验证码需要人工处理，不自动绕过。
- `DOWNLOADS_PATH` 和 `WINDOWS_CHROME_PATH` 仍是待配置化的本地环境参数。

## 6. 后续需求：本地环境配置化

为支持其他用户从 GitHub 下载并部署 JobSniper，后续必须移除本机硬编码路径依赖。

### Downloads 路径

当前代码仍存在类似配置：

```python
DOWNLOADS_PATH = "/mnt/d/Downloads"
```

后续需求：

- 支持通过环境变量配置，例如 `JOBSNIPER_DOWNLOADS_PATH`。
- 支持本地配置文件，例如 `.env` 或 `jobsniper.local.json`。
- 支持常见默认目录自动探测，例如 WSL 下的 Windows Downloads 或 Linux/macOS 用户 Downloads。
- MCP Server、监视脚本、归档脚本、Joblens 队列路径应保持一致。

### Chrome 路径

当前代码仍存在类似配置：

```python
WINDOWS_CHROME_PATH = "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
```

后续需求：

- 支持通过环境变量配置，例如 `JOBSNIPER_CHROME_PATH`。
- 支持自动探测常见浏览器路径，包括 Windows Chrome、Windows Edge、Linux Chrome/Chromium、macOS Chrome。
- 启动失败时返回清晰错误，提示用户如何配置浏览器路径。
- 不要求用户修改源码即可完成本地部署。

### 成功标准

- 用户 clone 项目后，只需安装 Python/Node 依赖、加载 Joblens 扩展、配置 MCP Client，即可运行基础采集和归档流程。
- 对于无法自动探测的环境，用户只需要编辑本地配置文件或设置环境变量。
- README 提供最小部署路径和常见环境配置示例。

## 7. 成功标准

- MCP Client 能完成 `initialize`、`list_tools` 和 `list_resources`。
- 智联 job menu、job list、job detail 采集入口可用。
- 队列结果写入后，监视脚本能自动触发归档。
- 岗位详情可在 `storage_layer/positions` 中按自然嵌套结构保存和检索。
- 用户画像可被读取和更新。
- 本地路径配置化完成后，新用户无需修改源码即可部署运行。

## 8. 风险

- 招聘平台页面结构变化会影响采集稳定性。
- 招聘平台安全验证会中断自动化流程。
- 浏览器扩展、MCP Server、监视脚本运行在不同上下文，路径配置必须保持一致。
- Windows/WSL、Linux、macOS 的路径和权限模型不同，配置化方案需要分阶段验证。
