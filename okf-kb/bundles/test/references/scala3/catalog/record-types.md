---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T31-record-types.md
title: 记录类型与数据建模 (Record Types)
description: Scala 3 通过 case class、命名元组与普通元组三种机制覆盖从领域建模到临时数据打包的完整数据建模谱系，由编译器保证字段形状的正确性。
tags:
- Scala 3
- vibe-types
- T31
- 记录类型
- case class
- 命名元组
- 元组
- 数据建模
timestamp: '2026-06-24T12:06:50Z'
---

# 记录类型与数据建模 (Record Types)

> **引入版本：** Scala 3.0 | **最近变更：** Scala 3.7（命名元组）

## 简介

Scala 3 的主要记录类型是 **case class**：一种名义型（nominal）积类型，会自动派生 `equals`、`hashCode`、`toString`、`copy` 以及用于模式匹配的 `unapply` 提取器。对于轻量级匿名记录，Scala 3.7 引入了**命名元组（named tuples）**（`(name: String, age: Int)`）——一种结构化积类型，字段按名访问且零运行时开销（名字只在编译期存在）。普通**元组（tuple）**（`(A, B, C)`）提供任意元数的位置型积类型。这三者共同覆盖了数据建模的完整谱系：从有名、模式约束的领域对象（case class），到临时数据束（命名元组），再到匿名位置组合（元组）。

## 可表达的约束

**记录类型允许声明数据的精确形状——存在哪些字段、各字段的类型、以及自动可用的操作——从而使编译器拒绝任何误用、遗漏或混淆字段的代码。** case class 以名义身份强制命名模式；命名元组以结构身份强制命名模式；普通元组只强制位置元数与类型。

## 最小示例

**case class（标准记录类型）：**

```scala
case class User(name: String, age: Int, email: String)
val alice = User("Alice", 30, "alice@example.com")
// 自动派生成员：
alice.toString // "User(Alice,30,alice@example.com)"
alice == User("Alice", 30, "alice@example.com") // true（结构相等）
alice.hashCode // 与 equals 一致
// 通过命名参数复制修改：
val older = alice.copy(age = 31)
// 通过自动生成的 unapply 进行模式匹配：
alice match
  case User(name, age, _) => s"$name is $age"
```

**命名元组（Scala 3.7+）：**

```scala
type Point = (x: Double, y: Double)
val origin: Point = (x = 0.0, y = 0.0)
origin.x // 0.0
origin.y // 0.0
// 命名元组模式匹配：
origin match
  case (x = a, y = b) => s"($a, $b)"
// 无名元组按位置兼容：
val p: Point = (1.0, 2.0) // OK
```

**普通元组：**

```scala
val pair: (String, Int) = ("Alice", 30)
pair._1 // "Alice"
pair._2 // 30
// 任意元数（Scala 3 不再限制 22 个）：
val big: (Int, Int, Int, Int, Int) = (1, 2, 3, 4, 5)
```

**case class 与命名元组的关键差异：**

```scala
case class Coord(x: Double, y: Double)
type CoordT = (x: Double, y: Double)
val a = Coord(1.0, 2.0)
val b: CoordT = (x = 1.0, y = 2.0)
// case class：名义型——Coord 是独立类型
// 命名元组：结构型——CoordT 即 (x: Double, y: Double)
// a == b // 无法编译：类型不同
```

## 与其他特性的交互

| 特性 | 组合方式 |
|---|---|
| **ADT / 枚举**（见 [algebraic-data-types](algebraic-data-types.md)） | case class 是代数数据类型的积分支。带参数的 `enum` 分支构成一组 case class 积之和。 |
| **类型类派生**（见 [derivation](derivation.md)） | `case class User(...) derives Eq, Show, JsonCodec` 通过 `Mirror.Product` 触发自动派生。命名元组没有 `Mirror` 实例。 |
| **不透明类型**（见 [newtypes-opaque](newtypes-opaque.md)） | 命名元组内部实现为不透明类型：`opaque type NamedTuple[N <: Tuple, +V <: Tuple] >: V = V`。名字在运行时被擦除。 |
| **结构类型**（见 [structural-typing](structural-typing.md)） | 命名元组连接名义与结构类型：`NamedTuple.From[User]` 提取 case class 对应的命名元组类型，可构建类型化查询 DSL。 |
| **模式匹配**（见 [type-narrowing](type-narrowing.md)） | case class 自动生成用于解构的 `unapply`。命名元组同时支持命名和位置模式匹配。 |
| **多宇宙相等性**（见 [equality-safety](equality-safety.md)） | `case class Foo(...) derives CanEqual` 把 `==` 限定为同类型比较，避免不同 case class 间的误判相等。 |

