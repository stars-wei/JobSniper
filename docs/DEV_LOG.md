# JobSniper 项目开发日志

## 记录规则
*   日志按时间倒序排列，最新记录在上。
*   新记录插入到“日志时间线”下方、现有最新记录上方。
*   每条记录必须包含时间戳、执行人或署名。
*   不删除其他人的原始记录；如需修正，通过新增记录说明。
*   开发日志记录人工/Agent 的开发过程。

---

## 日志时间线

## [2026-05-07] - 列表页采集接入队列与自动归档 (Codex)

### 会话纪要
岗位列表页（job list）原逻辑依赖 MCP 打开浏览器前台并由 content script 在当前标签页执行采集，采集产物下载后需要手工调用归档工具。为与岗位详情页（job detail）保持一致，本次将 job list 采集改为“入队 → 扩展后台处理 → 监视脚本完成判定 → 自动归档”的流水线。

### 主要变更
- Joblens 扩展新增 job list 队列：
  - 任务文件：`D:\\Downloads\\zhilian_list_tasks.jsonl`
  - 结果文件：`D:\\Downloads\\zhilian_list_results.jsonl`
  - background 警报轮询：`listQueuePoll`（与 detail 同为 5s 周期）
- content script 在 `clipper_list_queue=1` 时：
  - 采集完成后发送 `zhilianListHarvestDone` 到 background
  - 自动关闭标签页（不再提示“请手动关闭”）
- 新增通用队列解析脚本：`programs/JobSniper/scripts/parse_queue_results.py`
- 新增 job list 监视脚本：`/home/xstars/.local/bin/watch_job_list.sh`，完成判定后调用 `archive_outputs.py` 自动归档
- MCP `launch_zhilian_job_list_collection()` 改为写入队列并启动监视脚本；新增可选 `wake_browser`，用于打开 `clipper_list_queue_wake=1` 唤醒页触发一次队列执行

