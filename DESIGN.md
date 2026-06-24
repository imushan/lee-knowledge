# OKF-KB 设计文档

> 基于 Open Knowledge Format (OKF) 的个人知识库 MCP 系统。
> 数据来源为网页文章；Claude Code 作为 agent，MCP server 提供工具，`CLAUDE.md` 提供规则。

---

## 1. 目标

把"网页文章"沉淀为**可版本化、可检索、可被 agent 直接消费**的知识库，且：

- **可复现**：原料钉死在本地，富化结果可 diff、可重跑。
- **可演进**：知识库能安全增长、加深分类、重组迁移而不断链。
- **零锁定**：产出是纯 markdown + YAML frontmatter（OKF），任何工具都能读。
- **Claude Code 即 agent**：不维护独立的 Python agent 循环，工具通过 MCP 暴露。

---

## 2. 设计原则

1. **两层模型** —— 原料层（source of truth）与知识层（curated output）分离，读取永远基于本地文件。
2. **约束住进工具，而非只靠 prompt** —— 必须成立的不变量（`type` 必填、链接完整性、augmentation）由工具强制，模型只是调用方。
3. **先采集后富化** —— 永远 `acquire_url` 落盘后再读，禁止拿实时 URL 当源。
4. **文件相对链接** —— 交叉链接用相对路径，保证 GitHub / 纯文件 / Obsidian 都能渲染。
5. **核心/包装分层** —— 纯逻辑（`okf_core.py`）不依赖 MCP，可脱离 server 单独测试或套批处理循环。

---

## 3. 部署布局（实际目录）

```
/home/ai/lee/workspace/lee_knowledge/
├── .mcp.json            # Claude Code MCP 注册（指向 mcp/server.py）
├── CLAUDE.md            # agent 指令：工作流 + 硬规则 + 中文产出
├── DESIGN.md            # 本文档
├── mcp/                 # 代码层（无状态，可随处部署）
│   ├── okf_core.py      # 纯逻辑（stdlib + PyYAML），11 个核心函数
│   ├── server.py        # FastMCP 包装，11 个工具，stdio 运行
│   └── requirements.txt # mcp / pyyaml / markdownify
└── okf-kb/              # 数据层（OKF_KB_ROOT 指向这里）
    ├── sources/articles/        # 原料层：抓取的文章（pin 死）
    └── bundles/<OKF_BUNDLE>/    # 知识层：curated OKF 概念
        ├── index.md             # 自动生成的目录（SPEC §6）
        ├── log.md               # 自动追加的更新历史（SPEC §7）
        ├── concepts/            # 主概念
        └── references/          # 可复用条目（metrics / joins / glossary，按需生成）
```

**配置项**（环境变量，见 `.mcp.json`）：

| 变量 | 当前值 | 含义 |
|---|---|---|
| `OKF_KB_ROOT` | `.../lee_knowledge/okf-kb` | 知识库根目录 |
| `OKF_BUNDLE` | `test` | 当前激活的 bundle 子目录 |

> 切换/新建知识库：改这两个变量即可，代码不动。

---

## 4. 两层模型

| 层 | 路径 | 角色 | 怎么产生 | 内容形态 |
|---|---|---|---|---|
| 原料层 | `sources/articles/*.md` | 事实 / 源材料（"catalog"） | `acquire_url` 抓网页 | 文章原文，原样 |
| 知识层 | `bundles/<name>/*.md` | 知识库本体（交付物） | `write_concept_doc` 模型撰写 | 结构化 OKF：frontmatter + 正文 + 交叉链接 |

**为什么分开**：原料钉死 → 富化可复现、可 diff、可溯源；多对多（一篇拆多个 concept，多篇喂一个 concept）不受干扰。`bundles/` 自包含，删掉 `sources/` 仍可用，但建议保留以便重跑与核对引用。

---

## 5. 工具清单（11 个）

代码真实实现见 `mcp/okf_core.py`；MCP 包装见 `mcp/server.py`。

