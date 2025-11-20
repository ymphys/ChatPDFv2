# ChatPDFv2 – MinerU-Powered PDF Intelligence

ChatPDFv2是一个命令行工作流，它可以将任何公开可下载的PDF链接或本地PDF文件利用[MinerU](https://mineru.net/)平台转换成Markdown格式文件，并进一步进行用户自定义的互动式快速解读，是对[Chatmd](https://github.com/ymphys/Chatmd)的升级。支持单一文件和批量处理模式。

**主要功能:**
- 单一PDF URL处理
- 本地PDF文件批量处理（通过目录）
- PDF URL批量处理
- 批量任务状态查询
- 将链接通过 MinerU API 上传，处理完成后得到 Markdown 版本 (以及原始的 PDF 文件) 并下载至 `files/<slug>/`
- 运行一个支持用户自定义问题的DeepSeek解读，每次问答结果都将存储下来作为后续提问的输入，因此具有上下文记忆功能
- 保存了可后续追溯的log文件，方便用户查看每次运行操作细节

使用它可以加速文献阅读，生成摘要或提取文献关键信息。

---

## 安装指南

1. **克隆仓库**
   ```bash
   git clone https://github.com/your-account/chatpdfv2.git
   cd chatpdfv2
   ```

2. **创建虚拟环境 (可选但推荐)**
   ```bash
   uv sync
   ```
   如果没有安装uv，请参见[uv installation](https://docs.astral.sh/uv/getting-started/installation/)

3. **配置环境变量**
   - `DEEPSEEK_API_KEY` – 用于解读文档
   - `MINERU_API_KEY` – 用于上传PDF链接到 MinerU，如果你已经将PDF文件转换为markdown文件，则不需要获取该API key
   - 上述API_KEY默认直接存储在环境变量中

---

## 使用指南

Mineru API 获取：请至[官方页面](https://mineru.net/apiManage/token)申请。
DeepSeek API 获取：请至[官方页面](https://platform.deepseek.com/api_keys)申请。

### 单一文件处理模式

**PDF URL 模式**
```bash
uv run main.py --pdf-url https://example.com/paper.pdf
```

**本地 Markdown 模式**
```bash
uv run main.py --md-path files/example.md
```

### 批量处理模式

**本地文件批量处理**
```bash
# 处理目录中的所有PDF文件
uv run main.py --batch-dir /path/to/pdf/files
```

**URL 批量处理**
```bash
# 处理文件中的PDF URL列表
uv run main.py --batch-urls-file files/batch_urls.txt

# 或者使用默认文件路径
uv run main.py --batch-urls-file
```

**批量任务状态查询**
```bash
# 查询批量任务状态
uv run main.py --batch-id your_batch_id_here
```

### 高级配置选项

**自定义超时时间**
```bash
uv run main.py --batch-dir ./documents --mineru-timeout 1200
```

**选择模型版本**
```bash
uv run main.py --batch-dir ./documents --model-version vlm
```

**控制AI输出随机性**
```bash
uv run main.py --md-path document.md --temperature 0.7
```

### 关键命令行参数

| 参数 | 描述 |
| --- | --- |
| `--pdf-url URL` | 获取，转换，并分析一个在线 PDF 文件。 |
| `--md-path PATH` | 跳过 MinerU 转换过程，分析已有 Markdown 文件。 |
| `--batch-dir DIR` | 批量处理指定目录中的所有 PDF 文件。 |
| `--batch-urls-file [FILE]` | 批量处理文本文件中的 PDF URL 列表（默认：files/batch_urls.txt）。 |
| `--batch-id ID` | 查询批量任务的状态。 |
| `--mineru-timeout SECONDS` | MinerU 处理超时时间（默认：600秒）。 |
| `--model-version VERSION` | MinerU 模型版本（默认：vlm）。 |
| `--temperature TEMPERATURE` | DeepSeek 模型温度参数（默认：1.0）。 |

---

## DeepSeek 集成

ChatPDFv2 使用 DeepSeek 作为唯一的 AI 模型进行文档解释和分析，提供了更好的成本效益和性能。

### 功能特性

- **成本优化**: DeepSeek 相比 OpenAI 具有更优的成本效益
- **重试机制**: 自动重试机制（最多 4 次）和指数退避策略
- **成本估算**: 包含详细的成本估算功能
- **错误处理**: 完整的错误处理和日志记录

### 成本估算

- 输入令牌：¥2.0/百万 tokens（缓存未命中）
- 输出令牌：¥3.0/百万 tokens

---

## 批量处理功能详解

### 本地文件批量上传与解析

**功能特性：**
- 支持批量申请文件上传链接（最多200个文件）
- 自动上传多个本地文件到 MinerU 服务器
- 系统自动提交解析任务，无需手动调用提交接口
- 文件上传链接有效期为 24 小时
- 上传文件时无需设置 Content-Type 请求头

**使用示例：**
```bash
# 批量处理目录中的所有PDF文件
uv run main.py --batch-dir ./documents --mineru-timeout 1200
```

### URL 批量处理

**功能特性：**
- 从文本文件读取多个 PDF URL 进行批量处理
- 支持注释行（以 # 开头）和空行过滤
- 默认使用 `files/batch_urls.txt` 文件
- 自动下载原始PDF文件并保存

**batch_urls.txt 文件格式：**
```
# 批量处理的 PDF URL 列表
# 每行一个 URL，以 # 开头的行会被忽略

https://example.com/paper1.pdf
https://example.com/paper2.pdf
https://example.com/paper3.pdf
```

### 批量任务状态查询

**功能特性：**
- 通过 batch_id 批量查询提取任务的进度
- 支持轮询等待任务完成
- 实时监控任务状态（pending, waiting-file, done）
- 自动下载并处理完成的任务结果

**使用示例：**
```bash
# 查询特定批次的结果
uv run main.py --batch-id 8c61f136-b2a0-4fa3-abd7-9a7f2a00fa61
```

---

## 输出结构

**单一文件处理：**
```
files/<slug_timestamp>/
├── <slug_timestamp>.pdf          # 原始PDF文件下载
├── full.md                       # 提取出的Markdown文件
└── interpretation_results.md     # DeepSeek生成的问答报告
```

**批量处理：**
```
files/
├── document1_20241120123456/
│   ├── document1_20241120123456.pdf
│   ├── full.md
│   └── interpretation_results.md
├── document2_20241120123457/
│   ├── document2_20241120123457.pdf
│   ├── full.md
│   └── interpretation_results.md
└── ...
```

- 处理日志写入到了 `chatpdf.log` 中
- 每个文件都会创建独立的子目录，便于管理和追溯
- 问题自定义：更改[cli.py](chatpdfv2/interfaces/cli.py)中的QUESTIONS列表

---

## 注意事项

1. **文件限制**: 单次批量处理最多支持 200 个文件
2. **链接有效期**: 上传链接有效期为 24 小时
3. **自动提交**: 文件上传完成后系统自动提交解析任务
4. **内容类型**: 上传文件时无需设置 Content-Type 请求头
5. **错误处理**: 包含完整的错误处理和重试机制
6. **网络要求**: 确保网络连接稳定，处理大量文件时建议使用较长的超时时间
7. **API密钥**: 确保正确设置 `DEEPSEEK_API_KEY` 和 `MINERU_API_KEY` 环境变量

---

## 使用的技术

- **Python 3.12+**
- **MinerU API** – 远程 PDF-to-Markdown 转换
- **DeepSeek API** – 切块的问题/答案合成

---

## 徽章

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![MinerU](https://img.shields.io/badge/MinerU-API-green)](https://mineru.net/)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-API-orange)](https://platform.deepseek.com/)
[![Status](https://img.shields.io/badge/status-active-success)](#project-statusroadmap)

---

## 项目状态 / 开发路线图

- **目前状态:** 持续更新中，通过命令行使用，支持单一文件和批量处理模式，自定义问题，可追加问题。
- **已实现功能:**
  - 单一PDF URL处理
  - 本地PDF文件批量处理（通过目录）
  - PDF URL批量处理
  - 批量任务状态查询
  - DeepSeek AI 集成
- **未来计划开发:**
  - 前端图形界面开发
  - 通过 Docker 打包处理依赖
  - 更丰富的输出格式选项

欢迎您通过 issues 或 pull requests 做出贡献！