### 验证
- `npm run build:chrome`：通过。
- `bash -n /home/xstars/.local/bin/watch_job_list.sh`：通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mcp_server.py scripts/parse_queue_results.py`：通过。

### 署名
**Codex**
*Timestamp: 2026-05-07 19:20 (Asia/Shanghai)*

---

## [2026-05-07] - 收敛详情监视脚本完成判定入口 (Codex)

### 会话纪要
讨论详情采集监视脚本时确认，`completed = done + failed` 引入后，`completed >= total` 应作为唯一完成判定入口。原脚本仍保留 `done >= total` 分支，虽然业务上无副作用，但会造成两个完成入口并降低状态机可读性。

### 主要变更
- 删除 `watch_downloads.sh` 中冗余的 `done >= total` 归档分支。
- 将全部成功路径显式归入 `completed >= total` 分支的 `failed == 0` 分支。
- 保留失败重试、部分成功归档、全部失败通知三类结果处理逻辑。

### 验证
- `bash -n /home/xstars/.local/bin/watch_downloads.sh`：通过。

### 署名
**Codex**
*Timestamp: 2026-05-07 01:02 (Asia/Shanghai)*

---

## [2026-05-07] - 分离归档 JSON 与 stderr 输出 (Codex)

### 会话纪要
检查监视脚本归档阶段时发现，`archive_outputs.py` 的 stdout 与 stderr 被 `2>&1` 合并写入 `archive_result.json`。如果归档脚本产生 warning、traceback 或其他 stderr 内容，后续 `json.load()` 会读取到被污染的 JSON 文件。

### 主要变更
- `watch_downloads.sh` 新增 `ARCHIVE_JSON` 与 `ARCHIVE_ERR`。
- 归档 stdout 单独写入 `archive_result.json`。
- 归档 stderr 单独写入 `archive_result.err`，并逐行写入监视日志 `ARCHIVE_ERR`。
- 记录归档命令非零退出码。
- `json.load()` 解析错误单独写入 `archive_parse.err`，并记录为 `ARCHIVE_PARSE_ERR`。

### 验证
- `bash -n /home/xstars/.local/bin/watch_downloads.sh`：通过。
- `git diff --check`：通过。

### 署名
**Codex**
*Timestamp: 2026-05-07 00:55 (Asia/Shanghai)*

---

## [2026-05-07] - 补齐详情监视脚本 failed 策略 (Codex)

### 会话纪要
验证码/安全验证页现在会写入 `status=failed`。原监视脚本主要以 `done==total` 作为完成条件，存在 failed 任务时可能卡住。因此补齐 failed 批次的重试、归档和通知策略。

### 主要变更
- `watch_downloads.sh` 使用 `done + failed` 判断任务是否已有结果。
- 有 failed 且未达到 `MAX_TASK_RETRIES` 时，自动将失败任务追加回队列重试。
- 重试后仍有 failed：
  - 如果存在 done 结果，则归档已成功下载的详情，并进入通知。
  - 如果全部 failed，则不归档，直接进入通知。
- 通知文案改为显示 `done/failed/total`。
- `parse_results.py` 改为按 `job_id` 或标准化 URL 归并任务和结果，避免重试追加队列行导致 total 虚增。

### 验证
- `bash -n /home/xstars/.local/bin/watch_downloads.sh`：通过。
- `python3 -m py_compile /tmp/watch_downloads/parse_results.py`：通过。
- 模拟同一岗位先 `failed` 后 `done`：解析结果为 `total=1 done=1 failed=0`。
- `git diff --check`：通过。

### 署名
**Codex**
*Timestamp: 2026-05-07 00:50 (Asia/Shanghai)*

---

## [2026-05-07] - 修复验证码路径误写 done 风险 (Codex)

### 会话纪要
检查详情队列验证码路径时发现风险：`captchaDetected` 会调用 `resolveCaptcha()` 立即 resolve，但 `processSingleDetailUrl()` 只按 timeout 判断失败。验证码路径因此可能返回 `success=true`，导致 `zhilian_detail_results.jsonl` 写入 `done`，即使详情 Markdown 并不存在。

### 主要变更
- 将 `captchaResolvers` 从无参 resolver 改为携带 `DetailProcessResult`。
- `captchaDetected` 触发时返回 `{ success: false, reason: "captcha detected" }`。
- `processSingleDetailUrl()` 优先返回 resolver 携带的结果，不再把验证码 resolve 误判为成功。
- 队列结果因此会写入 `status="failed"`，并记录 `error="captcha detected"`。

### 验证
- `npm run build:chrome`：通过，已更新 `dist/background.js` 和 Chrome zip 构建产物。
- `rg "DetailProcessResult|captcha detected|resolvedResult"`：确认源码和构建产物包含失败结果路径。
- `git diff --check`：通过。

### 后续事项
- 监视脚本仍需明确 failed 批次策略：失败重试后仍失败时，应进入通知而不是等待 `done==total`。

### 署名
**Codex**
*Timestamp: 2026-05-07 00:40 (Asia/Shanghai)*

---

## [2026-05-07] - 检测智联 EdgeOne 安全验证页 (Codex)

### 会话纪要
详情采集默认纯队列模式测试中，`CC159297110J40882172201` 被智联/Tencent Cloud EdgeOne 安全验证页拦截。扩展将验证页通过 DOM fallback 误判为 `success`，生成并归档了 `未知公司_www.zhaopin.com.md`。

### 主要变更
- 在 `parseZhilianDetailPage()` 开头前置调用 `isCaptchaPage()`。
- 命中验证页时直接返回 `status="failed"` 和 `error="security verification page detected"`。
- 扩充 `isCaptchaPage()` 检测特征：
  - `正在验证连接安全性`
  - `请勾选下方复选框`
  - `验证完成后.*重定向`
  - `Tencent Cloud EdgeOne`
  - `Protected by Tencent Cloud EdgeOne`

### 验证
- `npm run build:chrome`：通过，已更新 `dist/content.js` 和 Chrome zip 构建产物。
- `rg "security verification page detected|Tencent Cloud EdgeOne|正在验证连接安全性"`：确认源码和构建产物包含安全验证检测。
- `git diff --check`：通过。

### 后续事项
- 需要重载 Chrome 扩展后复测安全验证页。
- 当前监视脚本主要按 `done==total` 触发归档；如果安全验证任务写入 `failed`，还需要明确 failed 批次的通知/重试策略，避免卡住。

### 署名
**Codex**
*Timestamp: 2026-05-07 00:30 (Asia/Shanghai)*

---

## [2026-05-07] - 详情采集默认改为纯队列后台模式 (Codex)

### 会话纪要
批量采集回归后发现两个体验问题：MCP 详情采集入口每次打开 `clipper_detail_queue=1` 唤醒页会导致 Chrome 切到前台；同时每次采集都先打开智联首页，而扩展后台本身已经能通过 alarm 轮询 `zhilian_detail_tasks.jsonl` 并访问正确详情 URL。

### 主要变更
- `launch_zhilian_job_detail_collection()` 默认只写入 `zhilian_detail_tasks.jsonl`，不再打开智联首页或唤醒页。
- 新增可选参数 `wake_browser: bool = False`。
- 只有显式传入 `wake_browser=True` 时，才打开 `https://www.zhaopin.com/?clipper_detail_queue=1` 作为人工/应急唤醒入口。
- 返回值保留 `wake_url`、`chrome_launched`、`wake_debounced`，默认分别为 `null`、`false`、`false`。