### 采集层
| 工具 | 参数 | 返回 | 作用 |
|---|---|---|---|
| `acquire_url` | `url`*, `slug`? | `{id,path,title,bytes}` | 抓网页→转 markdown→落 `sources/articles/` |

### 浏览源层
| 工具 | 参数 | 返回 | 作用 |
|---|---|---|---|
| `list_articles` | — | `[{id,title,resource,timestamp}]` | 列出原料 |
| `read_article` | `article_id`* | `{id,frontmatter,body}` | 读原文（等价原 `read_concept_raw`） |

### 知识库读写层
| 工具 | 参数 | 返回 | 作用 |
|---|---|---|---|
| `list_concepts` | — | `[{id,type,title,description,resource}]` | 列概念 + 合法链接目标 |
| `read_existing_doc` | `concept_id`* | `{id,frontmatter,body}` \| `null` | 读已有 doc（`null`→新建） |
| `write_concept_doc` | `concept_id`*, `frontmatter`*, `body`* | `{id,path,created,bytes}` 或 `{error,...}` | 全量写/替换 concept（强制 type/title/description + augmentation 守卫） |

### 维护层
| 工具 | 参数 | 返回 | 作用 |
|---|---|---|---|
| `generate_index` | — | `{written:[...]}` | 重生成各级 `index.md`（幂等） |
| `append_log` | `action`*, `summary`* | `{path,date,entry}` | 追加 `log.md`（SPEC §7 格式） |
| `move_concept` | `from_id`*, `to_id`* | `{moved,from,to,path,links_rewritten}` | 迁移 + 重写所有受影响链接 |

### web 富化层（爬取模式，可选）
| 工具 | 参数 | 返回 | 作用 |
|---|---|---|---|
| `start_web_crawl` | `seeds`*, `max_pages`?, `max_depth`?, `allowed_hosts`?, `denied_path_substrings`? | `{seeds,allowed_hosts,max_pages,max_depth}` | 注册 seeds + 爬取预算（host 自动加白） |
| `fetch_url` | `url`* | `{url,title,markdown,links,...}` 或 `{error,...}` | 带守卫抓单页（host 白名单/预算/深度/去重/防自造 URL） |

---

## 6. 标准工作流

```
1. acquire_url(url)                          → 落 sources/articles/
2. read_article(id)                          → 读原文
3. list_concepts() + read_existing_doc(id)   → 查是否已存在
4. write_concept_doc(id, frontmatter, body)  → 写概念文档（中文）
5. generate_index()                          → 刷新 index.md
6. append_log("Creation"/"Update", "...")    → 记日志
```

**重组**（移动已有概念，禁止手改）：
```
move_concept(from_id, to_id)   → 自动重写链接 + 刷新 index + 记 log
```

**web 富化**（顺藤摸瓜爬取权威文档，可选）：
```
start_web_crawl(seeds, max_pages=20, max_depth=2)   → 注册 seeds + 预算 + host 白名单
fetch_url(seed)                                     → {markdown, links, ...}
  → 从 links 挑权威页 → fetch_url → 富化已有 concept / mint references/ / 跳过
  → error（max_pages/host/depth/not-reachable）即停或换 URL，不重试同一 URL
```

---

## 7. 关键不变量与保证

