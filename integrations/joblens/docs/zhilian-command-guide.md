# Joblens Automation Guide

## Agent Rules

- Do not run `npm run build:chrome` before every harvest.
- Run `npm run build:chrome` only after source code or manifest changes, such as changes under `src/`, `package.json`, `package-lock.json`, or `webpack.config.js`.
- If the user only asks to collect data, launch Chrome directly with the matching WSL2 Agent command.
- Prefer WSL2 Agent commands. CMD and PowerShell commands are human fallback commands.
- Browser download results first land under `D:\Downloads`.
- Test results stay in `D:\Downloads`.
- Formal results must be archived into `/home/xstars/zhilian_intelligence_sandbox/artifacts` with `scripts/archive-zhilian-artifacts.sh`.
- For keywords containing `+`, such as `C++培训讲师`, include `clipper_keyword_b64u` to preserve the exact keyword.

## WSL2 Agent

### 进入项目目录

```bash
cd /home/xstars/programs/joblens
```

### 构建 Chrome 扩展，仅在代码变更后使用

```bash
npm run build:chrome
```

### 归档正式结果到 artifacts

```bash
scripts/archive-zhilian-artifacts.sh --keyword "C++培训讲师" --dry-run --since-minutes 30
```

```bash
scripts/archive-zhilian-artifacts.sh --keyword "C++培训讲师" --since-minutes 30
```

### 关键词分类采集

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://www.zhaopin.com/?jl=538&clipper_keyword_discovery=1&clipper_debug=1'
```

### 单页列表测试

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_test=1&clipper_debug=1'
```

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?kw=算法工程师&jl=538&clipper_auto=1&clipper_test=1&clipper_debug=1'
```

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?kw=前端开发&jl=538&clipper_auto=1&clipper_test=1&clipper_debug=1'
```

### 单页列表加详情测试

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_test=1&clipper_detail_test=1&clipper_debug=1'
```

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_test=1&clipper_detail_test=1&clipper_detail_limit=5&clipper_debug=1'
```

### 自动翻页采集

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_debug=1'
```

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?kw=算法工程师&jl=538&clipper_auto=1&clipper_debug=1'
```

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?kw=前端开发&jl=538&clipper_auto=1&clipper_debug=1'
```

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?kw=C%2B%2B%E5%9F%B9%E8%AE%AD%E8%AE%B2%E5%B8%88&clipper_keyword_b64u=Qysr5Z-56K6t6K6y5biI&jl=538&clipper_auto=1&clipper_debug=1'
```

### 指定页数采集

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_debug=1&clipper_pages=5'
```

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_debug=1&clipper_pages=auto'
```

### 批量关键词采集

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?jl=538&clipper_auto=1&clipper_pages=auto&clipper_debug=1&clipper_batch_keywords=AI产品经理%7C前端开发'
```

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://sou.zhaopin.com/?jl=538&clipper_auto=1&clipper_pages=auto&clipper_debug=1&clipper_batch_keywords=AI产品经理%7C算法工程师%7C前端开发'
```

### 打开指定智联路径

```bash
'/mnt/c/Program Files/Google/Chrome/Application/chrome.exe' 'https://www.zhaopin.com/sou/jl538/kw010G0IAEKTAC2VMFEG30/p1?clipper_auto=1&clipper_debug=1'
```

## CMD

### 进入项目目录

```cmd
pushd \\wsl.localhost\Ubuntu\home\xstars\programs\joblens
```

### 构建 Chrome 扩展，仅在代码变更后使用

```cmd
npm run build:chrome
```

### 关键词分类采集

```cmd
start chrome "https://www.zhaopin.com/?jl=538&clipper_keyword_discovery=1&clipper_debug=1"
```

### 单页列表测试

```cmd
start chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_test=1&clipper_debug=1"
```

```cmd
start chrome "https://sou.zhaopin.com/?kw=算法工程师&jl=538&clipper_auto=1&clipper_test=1&clipper_debug=1"
```

```cmd
start chrome "https://sou.zhaopin.com/?kw=前端开发&jl=538&clipper_auto=1&clipper_test=1&clipper_debug=1"
```