### 验证
- 本地 smoke test：默认调用 `Popen` 次数为 0。
- 本地 smoke test：显式 `wake_browser=True` 时 `Popen` 次数增加为 1。
- `bash -n /home/xstars/.local/bin/watch_downloads.sh`：通过。

### 结论
详情采集默认回归“后台模式”：MCP 只负责入队，Chrome 扩展后台轮询队列并采集详情页。这样避免浏览器切前台，也避免每个任务先打开智联首页。

### 署名
**Codex**
*Timestamp: 2026-05-07 00:20 (Asia/Shanghai)*

---

## [2026-05-07] - 修复详情批量队列竞态与监视状态机 (Codex)

### 会话纪要
针对 5 条详情批量采集测试暴露的问题，本次修复两个批量闭环缺口：连续唤醒导致首条任务重复采集，以及监视脚本停留在旧 `notifying` 阶段时无法处理新批次。

### 主要变更

#### 1. 扩展侧 in-flight 锁
- `background.ts` 新增 `jobsniper_detail_inflight_locks_v1` 与 `jobsniper_detail_done_locks_v1`。
- 队列执行前按 `job_id` 或标准化 URL 生成锁键。
- 同一扩展后台实例内先用内存 `detailRuntimeClaims` 同步占位，再写入 `chrome.storage.local`。
- 任务开始前写入 in-flight 锁，成功后写入 done 锁，失败后释放 in-flight 锁。
- in-flight 锁设置 10 分钟 TTL，避免异常中断后永久阻塞任务。

#### 2. MCP 唤醒去抖
- `launch_zhilian_job_detail_collection()` 增加 10 秒唤醒去抖。
- 连续批量入队时只让第一条任务打开 `clipper_detail_queue=1` 唤醒页，后续短时间调用只入队并返回 `wake_debounced=true`。

#### 3. 监视脚本新批次识别
- `watch_downloads.sh` 为 `zhilian_detail_tasks.jsonl` 计算 `cksum` 签名。
- 检测到任务文件签名变化且 `total>0` 时，重置 `phase`、`done_prev`、`retry_count` 和 `notify_attempt`。
- 解决旧 `notifying` 状态下新任务完成后无法进入归档阶段的问题。

