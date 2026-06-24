---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC15-equality.md
title: 相等性与比较（UC15）
description: 通过 Scala 3 的多宇宙相等性（multiversal equality）在编译期阻止无意义的相等比较。
tags:
- 相等性
- CanEqual
- strictEquality
- UC15
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:07:56Z'
---

# 相等性与比较（UC15）

## 约束目标

**在编译期阻止无意义的相等比较。**

在标准 Scala（以及 Java）中，任意两个值都可以用 `==` 比较，哪怕这种比较永远不可能为 `true`——例如 `42 == "hello"` 或 `Option(1) == List(1)`。Scala 3 的多宇宙相等性（multiversal equality）将这类比较变为编译错误，强制开发者显式声明哪些类型对之间可以进行合法比较。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 多宇宙相等性 | `strictEquality` 语言导入使 `==` 和 `!=` 要求存在 `CanEqual` 实例 | [T20 equality-safety](../catalog/equality-safety.md) |
| CanEqual | 编译器查找的类型类，用于允许两个类型之间的 `==` | [T20 equality-safety](../catalog/equality-safety.md) |
| Enums / ADTs | 在 enum 上 `derives CanEqual` 可为所有分支生成实例 | [T01 algebraic-data-types](../catalog/algebraic-data-types.md) |
| Opaque types | opaque type 是独立类型；在严格相等下拥有自己的相等性域 | [T03 newtypes-opaque](../catalog/newtypes-opaque.md) |

## 模式

### 模式 A：启用 `strictEquality`

通过编译器选项全项目开启，或通过 import 在单文件内开启。之后，比较不相关类型将报错。

```scala
import scala.language.strictEquality
val x: Int = 42
val s: String = "hello"
// x == s // error: Values of types Int and String cannot be compared with == or !=
x == 42 // ok: same type
```

等价的编译器选项为 `-language:strictEquality`。

### 模式 B：为 ADT 派生 `CanEqual`

在 enum 或 sealed 层级上使用 `derives CanEqual`，允许其成员之间进行比较。

```scala
import scala.language.strictEquality
enum Color derives CanEqual:
  case Red, Green, Blue

val a: Color = Color.Red
val b: Color = Color.Blue
a == b // ok: CanEqual[Color, Color] is derived
// a == 42 // error: Values of types Color and Int cannot be compared
```

对于 sealed trait 层级，在父类型上派生：

```scala
sealed trait Shape derives CanEqual
case class Circle(r: Double) extends Shape
case class Rect(w: Double, h: Double) extends Shape
Circle(1.0) == Rect(2.0, 3.0) // ok: both are Shape
```

### 模式 C：为领域类型自定义 `CanEqual`

当两个不同类型应当可比较时，显式提供 `given CanEqual` 实例。

```scala
import scala.language.strictEquality
case class Celsius(value: Double)
case class Fahrenheit(value: Double)

// 允许双向跨类型比较
given CanEqual[Celsius, Fahrenheit] = CanEqual.derived
given CanEqual[Fahrenheit, Celsius] = CanEqual.derived

Celsius(100) == Fahrenheit(212) // compiles (semantics are yours to define)
// Celsius(100) == 100 // error: no CanEqual[Celsius, Int]
```

限制比较可以防止跨领域的意外 bug：

```scala
case class UserId(value: Long) derives CanEqual
case class OrderId(value: Long) derives CanEqual
// UserId(1) == OrderId(1) // error: no CanEqual[UserId, OrderId]
// 这捕获了一个真实 bug —— 不同领域的 ID 不应被比较。
```

### 模式 D：Opaque Types 与相等性

opaque type 与其底层类型相互独立。在严格相等下，它拥有自己的相等性域。若希望与其他类型比较，必须显式提供 `CanEqual`。

```scala
import scala.language.strictEquality
object Units:
  opaque type Meters = Double
  object Meters:
    def apply(d: Double): Meters = d
  given CanEqual[Meters, Meters] = CanEqual.derived

  opaque type Feet = Double
  object Feet:
    def apply(d: Double): Feet = d
  given CanEqual[Feet, Feet] = CanEqual.derived

import Units.*
Meters(1.0) == Meters(2.0) // ok
Feet(3.0) == Feet(3.0) // ok
// Meters(1.0) == Feet(3.28) // error: no CanEqual[Meters, Feet]
// Meters(1.0) == 1.0 // error: no CanEqual[Meters, Double]
```

这是 opaque types 的一个重要收益：一旦启用严格相等，即可免费获得类型安全的相等性。

## Scala 2 对比

| 方面 | Scala 2 | Scala 3 |
|---|---|---|
| 默认相等性 | 全局相等：任意两个值都可用 `==` 比较，`42 == "hello"` 可编译无警告 | 默认相同，但 `strictEquality` 可选开启后变为类型错误 |
| 限制相等性 | 非内建。Scalactic 的 `===` 或 cats 的 `Eq` 类型类提供受检相等，但需要不同运算符 | `CanEqual` 适用于标准 `==` 和 `!=` 运算符，无需特殊语法 |
| ADT 相等性 | 无机制为 case class 层级自动派生安全相等 | enum 或 sealed trait 上的 `derives CanEqual` |
| Newtype 相等性 | 值类（`extends AnyVal`）仍使用全局相等 | `strictEquality` 下的 opaque types 默认处于各自的相等性域 |

## 何时选择哪个特性

| 需求 | 推荐 |
|---|---|
| 全项目防止无意义比较 | 通过编译器选项启用 **`strictEquality`**，按需添加 `CanEqual` 实例 |
| 为 ADT 提供安全相等 | 在 enum 或 sealed trait 上使用 **`derives CanEqual`**（模式 B） |
| 两个特定领域类型之间的跨类型比较 | **显式 `given CanEqual`** 实例（模式 C），需提供双向 |
| 阻止结构相同但语义不同的类型被比较 | **Opaque types**（模式 D），每个 opaque type 都是独立的相等性孤岛 |
| 渐进式迁移 | 先不启用 `strictEquality`；为新类型添加 `derives CanEqual`。覆盖面足够后再开启选项，编译错误会指引补齐缺失实例 |

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC15-equality.md