| 不变量 | 由谁保证 | 机制 |
|---|---|---|
| frontmatter 必含 `type`+`title`+`description` | `write_concept_doc` | 缺则返回 `{error,missing}`（不抛异常，便于模型恢复） |
| `timestamp` 自动刷新 | `write_concept_doc` | 空则填当前 UTC |
| frontmatter 规范排序 | `write_concept_doc` | `_reorder_frontmatter` 固定 key 顺序，diff 干净 |
| concept_id 无逃逸 | `write/read/move` | `_normalize_concept_id` 剥离 `/`、过滤 `.`/`..` |
| **augmentation 不丢章节** | `write_concept_doc` | 覆盖已有 doc 时若丢掉已有 `#` 标题则拒绝（代码块感知） |
| 写是全量替换 | `write_concept_doc` | prompt 要求 augmentation 时回传所有 key |
| `index.md` 反映真实内容 | `generate_index` | 扫描派生，幂等 |
| `log.md` SPEC §7 格式 | `append_log` | ISO 日期、newest-first、同日分组 |
| **迁移不断链** | `move_concept` | 入站链接重写 + 出站链接重基（见下） |
| **爬取受控** | `fetch_url` | host 白名单 / 页数预算 / 深度上限 / 去重 / 必须从 seed 可达 |
| 交叉链接用相对路径 | `CLAUDE.md` 规则 | 不以 `/` 开头 |
| 只链已存在 concept | `CLAUDE.md` 规则 | 目标取自 `list_concepts` |
| 不编造事实/URL | `CLAUDE.md` 规则 | 引用只用真实抓取过的 |
| 产出中文 | `CLAUDE.md` 规则 | 代码/字段名/路径/URL 保持原样 |

### 链接完整性（move_concept 的核心）

移动一个文档会**双向断链**，`move_concept` 确定性修复：

- **入站**：其他文档里指向旧路径的链接 → 改写为指向新路径的正确相对路径（按每个源文档位置算 `../` 层数）。同时识别 bundle 绝对路径 `/x.md` 形式。
- **出站**：被移动文档自身的相对链接 → 按新位置重基（rebase）。
- 之后自动：清空旧目录、`generate_index`、`append_log`。

边界：`from==to` no-op；目标已存在 `ValueError`；源不存在 `FileNotFoundError`。

---

## 8. 配置与运行

**环境**：conda env `okf-kb`（`/home/ai/miniconda3/envs/okf-kb/bin/python`），已装 `mcp/pyyaml/markdownify`。

**注册**（已配置，见 `.mcp.json`）：

```json
{
  "mcpServers": {
    "okf-kb": {
      "command": "/home/ai/miniconda3/envs/okf-kb/bin/python",
      "args": ["/home/ai/lee/workspace/lee_knowledge/mcp/server.py"],
      "env": {
        "OKF_KB_ROOT": "/home/ai/lee/workspace/lee_knowledge/okf-kb",
        "OKF_BUNDLE": "test"
      }
    }
  }
}
```

> `command` 直指 env 的 `python` 二进制，**不要**用 `conda run`（MCP server 必须是直接可执行程序）。

**使用**：重启 Claude Code（或 `/mcp`）→ 工具可用 → 自然语言驱动，例如"抓 URL 并按 CLAUDE.md 富化成中文概念"。

---

## 9. 演进策略

| 场景 | 是否自愈 | 做法 |
|---|---|---|
| 新增概念 | ✅ 自动 | 写完 `generate_index` |
| 加深嵌套（新子目录） | ✅ 自动 | 写到深路径，`generate_index` 给每层建 index |
| 移动/重命名 | ✅ 工具保证 | `move_concept`（禁手改） |
| 知识库迁移位置 | 改 `OKF_KB_ROOT` | 代码不动 |
| 多知识库 | 复制 `.mcp.json` 改 `OKF_KB_ROOT`/`OKF_BUNDLE` | 独立 server |

**分类粒度**：文章是散文非表，按内容自定目录（`concepts/`、`references/metrics/` 等）。`datasets/`/`tables/` 是 BigQuery 场景的领域约定，**不是 OKF 固定结构**，不要硬套。

---

## 10. 与原 OKF 的关系