### 验证
- `compile(mcp_server.py)`：通过。
- `bash -n /home/xstars/.local/bin/watch_downloads.sh`：通过。
- `npm run build:chrome`：通过，已更新 Chrome 扩展构建产物。
- `rg "jobsniper_detail_done_locks_v1|jobsniper_detail_inflight_locks_v1|wake_debounced|NEW BATCH"`：确认源码/构建产物包含新逻辑。
- `git diff --check`：通过。

### 后续验证
- 已在重启 JobSniper MCP Server 并刷新 Chrome 扩展后执行 5 条批量回归。
- 任务文件签名变化被正确识别，监视脚本多次记录 `NEW BATCH` 并重置状态。
- 采集结果为 `done=5/5`，归档日志显示 `ARCHIVE: moved=5 → notifying`，通知确认后清理任务/结果文件。
- 5 个岗位详情已归档到“人工智能讲师”职业目录。
- MCP 唤醒去抖在批量调用中部分生效；实际防重复主要由扩展侧 runtime/in-flight/done 锁完成，未再出现重复详情文件。

### 署名
**Codex**
*Timestamp: 2026-05-07 00:05 (Asia/Shanghai)*

---

## [2026-05-06] - 详情队列五条批量采集测试 (Codex)

### 会话纪要
按系统业务流测试 5 条“人工智能讲师”岗位详情批量采集。MCP 详情入口连续入队 5 条任务，Chrome 扩展后台成功消费队列并写入 `zhilian_detail_results.jsonl`，但批量场景暴露出重复采集竞态和监视脚本状态未重置问题。

### 测试对象
- 毕马科技 - AI工程师（含后端）
- 上海自仪院智能化系统有限公司 - 研发工程师
- 新东方教育科技集团有限公司 - 上海-智慧空间逻辑思维教师(J55835)
- 沈阳为来教育科技有限公司 - 管培生（讲师方向）
- 方家铺子 - AI工程师 - 龙虾训练 & AI应用【base莆田】

### 测试结果
- `zhilian_detail_tasks.jsonl`：5 行。
- `zhilian_detail_results.jsonl`：6 行。
- 5 个目标岗位均出现 `status=done`。
- 未再生成 `zhilian_detail_results.txt`。
- Downloads 中生成 6 个详情 Markdown，其中“毕马科技”重复生成 2 次。

### 问题记录

#### 1. 批量唤醒存在并发竞态
- 连续 5 次 MCP 调用都会打开 `clipper_detail_queue=1` 唤醒页。
- 第 1 条任务在结果文件落盘前被另一轮队列再次处理，导致 `task_index=0` 出现两条 done 记录。
- 后续修复方向：支持批量入队后只唤醒一次，或在扩展侧增加更强的 in-flight URL/job_id 锁。

#### 2. 监视脚本 stale notifying 状态未重置
- 上一轮单条测试后监视脚本仍处于 `phase=notifying`。
- 新的 5 条任务完成后状态显示 `total=5 done=5 failed=0 phase=notifying`，但未进入新一轮归档。
- 后续修复方向：监视脚本检测到新任务文件或新结果批次时，应从 stale `notifying` 状态重置为 crawling/archiving。

### 结论
MCP 入队、Chrome 唤醒、扩展后台批量采集和 JSONL 结果写入已经可用；批量业务闭环还需修复唤醒并发和监视脚本状态机。

### 署名
**Codex**
*Timestamp: 2026-05-06 23:58 (Asia/Shanghai)*

---

## [2026-05-06] - 修正详情结果 JSONL 下载 MIME (Codex)

### 会话纪要
后台详情队列已能消费 `zhilian_detail_tasks.jsonl`，但 Chrome 实际生成的结果文件为 `zhilian_detail_results.txt`，而监视脚本和源码约定为 `zhilian_detail_results.jsonl`。这会导致监视脚本无法读取完成状态。

