---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T16-compile-time-ops.md
title: inline 与编译期操作
description: inline 关键字保证调用点展开与编译期求值，compiletime.ops 将算术、布尔、字符串操作提升到类型层，实现条件编译与编译期特化。
tags:
- T16
- Scala 3
- vibe-types
- inline
- compiletime
- constValue
- erasedValue
- summonFrom
- 类型级计算
timestamp: '2026-06-24T12:05:39Z'
---

# inline 与编译期操作

## 简介

Scala 3 的 `inline` 关键字是一个软修饰符，**保证**定义在每个调用点被内联——与 Scala 2 中建议性的 `@inline` 注解不同。inline 定义启用编译期求值：`inline val` 产生编译期常量，`inline def` 原地展开，`inline if` 与 `inline match` 要求其条件/scrutinee 在编译期归约，而 `transparent inline` 方法可根据展开结果特化返回类型。`scala.compiletime` 包提供 `constValue`、`erasedValue`、`summonInline`、`summonFrom`、`error` 等操作，以及 `scala.compiletime.ops` 的类型级算术/布尔/字符串操作。

## 可表达的约束

**`inline` 保证代码在调用点展开并在条件为常量时于编译期求值。`compiletime.ops` 将算术、布尔与字符串操作提升到类型层。二者合力实现条件编译、类型级计算与编译期特化——全部由编译器检查，而非推迟到运行时。**

## 最小示例

### inline val 与 inline def

```scala
object Config:
  inline val logging = false

inline def log(msg: String)(op: => Unit): Unit =
  inline if Config.logging then
    println(msg)
    op
  else op

def heavyComputation(): Unit = ()
log("debug") { heavyComputation() }
// 当 logging = false 时，编译为：heavyComputation()
```

### 递归 inline（编译期展开）

```scala
inline def power(x: Double, n: Int): Double =
  if n == 0 then 1.0
  else if n == 1 then x
  else
    val y = power(x, n / 2)
    if n % 2 == 0 then y * y else y * y * x

power(2.0, 10)
// 展开为直线式乘法代码（无循环）
```

### transparent inline（返回类型特化）

```scala
transparent inline def choose(b: Boolean): Any =
  inline if b then "hello" else 42

val x = choose(true)  // 静态类型：String
val y = choose(false) // 静态类型：Int
```

### inline match（类型级分派）

```scala
import scala.compiletime.erasedValue
transparent inline def defaultValue[T] =
  inline erasedValue[T] match
    case _: Int     => Some(0)
    case _: Boolean => Some(false)
    case _          => None

val d: Some[Int]  = defaultValue[Int]    // 类型是 Some[Int]，而非 Option[Int]
val n: None.type  = defaultValue[String]
```

### compiletime.ops（类型级算术）

```scala
import scala.compiletime.ops.int.*
val x: 1 + 2 * 3 = 7 // 类型级计算
val y: S[S[0]]    = 2 // S 是后继：S[0] = 1, S[1] = 2

type Factorial[N <: Int] <: Int = N match
  case 0    => 1
  case S[n] => N * Factorial[n]

val f: Factorial[5] = 120
```

### constValue 与 erasedValue

```scala
import scala.compiletime.{constValue, erasedValue}
import scala.compiletime.ops.int.S
transparent inline def toIntC[N]: Int =
  inline constValue[N] match
    case 0       => 0
    case _: S[n1] => 1 + toIntC[n1]

inline val two = toIntC[2] // 编译期计算出 2
```

### summonInline 与 summonFrom

```scala
import scala.compiletime.{summonInline, summonFrom}
import scala.collection.immutable.{TreeSet, HashSet}

// summonFrom：带回退的函数式隐式搜索
inline def setFor[T]: Set[T] = summonFrom {
  case ord: Ordering[T] => TreeSet.empty[T](using ord)
  case _                => HashSet.empty[T]
}

trait Show[T]:
  def show(x: T): String

// summonInline：带恰当错误信息的延迟 summon
inline def showType[T](x: T): String =
  summonInline[Show[T]].show(x)
```

