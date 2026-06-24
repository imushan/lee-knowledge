---
type: Concept
resource: https://github.com/jpablo/vibe-types/tree/main/plugin/skills/scala3
title: vibe-types：Scala 3 编译期约束指南
description: 将 Scala 3 每个类型系统特性映射到它在编译期能强制的约束与属性的穷尽参考：核心原则、特性目录（catalog）与用例索引（use
  cases）的导航总览。
tags:
- Scala 3
- vibe-types
- 类型系统
- 编译期约束
- 类型安全
- 总览
- 导航
timestamp: '2026-06-24T12:11:40Z'
---

# vibe-types：Scala 3 编译期约束指南

本指南源自 [vibe-types](https://github.com/jpablo/vibe-types) 项目的 Scala 3 技能，是一份**穷尽性参考**：把 Scala 3 的每一个类型系统特性映射到它在编译期能强制（enforce）的约束与属性。读者对象是有经验的 Scala 开发者，目标是回答两个互逆的问题——

- **给定某个特性，它能表达什么约束？** → 见 [第一部分：特性目录](#第一部分特性目录-feature-catalog)
- **我想在编译期强制某个属性，该用哪些特性？** → 见 [第二部分：用例索引](#第二部分用例索引-use-case-index)

> 核心立场：**让类型检查器承担尽可能多的正确性证明。** 把保证从运行时检查、测试和纪律中迁移到类型里，使得「持有一个值」本身就是其不变量成立的证据。这些是带判断运用的默认原则，而非绝对教条。

## 与本库其他 Scala 3 文档的关系

本指南与 [Scala 3 完整学习指南](scala3_complete_guide.md)、[Scala 3 上下文抽象与现代架构设计指南](scala3_context_abstraction.md) 互补：那两篇是系统学习与架构视角，本篇是「特性 × 约束」的索引化参考手册，所有细节沉淀在 [references/scala3/catalog/](../../references/scala3/catalog/) 与 [references/scala3/usecases/](../../references/scala3/usecases/) 两个参考树中。

## 核心原则

- **让非法状态不可表达（Make illegal states unrepresentable）。** 对数据建模，使得非法的值组合根本无法通过类型检查，而非事后检查。 → [屏蔽非法状态](../../references/scala3/usecases/invalid-states.md)
- **解析而非校验（Parse, don't validate）。** 在边界处把一次检查转化为一个**细化类型**的值，该值证明检查已经发生过，而不是返回布尔值再丢弃获得的信息。 → [细化类型](../../references/scala3/catalog/refinement-types.md)
- **保留函数式内核，命令式外壳。** 决策与计算放进取值、返回值的纯函数里；把副作用（IO、网络、数据库、时钟、随机性）推到一层薄外壳。内核确定性、易测试。 → [效果追踪](../../references/scala3/usecases/effect-tracking.md)
- **在边界升级信息，内核不再重新获取。** 每次解析、检查或分支都获得信息——在边界用类型捕获它并向内传递，内核依赖已有证据而非重新校验。 → [Witness 与 Evidence 类型](../../references/scala3/catalog/witness-evidence.md)
- **优先选择更精确的类型。** 一个类型越精确，其居民（inhabitants）越贴合合法取值：在所有能表示每个合法值的类型中，选择居民最少的那个，因为多出的居民恰好就是不该出现的值。`Bool` 比 `Int` 精确；封闭枚举比 `String` 精确；`NonEmptyList` 比 `List` 精确；newtype 让 `UserId` 与 `OrderId` 即便底层相同也无法互换。 → [不透明类型](../../references/scala3/catalog/newtypes-opaque.md)
- **在错值会造成实质伤害处增加精度，低风险处保持朴素。** 引入精确类型有摩擦成本：当错值会无声通过、代价高昂（金钱、权限、数据丢失）、跨越边界（不可信输入、公共 API、需持久化或传输）、或在远离首次确立处被多处依赖时，才值得引入。一次性、局部、从不分支、错了也明显无害的值，保持朴素即可。
- **优先用类型而非测试捕获不变量。** 编译器能强制的属性就不要写测试；把测试留给类型无法表达的行为。
- **让函数全，让编译器强迫覆盖每个分支。** 全函数对参数类型允许的每个输入都有定义：要么拓宽输出（返回 `Option`/`Result`，让「无答案」成为调用方必须处理的情形），要么收窄输入（如取 `NonEmptyList` 使 `head` 永远有答案）。匹配时覆盖每个构造器，除非集合真正开放，否则避免 catch-all，使后续新增变体成为编译错误而非静默穿透。对确不可达的分支，用空类型（Scala 中为 `Nothing`）的值关闭它，证明该分支不可达，而非抛「不可能发生」的异常。 → [穷尽匹配](../../references/scala3/usecases/exhaustiveness.md)、[Nothing 与底类型](../../references/scala3/catalog/never-bottom.md)
- **让不可变性成为默认，把可变标记为例外。** 构造后不可变的值不会在背书它的检查背后悄悄变非法。要求显式、可见的标记才能选择可变或共享别名。 → [不可变性标记](../../references/scala3/catalog/immutability-markers.md)
- **适当时使用状态机。** 当对象有生命周期或协议时，把状态编码为类型，使非法迁移不通过编译。 → [协议状态机](../../references/scala3/usecases/state-machines.md)
- **把权限作为类型化值传递，而非伸手拿环境式能力。** 「做某件强大或带副作用之事的权利」本身是一个值：需要文件系统、网络、时钟、随机源、环境变量、密钥、子进程、转账权限时，应作为参数接收，而非调用全局或单例。函数类型不声明某项权限，就无法使用它；调用方决定传入什么，测试时换一个值即可。 → [捕获检查与 CanThrow](../../references/scala3/catalog/effect-tracking.md)

## 第一部分：特性目录（Feature Catalog）

按特性组织。每篇回答：「这个特性能强制什么？」目录文档遵循统一模板——版本注解、定义、可表达的约束、最小示例、与其他特性的交互、注意事项与局限、用例交叉引用。

| # | 特性 | 文档 |
|----|------|------|
| T01 | 枚举与代数数据类型（enum / ADT / GADT） | [代数数据类型](../../references/scala3/catalog/algebraic-data-types.md) |
| T02 | 联合类型与交叉类型（`A \| B`、`A & B`） | [联合与交叉类型](../../references/scala3/catalog/union-intersection.md) |
| T03 | 不透明类型（opaque type） | [不透明类型](../../references/scala3/catalog/newtypes-opaque.md) |
| T04 | 泛型与有界多态（上/下界、context bound、F-有界） | [泛型与界](../../references/scala3/catalog/generics-bounds.md) |
| T05 | 类型类（given / using / given import） | [类型类](../../references/scala3/catalog/type-classes.md) |
| T06 | 类型类派生（derives、Mirror） | [类型类派生](../../references/scala3/catalog/derivation.md) |
| T07 | 结构类型与细化类型、命名元组 | [结构类型](../../references/scala3/catalog/structural-typing.md) |
| T08 | 变型与子类型（协变 `+A`、逆变 `-A`） | [变型与子类型](../../references/scala3/catalog/variance-subtyping.md) |
| T09 | 依赖类型（路径依赖 + match 类型） | [依赖类型](../../references/scala3/catalog/dependent-types.md) |
| T12 | 捕获检查与 CanThrow | [效果追踪（捕获检查）](../../references/scala3/catalog/effect-tracking.md) |
| T13 | 显式 null（`T \| Null`） | [显式 null](../../references/scala3/catalog/null-safety.md) |
| T14 | Matchable 与 TypeTest | [类型收窄](../../references/scala3/catalog/type-narrowing.md) |
| T15 | 单例类型与编译期值参数 | [const generics](../../references/scala3/catalog/const-generics.md) |
| T16 | inline 与 compiletime 操作 | [inline 与编译期操作](../../references/scala3/catalog/compile-time-ops.md) |
| T17 | 宏（quotes & splices） | [宏与元编程](../../references/scala3/catalog/macros-metaprogramming.md) |
| T18 | 隐式转换、by-name 上下文参数、deferred givens | [转换与强制](../../references/scala3/catalog/conversions-coercions.md) |
| T19 | 扩展方法 | [扩展方法](../../references/scala3/catalog/extension-methods.md) |
| T20 | 多元宇宙相等性（CanEqual） | [相等性安全](../../references/scala3/catalog/equality-safety.md) |
| T21 | open、export、transparent | [封装修饰符](../../references/scala3/catalog/encapsulation.md) |
| T22 | 可调用类型与重载 | [可调用类型](../../references/scala3/catalog/callable-typing.md) |
| T23 | 类型别名（透明别名、参数化别名、类型成员） | [类型别名](../../references/scala3/catalog/type-aliases.md) |
| T25 | 连贯性与实例作用域（given import 规则，无孤儿规则） | [连贯性与孤儿规则](../../references/scala3/catalog/coherence-orphan.md) |
| T26 | 细化类型（Iron / refined 库） | [细化类型](../../references/scala3/catalog/refinement-types.md) |
| T27 | 抹除定义（erased） | [抹除定义](../../references/scala3/catalog/erased-phantom.md) |
| T31 | 记录类型与数据建模（case class、命名元组） | [记录类型](../../references/scala3/catalog/record-types.md) |
| T32 | 不可变性标记（val、final、sealed） | [不可变性标记](../../references/scala3/catalog/immutability-markers.md) |
| T33 | 自身类型（`self: T =>`） | [自身类型](../../references/scala3/catalog/self-type.md) |
| T34 | Nothing 与底类型 | [Nothing 与底类型](../../references/scala3/catalog/never-bottom.md) |
| T35 | Kind 多态（AnyKind） | [Kind 多态](../../references/scala3/catalog/universes-kinds.md) |
| T36 | 基于 trait 的动态分派（JVM vtable） | [Trait 与动态分派](../../references/scala3/catalog/trait-objects.md) |
| T37 | given / 隐式解析（trait solver） | [Given 解析](../../references/scala3/catalog/trait-solver.md) |
| T39 | 注解与编译器指令（`@inline`、`@tailrec`、`@targetName`） | [注解与指令](../../references/scala3/catalog/notation-attributes.md) |
| T40 | 类型 Lambda 与高阶类型 | [类型 Lambda](../../references/scala3/catalog/type-lambdas.md) |
| T41 | Match 类型 | [Match 类型](../../references/scala3/catalog/match-types.md) |
| T42 | 上下文函数与 context bounds（`T ?=> U`） | [上下文函数](../../references/scala3/catalog/context-functions.md) |
| T43 | 实验/预览：命名类型参数、`into`、模块化 | [实验与预览特性](../../references/scala3/catalog/experimental-preview.md) |
| T44 | 变更与移除的特性（Scala 2 迁移） | [变更与移除特性](../../references/scala3/catalog/changed-dropped.md) |
| T49 | 关联类型（trait 中的抽象类型成员） | [关联类型](../../references/scala3/catalog/associated-types.md) |
| T52 | 字面量类型 | [字面量类型](../../references/scala3/catalog/literal-types.md) |
| T53 | 路径依赖与多态函数类型 | [路径依赖类型](../../references/scala3/catalog/path-dependent-types.md) |
| T54 | Functor / Applicative / Monad | [Functor/Applicative/Monad](../../references/scala3/catalog/functor-applicative-monad.md) |
| T55 | Monad 变换器（EitherT、StateT、ReaderT） | [Monad 变换器](../../references/scala3/catalog/monad-transformers.md) |
| T56 | Tagless Final | [Tagless Final](../../references/scala3/catalog/tagless-final.md) |
| T57 | Typestate 模式（phantom 类型追踪状态） | [Typestate](../../references/scala3/catalog/typestate.md) |
| T58 | Witness 与 evidence 类型（`=:=`、`<:<`） | [Witness 与 Evidence](../../references/scala3/catalog/witness-evidence.md) |
| T59 | 存在类型 | [存在类型](../../references/scala3/catalog/existential-types.md) |
| T61 | 递归类型 | [递归类型](../../references/scala3/catalog/recursive-types.md) |

## 第二部分：用例索引（Use-Case Index）

按约束组织。每篇回答：「我想让编译器强制 X——哪些特性有帮助，怎么用？」每篇包含约束目标、特性工具箱、2–4 个最小模式、Scala 2 对比与选择决策。

| # | 约束 | 文档 |
|----|------|------|
| UC01 | 屏蔽非法状态（让非法状态不可表达） | [屏蔽非法状态](../../references/scala3/usecases/invalid-states.md) |
| UC02 | 领域建模（精确领域类型） | [领域建模](../../references/scala3/usecases/domain-modeling.md) |
| UC03 | 穷尽匹配（全函数，覆盖每个分支） | [穷尽匹配](../../references/scala3/usecases/exhaustiveness.md) |
| UC04 | 泛型约束 | [泛型约束](../../references/scala3/usecases/generic-constraints.md) |
| UC05 | 结构化契约（静态检查的鸭子类型） | [结构化契约](../../references/scala3/usecases/structural-contracts.md) |
| UC06 | 不可变性 | [不可变性](../../references/scala3/usecases/immutability.md) |
| UC07 | 可调用契约 | [可调用契约](../../references/scala3/usecases/callable-contracts.md) |
| UC08 | 错误处理（checked exception、错误 ADT） | [错误处理](../../references/scala3/usecases/error-handling.md) |
| UC09 | DSL 与构建器模式（流式 API、phantom 类型） | [DSL 与构建器](../../references/scala3/usecases/builder-config.md) |
| UC10 | 访问与封装 | [访问与封装](../../references/scala3/usecases/encapsulation.md) |
| UC11 | 效果追踪（IO、异常、变异提到类型层） | [效果追踪](../../references/scala3/usecases/effect-tracking.md) |
| UC12 | 编译期编程 | [编译期编程](../../references/scala3/usecases/compile-time.md) |
| UC13 | 协议与状态机（强制调用顺序、session 类型） | [协议状态机](../../references/scala3/usecases/state-machines.md) |
| UC14 | 扩展性（开/闭扩展点） | [扩展性](../../references/scala3/usecases/extensibility.md) |
| UC15 | 相等性与比较（类型安全的相等） | [相等性](../../references/scala3/usecases/equality.md) |
| UC16 | 可空性与可选性（null 安全） | [可空性](../../references/scala3/usecases/nullability.md) |
| UC17 | 变型与子类型（协变、逆变、界） | [变型](../../references/scala3/usecases/variance.md) |
| UC18 | 类型级算术（编译期数值约束） | [类型级算术](../../references/scala3/usecases/type-arithmetic.md) |
| UC19 | 序列化编解码器（派生序列化器、schema 安全） | [序列化编解码](../../references/scala3/usecases/serialization.md) |
| UC21 | 并发（经库：ZIO、Cats Effect、Akka Typed、Ox） | [并发](../../references/scala3/usecases/concurrency.md) |

## 交叉引用记号

- `[-> catalog/Tnn]` 指向特性目录条目 nn（例如 T03 → 不透明类型）。
- `[-> UC-nn]` 指向用例索引条目 nn。
- 每篇特性文档末尾有用例交叉引用；每篇用例文档回链相关特性。

## Scala 版本覆盖

每篇特性文档含版本注解，标注引入该特性的 Scala 3.x 版本。本指南当前覆盖至 **Scala 3.8**。变更历史见上游 [CHANGELOG](https://github.com/jpablo/vibe-types/blob/main/CHANGELOG.md)。

# 引用

- 上游技能目录：https://github.com/jpablo/vibe-types/tree/main/plugin/skills/scala3
- README：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/README.md
- SKILL 定义：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/SKILL.md
- 特性目录阅读指南：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/00-overview.md
- 用例索引导航：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/00-overview.md
