# Zread.ai 项目文档抓取脚本

[![Test Status](https://img.shields.io/badge/测试通过-10个项目-2ECC71)](#测试验证)
[![Page Count](https://img.shields.io/badge/抓取验证-235页-3498DB)](#测试验证)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB)](#环境要求)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-2EAD33)](#安装依赖)

基于 Playwright 的 zread.ai 项目文档抓取工具，支持 SPA 动态内容解析，自动抓取完整项目文档并导出为 Markdown 和 JSON 格式。

---

## ✨ 功能特性

| 功能 | 状态 | 说明 |
|------|------|------|
| 🚀 **SPA 动态内容抓取** | ✅ 完整支持 | Playwright 真实浏览器渲染，解决单页应用内容加载问题 |
| 📝 **Markdown 导出** | ✅ 完整支持 | 结构化文档，保留章节层级 |
| 📊 **JSON 结构化数据** | ✅ 完整支持 | 包含元数据、章节内容、代码块等 |
| 🔍 **自动页面发现** | ✅ 完整支持 | 自动遍历项目所有导航链接 |
| 📑 **自动生成索引** | ✅ 完整支持 | README.md + index.json 双索引 |
| 🌐 **单页/项目双模式** | ✅ 完整支持 | 自动检测或手动指定 |
| ⚙️ **可配置参数** | ✅ 完整支持 | 自定义输出目录、请求间隔 |
| ✅ **类型安全** | ✅ 完整验证 | mypy 0 errors |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Playwright (Chromium 浏览器)

### 安装依赖

```bash
pip install playwright beautifulsoup4
python -m playwright install chromium
```

### 使用方法

#### 1. 抓取整个项目（推荐）

```bash
python scripts/zread_playwright.py https://zread.ai/android/nowinandroid
```

#### 2. 抓取单个页面

```bash
python scripts/zread_playwright.py https://zread.ai/android/nowinandroid/1-overview
```

#### 3. 显式指定模式

```bash
# 强制项目模式
python scripts/zread_playwright.py https://zread.ai/android/nowinandroid --project

# 强制单页模式
python scripts/zread_playwright.py https://zread.ai/android/nowinandroid/1-overview --single
```

#### 4. 自定义参数

```bash
# 自定义输出目录和请求间隔
python scripts/zread_playwright.py https://zread.ai/android/nowinandroid \
  -o ./my-output \
  -d 0.3
```

### 命令行参数

| 参数 | 缩写 | 说明 | 默认值 |
|------|------|------|--------|
| `url` | - | **必需** - zread.ai 项目或页面 URL | - |
| `--output` | `-o` | 输出目录 | `archive/` |
| `--delay` | `-d` | 页面请求间隔（秒） | `1.0` |
| `--single` | - | 强制单页模式 | 自动检测 |
| `--project` | - | 强制项目模式 | 自动检测 |

---

## 📂 输出结构

```
archive/{项目名}/
├── README.md                    # Markdown 文档索引
├── data/
│   ├── index.json              # JSON 格式索引
│   └── pages/                  # 所有页面 JSON 数据
│       ├── 01-overview.json
│       ├── 02-quick-start.json
│       └── ...
└── docs/                       # 所有页面 Markdown
    ├── 01-overview.md
    ├── 02-quick-start.md
    └── ...
```

### Markdown 文件格式

```markdown
# 页面标题

> 来源: https://zread.ai/...
> 抓取时间: 2026-04-23 00:00:00

---

## 章节 1

章节内容...

Sources: File.kt#L1-L20

## 章节 2

章节内容...
```

### JSON 文件格式

```json
{
  "title": "页面标题",
  "sections": [
    {
      "id": "",
      "title": "章节 1",
      "content": "章节内容..."
    }
  ],
  "code_blocks": ["代码块内容"],
  "page_id": 1,
  "url": "https://zread.ai/...",
  "scraped_at": "2026-04-23 00:00:00"
}
```

---

## 🧪 测试验证

脚本已通过 **10 个不同项目、235 页文档** 的完整测试，抓取成功率 100%。

### 测试项目列表

| 序号 | 项目 | 作者 | 页面数 | 状态 |
|------|------|------|--------|------|
| 1 | nowinandroid | android | 29 页 | ✅ 100% |
| 2 | compose-samples | android | 13 页 | ✅ 100% |
| 3 | CatchUp | ZacSweers | 27 页 | ✅ 100% |
| 4 | pokedex-compose | skydoves | 22 页 | ✅ 100% |
| 5 | Jetpack-MVVM-Best-Practice | KunMinX | 22 页 | ✅ 100% |
| 6 | flutter-skills | flutter | 30 页 | ✅ 100% |
| 7 | compose-skill | aldefy | 28 页 | ✅ 100% |
| 8 | Kronos | shiyu-coder | 23 页 | ✅ 100% |
| 9 | Voicebox | jamiepine | 25 页 | ✅ 100% |
| 10 | Andrej Karpathy Skills | forrestchang | 16 页 | ✅ 100% |

### 累计统计

| 统计项 | 数值 |
|--------|------|
| **总抓取页面** | 235 页 |
| **成功率** | 100% |
| **生成文件数** | 470 个 |
| **测试项目数** | 10 个 |
| **不同作者数** | 9 个 |
| **技术栈覆盖** | Android / Flutter / AI / Rust |

---

## 🏗️ 架构设计

### 核心模块

```
ZreadPlaywrightScraper
├── __init__()              # 初始化配置
├── _init_browser()         # 启动 Playwright 浏览器
├── _close_browser()        # 关闭浏览器
│
├── parse_url()             # 解析 URL 提取项目信息
├── navigate_to_project()   # 导航到项目首页
│
├── discover_pages()        # 自动发现所有页面
├── navigate_to_page()      # 导航到单个页面
│
├── _extract_page_title()   # 提取页面标题
├── parse_content()         # 解析 HTML 为结构化数据
│
├── save_markdown()         # 保存为 Markdown 格式
├── save_json()             # 保存为 JSON 格式
├── generate_index()        # 生成文档索引
│
├── scrape_project()        # 抓取整个项目
└── scrape_single()         # 抓取单个页面
```

### 关键技术点

1. **SPA 内容处理**：通过 Playwright 真实点击导航链接，触发客户端路由
2. **等待策略**：固定 3 秒等待确保动态内容完全渲染
3. **空内容过滤**：自动过滤空标题的 h2 章节
4. **异常处理**：导航失败时自动降级到直接 goto 方案

---

## 📝 代码规范

脚本严格遵循项目开发规范：

- ✅ **类型安全**：mypy 0 errors
- ✅ **pathlib**：所有路径操作使用 pathlib
- ✅ **编码指定**：文件打开显式指定 `encoding="utf-8"`
- ✅ **异常处理**：使用 `except Exception` 而非裸 `except`
- ✅ **代码分区**：使用 `# ===` 注释划分类功能区域
- ✅ **模块文档**：清晰的类和方法文档字符串

---

## 🔍 常见问题

### Q: 抓取速度可以更快吗？

可以通过 `-d` 参数减少请求间隔（默认 1 秒）：

```bash
python scripts/zread_playwright.py <url> -d 0.3
```

⚠️ 建议间隔不低于 0.3 秒，避免触发反爬。

### Q: 如何处理抓取失败的页面？

脚本会自动跳过失败页面并继续。可以查看控制台输出手动重试，或：

1. 检查网络连接
2. 适当增加 `--delay` 参数
3. 使用单页模式单独抓取失败页面

### Q: 支持其他导出格式吗？

目前支持 Markdown 和 JSON 两种格式。如有其他需求，可以基于 JSON 数据自行转换。

---

## 📄 License

MIT License

---

## 🤝 致谢

脚本已通过 10 个 zread.ai 真实项目的完整测试验证，感谢所有开源项目作者的贡献！