### compiletime.error

```scala
import scala.compiletime.{error, codeOf}
inline def requirePositive(inline n: Int): Int =
  inline if n <= 0 then error("Expected positive, got: " + codeOf(n))
  else n

requirePositive(-1) // error: Expected positive, got: -1
```

## 与其他特性的交互

| 特性 | 交互 |
|------|------|
| **match 类型**（见 [match-types](match-types.md)） | `inline match` 与 match 类型互补。前者在内联期间于项层求值；后者在类型层计算。可组合：带 `inline match` 的 `transparent inline def`，其返回类型为 match 类型。 |
| **宏（quotes/splices）**（见 [macros-metaprogramming](macros-metaprogramming.md)） | 顶层 splice `${ ... }` 必须出现在 `inline def` 内。inline 是宏展开的入口。 |
| **given 实例**（见 [type-classes](type-classes.md)） | `transparent inline given` 特殊：若内联产生错误，被视为隐式搜索未命中（非硬错误），允许回退到其他候选。 |
| **单例类型** | `inline val` 总有单例字面量类型（如 `inline val x = 4` 类型为 `4`）。`transparent inline` 方法可返回单例类型。参见 [const-generics](const-generics.md)。 |
| **类型类 / 派生**（见 [derivation](derivation.md)） | `summonInline` 与 `summonFrom` 实现带分支消除的编译期类型类分派。 |
| **opaque types**（见 [newtypes-opaque](newtypes-opaque.md)） | 若 opaque 类型别名是常量类型，`constValue` 可从中提取底层字面量。 |
| **erased 定义** | `erasedValue[T]` 假装产生 `T` 类型的值供编译期审视；运行时调用是错误。与 `erased` 参数相关但用途不同。 |

## 注意事项与局限

- **递归深度限制。** 递归 inline 方法默认限制为 32 次连续内联。用 `-Xmax-inlines` 调整。
- **inline 方法必须完全应用。** 缺少参数列表的部分应用（如 `Logger.log("msg", 2)`）是非法的。用通配符参数（`_`）做 eta 展开。
- **inline 方法实际上是 final 的。** 不能被覆盖（除非被其他 inline 方法覆盖）。抽象 inline 方法只能由另一 inline 方法实现，且不能通过动态分派调用。
- **`inline if` / `inline match` 必须归约。** 若条件或 scrutinee 不是编译期常量，编译器报错——而非回退到运行时。
- **`transparent inline` 改变类型行为。** 返回类型可能比声明更具体，若调用方依赖声明类型会导致意外类型不匹配。
- **`compiletime.ops` 要求单例类型。** 类型级操作仅在所有参数为单例类型时求值。非单例参数产生抽象类型，而非错误。
- **`summonFrom` 可能引发歧义错误。** 若多个 given 实例匹配 `summonFrom` 中的某个模式，报告歧义错误。
- **by-name vs inline 参数。** `inline` 参数类似 by-name 但可在展开中重复。按值参数绑定到 `val`；by-name 绑定到 `def`。

## 用例交叉引用

- 编译期配置与条件编译（日志、调试模式），参见 [非法状态不可表示](../usecases/invalid-states.md)。
- 用于定长向量、矩阵维度或有界自然数的类型级算术，参见 [编译期计算](../usecases/compile-time.md)。
- 用 `summonFrom` 进行类型类实例的编译期特化，参见 [相等性](../usecases/equality.md)。
- 递归 inline 用于展开循环或生成特化代码路径，参见 [类型算术](../usecases/type-arithmetic.md)。
- 为非法类型组合生成自定义编译期错误信息，参见 [编译期计算](../usecases/compile-time.md)。
- 通过 `inline def` + `${ ... }` 作为宏定义入口，参见 [编译期计算](../usecases/compile-time.md)。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T16-compile-time-ops.md