## 注意事项与局限

1. **case class 相等性是结构性的，而非引用性的。** 字段值相同的两个实例即 `==`。这通常是期望行为，但当把含可变字段的实例作为 map 键时会令人意外（不要在 case class 中放可变字段）。
2. **`copy` 与默认参数。** `copy` 使用命名参数。给 case class 新增字段不会破坏已有的命名 `copy` 调用，但在已有位置参数**之前**新增字段则会。
3. **case class 继承受限。** 一个 case class 不能继承另一个 case class。这是有意为之：继承 + 自动生成的相等性是不健全的（即 "equals-hashCode 契约" 问题）。
4. **命名元组字段顺序有意义。** `(name: String, age: Int)` 与 `(age: Int, name: String)` 是不同的不兼容类型。与 Python 的 `TypedDict` 不同，字段顺序不可忽略。
5. **命名元组不能混用命名与未命名元素。** 所有元素要么全部命名，要么全部未命名。`(name: String, Int)` 是非法的。
6. **命名元组上不能定义自定义方法。** 命名元组是结构性的——无法添加方法或实现 trait。需要行为时请用 case class。
7. **模式匹配穷尽性。** sealed 层级中的 case class 会得到穷尽性检查。命名元组和普通元组不参与 sealed 层级。

## 入门心智模型

可以把 Scala 的记录类型视为三种正式程度的级别：

- **case class**：正式、命名的数据类型。像带模式的数据库表——有名字、类型化字段、相等性、模式匹配，还能实现 trait。用于领域模型。
- **命名元组**：快速、临时的带标签束。类似 Python `namedtuple` 或 TypeScript `{ name: string, age: number }`——轻量、结构化、零仪式。用于返回值和中间数据。
- **普通元组**：位置型杂货袋。类似返回 `(Int, String)`——快速且极简，但字段没有名字。用于平凡的多值返回。

## 常见类型检查器报错

```
-- [E007] Type Mismatch Error ---
case class Celsius(value: Double)
case class Fahrenheit(value: Double)
val temp: Celsius = Fahrenheit(72.0)
^^^^^^^^^^^^^^^^
Found: Fahrenheit
Required: Celsius
Note: case classes are nominal -- same fields does not mean same type.
```

```
-- Error ---
case class A(x: Int)
case class B(x: Int) extends A(x)
^
case class B may not extend another case class
Fix: use a common trait instead:
sealed trait HasX { def x: Int }
case class A(x: Int) extends HasX
case class B(x: Int) extends HasX
```

```
-- Error ---
type Rec = (name: String, 42)
^^
Illegal combination of named and unnamed tuple elements
Fix: all elements must be named or all must be unnamed:
type Rec = (name: String, id: Int)
```

## 用例交叉引用

- 见 [领域建模](../usecases/domain-modeling.md)：以 case class 作为主要记录类型进行领域建模。
- 见 [非法状态不可表示](../usecases/invalid-states.md)：通过 sealed case class 层级让非法状态不可表示。
- 见 [构建器配置](../usecases/builder-config.md)：用命名元组表达轻量级配置记录。
- 见 [序列化](../usecases/serialization.md)：通过类型类派生为 case class 生成 JSON 编解码器。
- 见 [编译期](../usecases/compile-time.md)：用 `NamedTuple.From` 在编译期提取模式。

# 引用

- [Scala 3 Reference: Case Classes](https://docs.scala-lang.org/scala3/book/domain-modeling-tools.html#case-classes)
- [Scala 3 Reference: Named Tuples](https://docs.scala-lang.org/scala3/reference/experimental/named-tuples.html)
- [Scala 3 Reference: Tuples](https://docs.scala-lang.org/scala3/reference/new-types/tuple-types.html)
- [Scala 3 Reference: Enums / ADTs](https://docs.scala-lang.org/scala3/reference/enums/adts.html)