本项目是 [knowledge-catalog/okf](https://github.com/GoogleCloudPlatform/knowledge-catalog) 的**消费侧复刻**，面向"网页文章"而非 BigQuery。早期版本相对原仓库存在 4 处差距，现已全部对齐（见 §12）：

| 维度 | 原 OKF reference agent | 本项目 | 状态 |
|---|---|---|---|
| 数据源 | BigQuery（结构化 catalog） | 网页文章（散文） | 设计差异 |
| agent 载体 | Python ADK runner（独立循环） | Claude Code（MCP） | 设计差异 |
| frontmatter 写时校验 | 强制 type/title/description/timestamp | 强制 type/title/description（timestamp 自动） | ✅ 已对齐 |
| augmentation 代码守卫 | 拒绝缩小 Schema/Citations | 拒绝丢掉已有 `#` 标题（代码块感知） | ✅ 已对齐 |
| concept_id 归一化 | `parse_concept_id` | `_normalize_concept_id`（防逃逸） | ✅ 已对齐 |
| frontmatter 规范排序 | `_reorder_frontmatter` | `_reorder_frontmatter` | ✅ 已对齐 |
| web 富化/爬取 | `fetch_url`（host/预算/深度/去重） | `start_web_crawl` + `fetch_url`（同套守卫） | ✅ 已对齐 |
| `index.md` 生成 | runner 后处理 `regenerate_indexes` | `generate_index` 工具（模型主动调） | ✅ |
| `log.md` | **无自动化** | `append_log` 工具（本项目新增） | ➕ 超越 |
| 移动/重组 | 无 | `move_concept` + 双向链接重写（本项目新增） | ➕ 超越 |
| 目录描述合成 | 调 LLM（gemini-flash） | 纯确定性（用 frontmatter description） | 简化 |

OKF 格式本身（SPEC §1–11）完全遵守：concept = markdown + YAML frontmatter，`type` 必填，`index.md`/`log.md` 为保留文件名，交叉链接表达关系。

---

## 11. 扩展点

- **换数据源**：`okf_core.py` 里 `list_articles`/`read_article`/`acquire_url` 是 file-source 实现；接数据库 catalog 时替换这三个即可，其余不变。
- **批处理**：需要无人值守批量富化时，`import okf_core` 套 `for concept in concepts:` 循环——核心函数已是纯 Python，零迁移成本。
- **可视化**：bundle 是标准 OKF，可用 `knowledge-catalog/okf` 的 `visualize`（仅需 PyYAML）生成单文件交互图谱。

---

## 12. v2 增量：约束进工具 + web 富化

v1 把若干"必须成立的不变量"留在了 prompt 里（违反 §2 原则）。v2 将它们下沉到代码，并补齐 web 爬取能力。工具总数 9 → **11**。

| 增量 | 解决的问题 | 实现 |
|---|---|---|
| **augmentation 代码守卫** | v1 整段重写会丢章节，纯靠 prompt | `write_concept_doc` 覆盖已有 doc 时，拒绝丢掉任何已有 `#` 标题，返回 `{error,dropped_headings}`；代码块内 `#` 不计 |
| **frontmatter 强校验** | v1 只校验 `type`，index/检索缺 description | 必填 `type+title+description`，缺则 `{error,missing}` |
| **concept_id 归一化** | v1 对 `/x`、`..` 不设防 | `_normalize_concept_id` 在 write/read/move 统一应用，防逃逸 |
| **frontmatter 规范排序** | v1 插入序，diff 噪音 | `_reorder_frontmatter` 固定 key 序 |
| **web 爬取（`start_web_crawl` + `fetch_url`）** | v1 只能钉死单篇，无"顺藤摸瓜"富化 | 守卫全在 `fetch_url` 内：host 白名单、denied 路径、页数预算、深度上限、去重、必须从 seed 可达（防模型自造 URL） |

### 校验/守卫的返回约定

`write_concept_doc` 与 `fetch_url` 在被拒绝时**返回 `{error, ...}` 而非抛异常**——模型读 `error`、修正输入、重调。这是与原仓库一致的模式，比异常更适合 tool-calling 循环。

### 验证摘要

augmentation 守卫（丢标题被拒 + 代码块感知）、强校验（缺 title/description）、id 归一化（无逃逸）、规范排序、web 守卫（host/预算/深度/去重/可达性）均已用临时 KB + `example.com` 实测通过；conda 环境 11 工具全部注册。