### 单页列表加详情测试

```cmd
start chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_test=1&clipper_detail_test=1&clipper_debug=1"
```

```cmd
start chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_test=1&clipper_detail_test=1&clipper_detail_limit=5&clipper_debug=1"
```

### 自动翻页采集

```cmd
start chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_debug=1"
```

```cmd
start chrome "https://sou.zhaopin.com/?kw=算法工程师&jl=538&clipper_auto=1&clipper_debug=1"
```

```cmd
start chrome "https://sou.zhaopin.com/?kw=前端开发&jl=538&clipper_auto=1&clipper_debug=1"
```

### 指定页数采集

```cmd
start chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_debug=1&clipper_pages=5"
```

```cmd
start chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_debug=1&clipper_pages=auto"
```

### 批量关键词采集

```cmd
start chrome "https://sou.zhaopin.com/?jl=538&clipper_auto=1&clipper_pages=auto&clipper_debug=1&clipper_batch_keywords=AI产品经理%7C前端开发"
```

```cmd
start chrome "https://sou.zhaopin.com/?jl=538&clipper_auto=1&clipper_pages=auto&clipper_debug=1&clipper_batch_keywords=AI产品经理%7C算法工程师%7C前端开发"
```

### 打开指定智联路径

```cmd
start chrome "https://www.zhaopin.com/sou/jl538/kw010G0IAEKTAC2VMFEG30/p1?clipper_auto=1&clipper_debug=1"
```

## PowerShell

### 进入项目目录

```powershell
Set-Location "\\wsl.localhost\Ubuntu\home\xstars\programs\joblens"
```

### 构建 Chrome 扩展，仅在代码变更后使用

```powershell
npm run build:chrome
```

### 关键词分类采集

```powershell
Start-Process chrome "https://www.zhaopin.com/?jl=538&clipper_keyword_discovery=1&clipper_debug=1"
```

### 单页列表测试

```powershell
Start-Process chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_test=1&clipper_debug=1"
```

```powershell
Start-Process chrome "https://sou.zhaopin.com/?kw=算法工程师&jl=538&clipper_auto=1&clipper_test=1&clipper_debug=1"
```

```powershell
Start-Process chrome "https://sou.zhaopin.com/?kw=前端开发&jl=538&clipper_auto=1&clipper_test=1&clipper_debug=1"
```

### 单页列表加详情测试

```powershell
Start-Process chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_test=1&clipper_detail_test=1&clipper_debug=1"
```

```powershell
Start-Process chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_test=1&clipper_detail_test=1&clipper_detail_limit=5&clipper_debug=1"
```

### 自动翻页采集

```powershell
Start-Process chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_debug=1"
```

```powershell
Start-Process chrome "https://sou.zhaopin.com/?kw=算法工程师&jl=538&clipper_auto=1&clipper_debug=1"
```

```powershell
Start-Process chrome "https://sou.zhaopin.com/?kw=前端开发&jl=538&clipper_auto=1&clipper_debug=1"
```

### 指定页数采集

```powershell
Start-Process chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_debug=1&clipper_pages=5"
```

```powershell
Start-Process chrome "https://sou.zhaopin.com/?kw=AI产品经理&jl=538&clipper_auto=1&clipper_debug=1&clipper_pages=auto"
```

### 批量关键词采集

```powershell
Start-Process chrome "https://sou.zhaopin.com/?jl=538&clipper_auto=1&clipper_pages=auto&clipper_debug=1&clipper_batch_keywords=AI产品经理%7C前端开发"
```

```powershell
Start-Process chrome "https://sou.zhaopin.com/?jl=538&clipper_auto=1&clipper_pages=auto&clipper_debug=1&clipper_batch_keywords=AI产品经理%7C算法工程师%7C前端开发"
```

### 打开指定智联路径

```powershell
Start-Process chrome "https://www.zhaopin.com/sou/jl538/kw010G0IAEKTAC2VMFEG30/p1?clipper_auto=1&clipper_debug=1"
```
