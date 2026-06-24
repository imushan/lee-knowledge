---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T09-dependent-types.md
title: 依赖类型（路径依赖类型与 match 类型）
description: 通过路径依赖类型、match 类型、单例类型与依赖函数类型，将输出类型绑定到输入值或输入类型，在编译期验证两者关系。
tags:
- T09
- Scala 3
- vibe-types
- 依赖类型
- 路径依赖类型
- match 类型
- 单例类型
- 编译期约束
timestamp: '2026-06-24T12:03:30Z'
---

# 依赖类型（路径依赖类型与 match 类型）

## 简介

Scala 3 并不具备 Lean、Idris 或 Agda 意义上的**完全依赖类型**——无法用任意运行时值索引类型，也无法编写关于整数的类型级证明。但 Scala 3 提供了一组特性组合，能够**近似**许多依赖类型的模式：

- **路径依赖类型**（`x.T`）——依赖对象 `x` 的类型。
- **match 类型**——类型级模式匹配，根据输入类型计算结果类型。
- **单例类型**——将字面量值（`42`、`"hello"`）提升到类型层。
- **依赖函数类型**——`(x: A) => x.T`，返回类型依赖参数的路径。
- **inline + compiletime ops**——`constValue`、`constValueTuple`、`erasedValue` 以及对单例类型的算术运算，支持有限的值级计算提升到类型层。

这些特性合在一起，让你可以表达“输出类型依赖输入值（通过路径）或输入类型（通过 match 类型）”这一依赖类型核心理念，同时受限于 JVM 擦除。

## 可表达的约束

**Scala 的依赖类型近似让你把输出类型绑定到输入值（通过路径）或输入类型（通过 match 类型），从而让编译器验证那些在其他语言中需要完全依赖类型系统才能成立的关系——但受限于 JVM 运行时擦除。**

## 最小示例

```scala
// 路径依赖：返回类型依赖参数
trait Key:
  type Value
val age: Key { type Value = Int } = new Key { type Value = Int }
val name: Key { type Value = String } = new Key { type Value = String }
def get(k: Key): k.Value = ??? // 依赖方法类型

// match 类型：根据输入类型计算输出类型
type Unpacked[T] = T match
  case Option[t] => t
  case List[t]   => t
  case _         => T
val x: Unpacked[Option[Int]] = 42 // Int
val y: Unpacked[String]      = "hello" // String

// 单例类型 + compiletime：类型级算术
import scala.compiletime.ops.int.*
type Three = 3
type Four  = 4
type Seven = Three + Four // 类型级 7
val seven: Seven = 7 // 只接受 7
```

## 可做与不可做

| 模式 | Scala 3 支持度 | 与 Lean / Idris 对比 |
|------|----------------|----------------------|
| 返回类型依赖参数的类型成员 | 路径依赖类型——完全支持 | N/A（机制不同） |
| 通过对类型做模式匹配选择类型 | match 类型——完全支持 | 类似 type families |
| 定长向量 `Vec[N, A]` | 单例类型 + match 类型——部分支持（无法对值归纳，须用类型级 Nat 或字面量 Int） | Nat 索引向量，带完整证明 |
| 关于算术的证明（如 `n + m == m + n`） | 不支持——无证明项、无依赖消去 | 核心能力 |
| 精化谓词（如 `{x: Int | x > 0}`） | 无内建精化类型（可用 opaque types + 智能构造器绕过） | 通过 propositions-as-types 支持 |
| 类型安全的 printf | 基于单例字符串类型的 match 类型——可行但脆弱 | 依赖类型下直观 |

## 与其他特性的交互

| 特性 | 组合方式 |
|------|----------|
| **路径依赖类型**（见 [path-dependent-types](path-dependent-types.md)） | 值依赖类型的主要机制。方法 `def f(k: Key): k.Value` 是依赖方法——返回类型依赖参数。 |
| **match 类型**（见 [match-types](match-types.md)） | 提供类型级计算：给定类型，计算另一类型。这是 Scala 最接近 type families 或类型级函数的方式。 |
| **字面量/单例类型**（见 [literal-types](literal-types.md)） | 将值提升为类型（`42` 变为类型 `42`）。对类型级算术与 const-generics 风格模式至关重要。 |
| **编译期操作**（见 [const-generics](const-generics.md)） | `scala.compiletime.ops` 提供对单例类型的类型级算术：`+`、`*`、`<` 等，是 Scala 对带算术的 const generics 的等价物。 |

## 注意事项与局限

1. **无值索引类型。** 无法写 `Vec(n, A)`，其中 `n` 是运行时 `Int`。必须用单例类型（`val n: 3 = 3`）或 opaque 编码。真正的运行时依赖类型超出 Scala 类型系统能力。
2. **match 类型可能卡住。** 当 scrutinee 抽象时，编译器无法归约 match 类型，限制了类型级计算跨泛型边界的可组合性。
3. **无证明项。** Scala 没有 Lean 的 `Prop` 或 Idris 的 `=` 类型的等价物，无法构造或模式匹配类型等式或算术性质的证明。
4. **擦除。** 所有这些类型级技巧在运行时被擦除。`Vec[3, Int]` 与 `Vec[5, Int]` 在 JVM 层是同一类型。运行时检查需要显式证据（如 `TypeTest`）。
5. **路径稳定性。** 只有稳定路径（`val`、`object`、`this`）可出现在依赖类型中。`def` 或 `var` 的结果不是稳定路径，因此 `def getKey: Key` 不允许在其结果上依赖类型。
6. **有限的类型级递归。** 递归 match 类型可能发散。编译器有递归限制，且无法证明一般性终止。

## 用例交叉引用

- 路径依赖类型与单例类型可在编译期阻止无效键值组合，参见 [非法状态不可表示](../usecases/invalid-states.md)。
- match 类型与 compiletime ops 将计算前移到编译期，在运行前捕获错误，参见 [编译期计算](../usecases/compile-time.md)。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T09-dependent-types.md
- [Scala 3 Reference — Match Types](https://docs.scala-lang.org/scala3/reference/new-types/match-types.html)
- [Scala 3 Reference — Dependent Function Types](https://docs.scala-lang.org/scala3/reference/new-types/dependent-function-types.html)
- [Scala 3 Reference — Literal Types](https://docs.scala-lang.org/scala3/reference/new-types/literal-types.html)
- [Scala 3 Reference — compiletime Operations](https://docs.scala-lang.org/scala3/reference/metaprogramming/compiletime-ops.html)