### 主要变更
- 保持结果文件名常量为 `zhilian_detail_results.jsonl`。
- 将结果下载的 data URL MIME 从 `text/plain;charset=utf-8` 改为 `application/x-ndjson;charset=utf-8`，与 JSONL/NDJSON 文本行格式匹配，避免 Chrome 将文件落为 `.txt`。

### 验证
- `npm run build:chrome`：通过，已更新 `dist/background.js` 和 Chrome zip 构建产物。
- `rg "application/x-ndjson|zhilian_detail_results\\.jsonl" integrations/joblens/src/background.ts integrations/joblens/dist/background.js`：确认源码和构建产物包含新 MIME 与 `.jsonl` 文件名。
- `git diff --check`：通过。

### 署名
**Codex**
*Timestamp: 2026-05-06 23:48 (Asia/Shanghai)*

---

## [2026-05-06] - 打通详情队列唤醒入口 (Codex)

### 会话纪要
按系统业务流测试详情采集时，MCP 工具能写入 `D:\Downloads\zhilian_detail_tasks.jsonl`，但 Chrome 扩展后台没有消费队列，`zhilian_detail_results.jsonl` 和详情 Markdown 均未生成。检查确认详情采集入口缺少 Chrome 唤醒动作，扩展队列也依赖旧的行号 checkpoint。

### 主要变更

#### 1. MCP 详情入口唤醒 Chrome
- `launch_zhilian_job_detail_collection()` 写入任务后打开 `https://www.zhaopin.com/?clipper_detail_queue=1`。
- 工具响应增加 `wake_url`、`chrome_launched` 和 `chrome_error`，便于 MCP 客户端判断是否完成唤醒动作。

#### 2. 扩展后台显式队列入口
- `background.ts` 新增 `runDetailTaskQueue` runtime message 入口。
- `content.ts` 识别 `clipper_detail_queue=1` 唤醒页，向后台发送队列执行消息。

#### 3. 去除行号 checkpoint 依赖
- 详情队列不再用 `chrome.storage.local.detailCheckpoint` 过滤任务。
- 改为读取 `zhilian_detail_results.jsonl`，按标准化 URL 和 `job_id` 判断已完成任务，避免重写任务文件后被旧行号跳过。

### 验证
- `python3 -m py_compile mcp_server.py`：通过。
- `npm run build:chrome`：通过，已更新 `dist/background.js`、`dist/content.js` 和 Chrome zip 构建产物。
- 本地函数级 smoke test：新版 `launch_zhilian_job_detail_collection()` 返回 `wake_url`、`chrome_launched` 和 `chrome_error`。
- MCP 客户端调用仍返回旧格式，说明当前运行的 MCP Server 进程尚未重载新代码；端到端闭环需重启 MCP Server 和刷新 Chrome 扩展后验证。

### 署名
**Codex**
*Timestamp: 2026-05-06 23:38 (Asia/Shanghai)*

---

## [2026-05-06] - 修复详情队列结果文件插值错误 (Codex)

### 会话纪要
采集详情任务后，`D:\Downloads\zhilian_detail_results.json` 内容出现字面量 `${encodeURIComponent(...)}`，说明 TypeScript 模板字符串没有执行插值。检查确认 `readResults()` 和 `writeResult()` 中存在错误的 `\${...}` 转义。

### 主要变更

#### 1. 模板字符串修复
- 将 `file:///D:/Downloads/\${DETAIL_RESULTS_FILE}` 修正为 `file:///D:/Downloads/${DETAIL_RESULTS_FILE}`。
- 将 `data:application/json;charset=utf-8,\${encodeURIComponent(...)}` 修正为正常插值。

#### 2. JSONL 输出格式
- 保持结果文件名常量为 `zhilian_detail_results.jsonl`。
- 将结果文件 MIME 改为 `text/plain;charset=utf-8`，以符合 JSONL 文本行格式。
- 写入前显式生成 `content`，内容为一行一个 JSON 对象。

