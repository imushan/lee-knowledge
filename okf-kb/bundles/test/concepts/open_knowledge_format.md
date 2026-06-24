---
type: Concept
title: Open Knowledge Format (OKF)
description: Google Cloud 提出的开放规范,用带 YAML frontmatter 的 markdown 文件目录表示知识,供人与 AI agent
  无需翻译地互操作。
resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf
tags:
- OKF
- 知识格式
- LLM
- AI agent
- BigQuery
- metadata
- markdown
- Google Cloud
- Knowledge Catalog
timestamp: '2026-06-24T08:13:18Z'
---

# Open Knowledge Format (OKF)

**Open Knowledge Format(OKF)** 是一个厂商中立的开放规范,将 [LLM-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 模式正式化为一种可移植、可互操作的格式,用于表示现代 AI 系统所需的元数据、上下文与策展知识。OKF v0.1 由 Google Cloud Data Cloud 团队于 2026 年 6 月 12 日发布。

OKF 的核心理念是:**format, not platform**(是格式,不是平台)。一个 OKF 文档集(bundle)只是:

- **只是 markdown** —— 任何编辑器可读、可在 GitHub 渲染、可被任何搜索工具索引
- **只是文件** —— 可打包为 tarball、托管于任意 git 仓库、挂载到任意文件系统
- **只是 YAML frontmatter** —— 用于少量需被查询的结构化字段:`type`、`title`、`description`、`resource`、`tags`、`timestamp`

没有复杂的压缩方案,没有新的运行时,也不需要 SDK。

## 要解决的问题:碎片化的上下文景观

组织内被基础模型使用的信息绝大多数是内部知识:表的 schema、指标的业务定义、事件处置 runbook、系统间的 join 路径、旧 API 的弃用通告等。这些「知识原子」目前散落在互不兼容的载体上:

- 自带 API 的元数据目录(metadata catalog)
- wiki、第三方系统或共享盘
- 代码注释、docstring 或 notebook 单元格
- 少数资深工程师的脑子里

当 AI agent 需要回答「如何从事件流计算周活跃用户?」时,必须从这些散乱、互不兼容的界面拼凑答案。每个厂商都有自己的目录、SDK、知识图谱 schema,知识无法跨产品/跨组织迁移。结果:每个 agent 构建者都在从零解决同一个上下文拼装问题,每个目录厂商都在重复发明同样的数据模型。

## 知识即活动 wiki(Knowledge as a living wiki)

与其反复让模型搜索同一批文档,不如给 agent 一个随时间增值的共享 markdown 库:agent 承担读取与更新文件的繁琐工作,团队像管理代码一样策展内容。Andrej Karpathy 在其 [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 中写道:「LLM 不会厌倦、不会忘记更新交叉引用,能一次触碰 15 个文件」——正是这些让人放弃个人 wiki 的记账工作,LLM 恰好擅长。

相同的「知识即 wiki」模式在不同名字下反复出现:接入编码 agent 的 [Obsidian vault](https://obsidian.md/help/vault)、`AGENTS.md` / `CLAUDE.md` 一类约定文件、agent 在干活前查阅的 `index.md` 与 `log.md` 工件库、数据团队内的「metadata as code」仓库。但每个实例都是定制的:Karpathy 的 wiki、团队的 wiki、厂商的目录导出看起来都像(markdown + frontmatter + 交叉链接),却没有任何一个被设计来彼此协作。缺少的是「每个文档应携带哪些字段」「哪些文件名意味着什么」的共识。

## 工作方式:一屏看清的设计

OKF **bundle** 是一个由 markdown 文件构成的目录,文件表示 **concept**(任何想捕获的东西:表、数据集、指标、playbook、runbook、API)。每个 concept 一个文件,**文件路径即 concept 的身份**:

```
sales/
├── index.md
├── datasets/
│   ├── index.md
│   └── orders_db.md
├── tables/
│   ├── index.md
│   ├── orders.md
│   └── customers.md
└── metrics/
    ├── index.md
    └── weekly_active_users.md
```

每个 concept 文档有一小块 YAML frontmatter 用于结构化字段,markdown body 承载其余内容:

```yaml
---
type: BigQuery Table
title: Orders
description: One row per completed customer order.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders
tags: [sales, revenue]
timestamp: 2026-05-28T14:30:00Z
---
# Schema
| Column | Type | Description |
|---------------|-----------|------------------------------------------|
| `order_id` | STRING | Globally unique order identifier. |
| `customer_id` | STRING | FK to [customers](/tables/customers.md). |
# Joins
Joined with [customers](/tables/customers.md) on `customer_id`.
```

concept 之间用普通 markdown 链接相互关联,把目录变成一张比文件系统父子关系更丰富的**关系图**。bundle 可选择性地包含 `index.md`(渐进式披露,供 agent 在层级中导航)与 `log.md`(变更的时间序列历史)。完整的 v0.1 规范(含一致性标准、交叉链接规则、少数保留文件名)可放在一页之内。

## 三条设计原则

1. **最小限度的约定(Minimally opinionated)。** OKF 对每个 concept 只硬性要求一个 `type` 字段。其余一切(存在哪些 type、包含哪些字段、body 有哪些 section)留给生产者。规范定义的是互操作面,而非内容模型。
2. **生产者/消费者独立(Producer/consumer independence)。** OKF 清晰地分离「谁写知识」与「谁消费知识」。人手写的 bundle 可被 AI agent 消费;元数据导出流水线生成的 bundle 可在可视化器中浏览;一个 LLM 合成的 bundle 可被另一个 LLM 查询。格式即契约,两端的工具各自可替换。
3. **是格式,不是平台(Format, not platform)。** OKF 不绑定任何特定云、数据库、模型供应商或 agent 框架。读写或服务它永不需要专有账号或 SDK。作为开放标准发布,因为知识格式的价值来自有多少方在说它,而非谁拥有它。

## 随规范一同发布的参考实现

为让格式具体可感,规范同时发布了生产端与消费端的参考实现:

- **enrichment agent**:遍历 BigQuery 数据集,为每张表/视图起草一份 OKF concept 文档,再运行第二轮 LLM pass 爬取权威文档,用引用、schema、join 路径丰富每个 concept。
- **静态 HTML 可视化器**:把任意 OKF bundle 转为单文件交互式图视图,无需后端、无需安装、数据不离开页面。
- **三个可直接浏览的样例 bundle**:[GA4 电商](https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset)、[Stack Overflow](https://console.cloud.google.com/bigquery?ws=!1m4!1m3!3m2!1sbigquery-public-data!2sstackoverflow)、[Bitcoin 公开数据集](https://cloud.google.com/blog/topics/public-datasets/bitcoin-in-bigquery-blockchain-analytics-on-public-data?e=48754805),由参考 agent 生成并提交到仓库,作为合规 OKF 的活样本。

这些是有意为之的概念验证:agent 演示了一种生产 OKF 的方式(格式本身不要求特定 agent 框架或 LLM);可视化器演示了一种消费方式(格式不要求 HTML 或图视图)。生产者与消费者生态被期望远超已发布的内容。

## 后续方向

OKF v0.1 是起点而非完成态。随着更多生产者与消费者出现,以及业界共同摸清 agent 在实践中到底需要怎样的知识表示,格式将持续演进。团队鼓励:阅读规范(很短)、为你的源系统/数据库/文档站点写生产者、写消费者(查看器/搜索索引/基于 bundle 推理的 agent)、用参考实现跑自己的数据、提 issue / 发 PR / 提扩展提案(规范有版本号,并被明确设计为可向后兼容地增长)。Google Cloud 的 [Knowledge Catalog](https://cloud.google.com/blog/products/data-analytics/introducing-the-google-cloud-knowledge-catalog) 也已更新,能够摄取 OKF 并服务给其 agent。

# Citations

- 原文:How the Open Knowledge Format can improve data sharing | Google Cloud Blog(2026-06-12)— https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing
- OKF 规范与样例 bundle 仓库:https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf
- Karpathy LLM Wiki gist:https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Knowledge Catalog 介绍:https://cloud.google.com/blog/products/data-analytics/introducing-the-google-cloud-knowledge-catalog
- 参考实现代码与示例:https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/toolbox/mdcode/demo
