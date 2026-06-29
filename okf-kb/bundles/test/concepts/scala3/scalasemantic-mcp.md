---
type: Concept
resource: https://medium.com/@victorkalinin/it-hurts-to-watch-an-ai-grep-my-scala-scalasemantic-99474ab37cd7
title: ScalaSemantic：让 AI 理解 Scala 编译器语义
description: 通过 SemanticDB 和 MCP 协议让 AI 助手访问 Scala 编译器的符号解析、类型推断和引用关系数据，替代 grep 文本匹配实现精确语义查询。
tags:
- Scala
- SemanticDB
- MCP
- AI
- 编译器
- 符号解析
- 类型推断
- bleep
timestamp: '2026-06-29T12:30:54Z'
---

# 核心问题

AI 助手（如 Claude）在分析 Scala 代码时常依赖 grep 文本搜索，这会导致：

- **漏匹配**：重命名导入、推断类型、隐式转换的引用无法通过文本匹配找到
- **过度匹配**：同名方法、注释、字符串中的文本全部返回，噪声累积消耗 token
- **上下文浪费**：每次查询都打开多个文件，结果可能仍是错的

实测中语义查询结果比 grep 结果小 **8×**，且零错误匹配。

# 解决方案

ScalaSemantic 让 AI 直接访问编译器已知的语义信息（SemanticDB），而非猜测文本匹配：

| grep | 编译器语义 |
|------|----------|
| 匹配字符 | 理解符号 |
| 同名全返回 | 区分不同定义 |
| 漏掉隐式/推断 | 解析后符号图 |
| 噪声消耗 token | 精确最小答案 |

# 核心概念

## SemanticDB

编译器在构建时输出的语义数据库，包含：

- **符号**（symbol）：方法/类/字段的完整标识符（含 owner 和 descriptor）
- **引用**（reference）：每个引用指向的具体符号
- **类型**：推断类型、签名
- **合成代码**：编译器插入的隐式转换、派生代码

## Presentation Compiler

Metals 使用的实时编译器，可理解未编译的当前缓冲区文本。用于：

- 鼠标悬停信息
- 代码补全
- 跳转到定义

ScalaSemantic 使用它处理刚编辑但未重新构建的代码。

## MCP（Model Context Protocol）

给 AI 助手提供额外工具的标准协议。AI 通过 JSON-RPC 调用工具，获取结构化结果。

# 工具列表

ScalaSemantic 提供的语义查询工具：

| 工具 | 功能 |
|------|------|
| `find_symbol` | 解析人类可读名称到 SemanticDB 符号 |
| `find_usages` | 返回精确符号的所有出现 |
| `method_signature` | 渲染编译器记录的签名 |
| `class_hierarchy` | 从符号图导出继承关系 |
| `members` | 类/trait 的成员列表 |
| `call_path` | 调用链分析 |
| `resolve_implicits` | 显示编译器插入的隐式转换 |
| `trace_implicit_chain` | 追踪隐式链 |
| `annotated_source` | 带推断信息注释的源码 |
| `type_at_position` | 获取位置处的精确类型 |

# 工作流程

典型查询流程（先解析后查询）：

1. `find_symbol("Service.run")` → 获得 SemanticDB 符号
2. `find_usages(symbol)` → 返回精确调用者（不是所有 "run" 文本）

# 响应压缩

默认返回压缩格式以节省 token：

- 位置：`uri:line:col`
- 签名：单行渲染
- 空字段：省略

可请求扩展：`detailed` 返回结构化字段，`include` 选择结果部分，`find_usages` 支持 `limit/offset` 分页。

# 初始化与进程边界

MCP 客户端通过 stdio 启动 ScalaSemantic 作为独立 JVM 进程，使用 JSON-RPC 通信。

**stdout 必须纯净**：日志和诊断写入 stderr，因为 stdout 是协议传输通道。一行杂乱日志可破坏协议流。

# sbt 项目配置

```scala
// 添加插件
addSbtPlugin("io.github.mercurievv" % "sbt-scalasemantic-mcp" % "x.y.z")

// 启用
enablePlugins(ScalaSemanticMcpPlugin)
```

```bash
# 构建 + 获取客户端配置
sbt compile
sbt mcpClientConfig  # 默认输出 Claude 风格 .mcp.json
```

其他客户端：`mcpClient := "codex"`

# bleep 项目配置

ScalaSemantic 服务器**构建工具无关**（只读磁盘上的 `.semanticdb`），sbt 插件并非特殊通道。因此 **bleep 项目**没有 sbt 插件也能接入——只需：

1. 在 `bleep.yaml` 加 `-Xsemanticdb -sourceroot`，让 `bleep compile` 产出 `META-INF/semanticdb/*.semanticdb`。
2. 用一个 BleepScript 复刻 sbt 插件的编排逻辑：装官方 launcher、prefetch jar、合并写 `.mcp.json`。

这是一条命令 `bleep mcp-setup`，具体实现见 [bleep mcp-setup 脚本](../../references/scala3/tooling/bleep-mcp-setup.md)。BleepScript 的共性写法见 [BleepScript 复用脚本姿势](tooling/bleep-scripts.md)。

# 局限性

- **数据时效性**：SemanticDB 反映最后构建状态，代码变更后需重新编译
- **纯文本不支持**：注释、任意文本仍需 grep
- **Presentation Compiler 覆盖有限**：部分工具尚未使用实时编译器路径

# 相关概念

- [bleep mcp-setup 脚本：接入 ScalaSemantic MCP](../../references/scala3/tooling/bleep-mcp-setup.md) - 在 bleep 项目里一键接入本服务器的实现
- [BleepScript 复用脚本姿势](tooling/bleep-scripts.md) - bleep 项目自动化的统一模式
- [上下文函数与 Context Bounds](../../references/scala3/catalog/context-functions.md) - Scala 3 隐式参数机制
- [类型类派生](../../references/scala3/catalog/derivation.md) - 编译器自动生成实例
- [隐式解析](../../references/scala3/catalog/trait-solver.md) - given 搜索算法

# Citations

- Victor Kalinin, "It Hurts to Watch an AI 'grep' My Scala | ScalaSemantic", Medium, 2026-06-25
  https://medium.com/@victorkalinin/it-hurts-to-watch-an-ai-grep-my-scala-scalasemantic-99474ab37cd7