#### 3. 构建产物
- 重新构建 Chrome 扩展，更新 `dist/background.js` 和 `builds/joblens-1.10.0-chrome.zip`。

### 验证
- `rg "\\\$\{|data:application/json|zhilian_detail_results\.json\b" integrations/joblens/src/background.ts`：确认错误插值和旧 MIME 不再存在。
- `npm run build:chrome`：通过。
- 构建产物中包含 `zhilian_detail_results.jsonl` 与 `data:text/plain;charset=utf-8`。

### 署名
**Codex**
*Timestamp: 2026-05-06 02:20 (Asia/Shanghai)*

---

## [2026-05-05] - 修复智联详情队列重复采集 (Codex)

### 会话纪要
扫描 `D:\Downloads` 后发现 `ZHILIAN_DETAIL_*.md` 在 2026-05-05 22:39-22:58 间大量重复生成。检查确认 `zhilian_detail_tasks.jsonl` 只有 5 条任务，但扩展后台仍反复处理同一批详情 URL。

### 主要变更

#### 1. 问题定位
- 详情任务文件：`D:\Downloads\zhilian_detail_tasks.jsonl`。
- 任务完成记录期望文件：`zhilian_detail_results.jsonl`。
- 实际目录中只有 `zhilian_detail_results.txt`，没有 `zhilian_detail_results.jsonl`，导致后台轮询无法可靠识别已完成任务。

#### 2. 队列去重修复
- 在 Joblens Chrome 扩展后台增加 `browser.storage.local` 已完成 URL 记录。
- `results.jsonl` 继续作为可读审计产物，但不再作为唯一去重依据。
- 详情队列按 URL 跳过已完成任务，避免任务文件残留时重复采集。

#### 3. 构建产物
- 重新构建 Chrome 扩展，更新 `dist/background.js` 和 `builds/joblens-1.10.0-chrome.zip`。

### 验证
- `npm run build:chrome`：通过。
- `rg "jobsniper_detail_done_task_urls_v1" dist/background.js`：确认构建产物包含存储去重逻辑。

### 署名
**Codex**
*Timestamp: 2026-05-05 23:05 (Asia/Shanghai)*

---

## [2026-05-05] - 生成职业级岗位画像文件 (Codex)

### 会话纪要
根据讨论结果，本次没有把岗位职责/岗位要求总结正文写入 `_岗位索引表_*.md`，而是在每个职业目录下单独生成 `_岗位画像_{职业}.md`。岗位索引表只保留一行跳转链接，继续承担岗位列表导航职责。

### 主要变更

#### 1. 新增职业画像文件
- `产品/互联网产品经理/AI产品经理/_岗位画像_AI产品经理.md`
- `教育培训/IT培训/人工智能讲师/_岗位画像_人工智能讲师.md`
- `教育培训/IT培训/编程教师/_岗位画像_编程教师.md`
- `教育培训/教务管理/课程设计/_岗位画像_课程设计.md`

#### 2. 统计口径
- 只统计具体岗位详情 Markdown 中的 JD 正文。
- 排除岗位索引表、frontmatter、标题、公司介绍和工商信息。
- 每条职责/要求后使用 `覆盖率：xx%（n/N）` 表示命中该语义主题的 JD 数与有效岗位详情样本数。

#### 3. 索引表链接
- 在 4 个 `_岗位索引表_*.md` 开头加入对应 `_岗位画像_*.md` 链接。

### 验证
- `find ... -name '_岗位画像_*.md'`：确认 4 份画像文件已生成。
- `rg -n "职业画像：见|覆盖率：" ...`：确认索引链接与覆盖率格式存在。

### 署名
**Codex**
*Timestamp: 2026-05-05 13:20 (Asia/Shanghai)*

---

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
