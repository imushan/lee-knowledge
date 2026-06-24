---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC18-type-arithmetic.md
title: 类型级算术（UC18）
description: 使用 compiletime.ops 与匹配类型在编译期执行数值计算并强制数值约束。
tags:
- 类型级算术
- compiletime-ops
- 匹配类型
- singleton
- constValue
- Peano
- UC18
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:09:07Z'
---

# 类型级算术（UC18）

## 约束目标

在编译期执行数值计算并强制数值约束。维度不匹配、越界索引、非法尺寸等成为编译错误，而非运行时异常。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| Compiletime ops | 基于单例 `Int` 类型的类型级 `+`、`-`、`*`、`/`、`<`、`>=` | [T16 compile-time-ops](../catalog/compile-time-ops.md) |
| 匹配类型 | 递归的类型级计算（Peano 编码、类型级列表） | [T41 match-types](../catalog/match-types.md) |
| Inline / constValue | 强制编译期求值；将单例类型提取为值 | [T16 compile-time-ops](../catalog/compile-time-ops.md) |
| 单例类型 | 如 `3`、`true` 等字面量类型，将值带入类型系统 | — |
| 宏 | 超出 `compiletime.ops` 能力时的逃生舱 | [T17 macros-metaprogramming](../catalog/macros-metaprogramming.md) |

## 模式

### 模式 1：用 `scala.compiletime.ops.int` 表达类型级算术

直接在类型中用 `scala.compiletime.ops.int` 表达约束。

```scala
import scala.compiletime.ops.int.*
type Positive[N <: Int] = N > 0 =:= true
def posOnly[N <: Int & Singleton](n: N)(using Positive[N]): N = n

val ok = posOnly(5) // compiles — 5 > 0 is true
// val no = posOnly(-1) // compile error — -1 > 0 is false
```

### 模式 2：类型安全的向量维度

将长度编码进类型，在编译期拒绝维度不匹配的操作。

```scala
import scala.compiletime.ops.int.*
final class Vec[N <: Int](val data: Array[Double]):
  def length: N = data.length.asInstanceOf[N]
  infix def dot(that: Vec[N]): Double =
    data.zip(that.data).map(_ * _).sum
  def concat[M <: Int](that: Vec[M]): Vec[N + M] =
    Vec(data ++ that.data)

val v3: Vec[3] = Vec(Array(1.0, 2.0, 3.0))
val v2: Vec[2] = Vec(Array(4.0, 5.0))
val v5: Vec[5] = v3.concat(v2) // compiles — 3 + 2 = 5
v3.dot(v3) // compiles — both Vec[3]
// v3.dot(v2) // compile error — Vec[3] vs Vec[2]
```

### 模式 3：用匹配类型递归实现 Peano 式编码

当 `compiletime.ops` 不足时，将自然数建模为类型。

```scala
sealed trait Nat
sealed trait Zero extends Nat
sealed trait Succ[N <: Nat] extends Nat

type NatToInt[N <: Nat] <: Int = N match
  case Zero => 0
  case Succ[n] => scala.compiletime.ops.int.+[NatToInt[n], 1]

type Two = Succ[Succ[Zero]]
type Three = Succ[Succ[Succ[Zero]]]
summon[NatToInt[Two] =:= 2]
summon[NatToInt[Three] =:= 3]

type NatPlus[A <: Nat, B <: Nat] <: Nat = A match
  case Zero => B
  case Succ[a] => Succ[NatPlus[a, B]]
summon[NatPlus[Two, Three] =:= Succ[Succ[Succ[Succ[Succ[Zero]]]]]]
```

### 模式 4：用 `constValue` 提取编译期数值

使用 `constValue` 和 `constValueTuple` 桥接类型层与值层。

```scala
import scala.compiletime.{constValue, constValueTuple}
import scala.compiletime.ops.int.*

inline def dimensionOf[N <: Int]: Int = constValue[N]
val n: 5 = constValue[5] // returns the literal 5

inline def describe[N <: Int]: String =
  inline constValue[N < 0] match
    case true => "negative"
    case false =>
      inline constValue[N] match
        case 0 => "zero"
        case _ => "positive"

val s: String = describe[3] // "positive" — resolved at compile time
// describe[-1] // "negative"
// describe[0] // "zero"
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 类型级数字 | Shapeless `Nat` 等 Church/Peano 编码库；编译慢、范围有限 | `compiletime.ops.int`——内建于编译器，快速，直接作用于 `Int` 字面量 |
| 维度检查 | Shapeless `Sized` 或自定义幻影类型；冗长脆弱 | 单例 `Int` 类型 + `ops.int`——简洁、一等 |
| 编译期提取 | Shapeless `Witness` / `nat.toInt` 宏——复杂 | `constValue[N]`——一次调用，除 `compiletime` 外无需额外导入 |
| 递归计算 | 通过隐式与 `Aux` 模式的类型级编程；难调试 | 匹配类型——类型层面的模式匹配，可读、由编译器支持 |

## 何时选择哪个特性

- **默认使用 `compiletime.ops.int`** 处理直接的算术约束（边界检查、维度匹配、容量限制）。它覆盖 `+`、`-`、`*`、`/`、`%`、`<`、`>`、`<=`、`>=`，且编译高效。
- **使用匹配类型** 进行递归或结构化计算（例如计算 HList 长度、展平嵌套元组）。匹配类型读起来像值层面的模式匹配。
- **使用 Peano 编码** 仅当需要归纳证明或递归无法映射到 `Int` 算术时（例如类型级列表、平衡树）。
- **求助于宏** 当需要引用领域术语的错误消息（"矩阵维度 3x4 与 5x2 不兼容"），或计算超出 `compiletime.ops` 支持时。
- **使用 `constValue` / `constValueTuple`** 在编译期常量需要流入运行时代码时跨越类型-值边界。

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC18-type-arithmetic.md
