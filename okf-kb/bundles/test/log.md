# Bundle Update Log


## 2026-07-02

* **Creation**: 新增概念文档「六边形架构与 Scala 3 类型类融合设计蓝图」：用 Typeclass 定义微端口、given 实例做适配器、extension 让领域模型在服务中穿梭的弹性六边形架构设计。


## 2026-06-29

* **Update**: 将 bleep 脚本簇的 4 份原料（README + 3 份设计文档）钉死到原料层 sources/articles/（bleep-scripts-readme / bleep-mcp-setup-design / bleep-link-vite-design / bleep-custom-dist-design），并把对应 4 份概念文档的 resource 指向这些落盘副本、Citations 补注钉死位置。
* **Creation**: 新增 bleep 构建工具脚本簇：1 个概念（BleepScript 共性姿势）+ 3 个参考（mcp-setup / link-vite / custom-dist），置于新建的 tooling/ 子目录；并 augment scalasemantic-mcp 概念，新增「bleep 项目配置」一节并交叉链接到 bleep-mcp-setup。
* **Creation**: 新增 ScalaSemantic 概念文档，介绍通过 SemanticDB 和 MCP 协议让 AI 助手访问 Scala 编译器语义信息的技术。


## 2026-06-25

* **Update**: 增强「捕获检查」与「分离检查」概念文档：补充捕获类型语法、引用透明 map 示例、别名追踪、设计动机说明，添加 VirtusLab 文章引用
* **Creation**: 创建分离检查（Separation Checking）概念文档，基于 Scala 3 的 Capture Checking 扩展，介绍 SharedCapability、ExclusiveCapability、移动语义和消费参数等核心概念。


## 2026-06-24

* **Creation**: 引入 vibe-types Scala 3 编译期约束指南：新增 1 篇总览概念（concepts/scala3/vibe_types_guide）、47 篇特性目录参考（references/scala3/catalog/）、20 篇用例索引参考（references/scala3/usecases/），全部简体中文、含文件相对路径交叉链接。
* **Update**: 将两个 Scala 3 概念文档迁入 concepts/scala3/ 子目录，便于主题归类（move_concept 自动重写交叉链接）。
* **Update**: 将概念 concepts/scala3_context_abstraction 迁移至 concepts/scala3/scala3_context_abstraction（重写 6 处链接）。
* **Update**: 将概念 concepts/scala3_complete_guide 迁移至 concepts/scala3/scala3_complete_guide（重写 6 处链接）。
* **Creation**: 新增两个 Scala 3 概念文档：Scala 3 完整学习指南、Scala 3 上下文抽象与现代架构设计指南（来源 imushan/scala-learning/notes）。
* **Creation**: 新建概念文档 concepts/open_knowledge_format,概述 Google Cloud 的 OKF 开放规范(动机、bundle 设计、三条原则、参考实现),采自同名博客文章。
