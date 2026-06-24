---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T34-never-bottom.md
title: Nothing 与底类型 (Never / Bottom Type)
description: Nothing 是 Scala 的底类型，无任何居民，使发散计算与任意类型上下文保持类型兼容；explicit-nulls 把 Null
  从引用类型层级中解耦。
tags:
- Scala 3
- vibe-types
- T34
- Nothing
- 底类型
- 'Null'
- explicit-nulls
- 变体
timestamp: '2026-06-24T12:06:51Z'
---

# Nothing 与底类型 (Never / Bottom Type)

> **引入版本：** Scala 3.0（继承自 Scala 2；语义不变）| **最近变更：** Scala 3.3（`-Yexplicit-nulls` 稳定）

## 简介

`Nothing` 是 Scala 的**底类型（bottom type）**：它是所有其他类型的子类型，且没有任何居民——没有任何值的类型可以是 `Nothing`。类型为 `Nothing` 的表达式必须发散（抛异常、永久循环或调用 `sys.error`）。因为 `Nothing` 是一切类型的子类型，它充当协变类型参数的单位元：空的 `List[Nothing]` 可赋值给 `List[Int]`、`List[String]` 或任何 `List[A]`。相关的 `Null` 类型是 `null` 字面量的类型；在标准 Scala 下它是所有引用类型（但非值类型）的子类型，而在 explicit-nulls 标志（`-Yexplicit-nulls`）下，它被从子类型层级中移除，使得不带显式 `T | Null` 联合的 `null` 赋值成为编译错误。

## 可表达的约束

**`Nothing` 让类型系统表达永不产生值的计算，同时与任何上下文保持类型兼容。** 返回 `Nothing` 的方法可以出现在任何期望类型的地方——`if/else` 分支、集合元素或默认分支——而不破坏类型推断。这让 `throw`、`???` 与非终止循环可与任何周围代码组合。`Null`（配合 explicit nulls）让你在类型层面表达一个引用是否可能缺失，把空安全从运行时移到编译期。

## 最小示例

**`Nothing` 作为发散表达式的返回类型：**

```scala
def fail(msg: String): Nothing = throw RuntimeException(msg)
// Nothing 与任何期望类型兼容：
val x: Int = if true then 42 else fail("unreachable")
val s: String = ??? // ??? : Nothing，在任何位置都可编译
```

**`Nothing` 在空集合中（协变拓宽）：**

```scala
val empty: List[Nothing] = Nil
val ints: List[Int] = empty // OK：List[Nothing] <: List[Int]
val strs: List[String] = Nil // Nil: List[Nothing] <: List[String]
// 这之所以成立，是因为 List 是协变的：List[+A]
// 而 Nothing <: Int，故 List[Nothing] <: List[Int]
```

**`???` 作为类型洞：**

```scala
def complexAlgorithm(data: List[Int]): Map[String, List[Double]] =
  ??? // 可编译 —— ??? : Nothing <: Map[String, List[Double]]
```

**`Null` 类型与 explicit nulls：**

```scala
//> using option "-Yexplicit-nulls"
// 启用 -Yexplicit-nulls 后：
@main def explicitNullsDemo(): Unit =
  val s: String = null // 错误：Found Null, Required String
  val s2: String | Null = null // OK：Null 是联合的一部分
  def fromJava(s: String | Null): Option[String] =
    if s != null then Some(s) else None
  ()
```

**`Nothing` 在协变返回拓宽中：**

```scala
enum Opt[+A]:
  case Some(value: A)
  case Non // Non extends Opt[Nothing]

val none: Opt[Nothing] = Opt.Non
val intOpt: Opt[Int] = none // OK：Opt[Nothing] <: Opt[Int]
val strOpt: Opt[String] = Opt.Non // 同理：拓宽到任意 Opt[A]
```

## 与其他特性的交互

| 特性 | 组合方式 |
|---|---|
| **变体**（见 [variance-subtyping](variance-subtyping.md)） | `Nothing` 位于子类型格的底部，故协变容器（`List[+A]`、`Option[+A]`）可持有 `Nothing` 并拓宽到任何元素类型。逆变容器反之：`Printer[Nothing]` 是 `Printer` 层级的**顶端**。 |
| **联合 / 交集类型**（见 [union-intersection](union-intersection.md)） | `A | Nothing` 化简为 `A`（Nothing 是联合的单位元）。`A & Nothing` 化简为 `Nothing`（Nothing 吸收交集）。在 explicit nulls 下，`String | Null` 是惯用的可空类型。 |
| **枚举 / ADT**（见 [algebraic-data-types](algebraic-data-types.md)） | 不带类型参数的单例枚举分支（如 `None`、`Nil`）以 `Nothing` 作为类型实参继承父类，启用协变拓宽。 |
| **泛型与约束**（见 [generics-bounds](generics-bounds.md)） | `Nothing` 满足任何上界：`Nothing <: A` 对所有 `A` 成立。这意味着 `Nothing` 可替换任何有界类型参数。下界 `A >: Nothing` 恒成立，因此是空泛的。 |
| **类型别名**（见 [type-aliases](type-aliases.md)） | `type Never = Nothing` 是合法的透明别名。库有时定义 `type Absurd = Nothing` 用于文档目的。 |
| **空安全**（见 [null-safety](null-safety.md)） | 在 `-Yexplicit-nulls` 下，`Null` 与引用类型层级解耦。只有 `T | Null` 可持有 `null`，使可空 API 在类型层面显式化。 |

## 注意事项与局限

1. **`Nothing` 没有值。** 你无法创建 `Nothing` 类型的值。任何此类尝试（如 `val x: Nothing = ???`）都会在运行时抛出。`Nothing` 只作为类型有用，绝不作为值。
2. **类型推断与 `Nothing`。** 当编译器无法推断类型参数时，有时会默认为 `Nothing`，在下游产生令人困惑的错误。例如 `List()` 推断为 `List[Nothing]`，后续添加元素时可能造成类型不匹配。
3. **`Null` vs `None` vs `Nothing`。** 三者常被混淆。`Null` 是 `null` 的类型（存在一个值：`null`）。`Nothing` 完全没有值。`None` 是类型为 `Option[Nothing]` 的一个值。它们位于不同层级：`Nothing <: Null <: AnyRef`（无 explicit nulls 时）。
4. **explicit nulls 不是默认。** `-Yexplicit-nulls` 标志必须显式启用。否则 `null` 可赋值给任何引用类型，`Null` 仍是所有 `AnyRef` 子类型的父类型。
5. **`throw` 是 `Nothing` 类型的表达式。** 在 Scala 3 中 `throw` 是表达式而非语句。其类型为 `Nothing`，所以 `if cond then value else throw ...` 能通过类型检查：`else` 分支类型为 `Nothing`，会拓宽到 `then` 分支的类型。
6. **Java 互操作与 `null`。** Java 方法经常返回 `null`。启用 explicit nulls 后，其返回类型被拓宽为 `T | Null`，要求显式空检查。不启用时 `null` 会未经检查地流过。
7. **`Nothing` 与协变类型参数默认值。** 定义 `type F[+A] = ...` 的库可能用 `Nothing` 作为默认。例如 `Either[Nothing, Int]` 表示一个无左分支的右偏值。意外地（因推断失败）使用 `Nothing` 可能掩盖逻辑错误。

## 入门心智模型

把 `Nothing` 视为**空类型**——一个零可能值的类型。它是类型系统层面的 "这永远不可能发生"。因为它没有值，所以假装它是任何类型都是安全的（一个永不会被兑现的承诺无法被打破）。这就是 `throw` 和 `???` 可以出现在任何地方的原因：它们承诺返回任何类型，并通过永不返回来兑现承诺。

在类型层级中：
- `Any` 在顶端（一切的超类型）。
- `Nothing` 在底部（一切的子类型）。
- 每个类型介于二者之间：`Nothing <: Int <: AnyVal <: Any`。

`Null` 类似但更窄：它是**引用类型**层级的底（`Null <: String <: AnyRef <: Any`），且它恰好有一个值：`null`。

## 常见类型检查器报错

```
-- [E007] Type Mismatch Error ---
val xs = List()
xs.head + 1
^^^^^^^^
Found: Nothing
Required: Int
Fix: 空 List() 被推断为 List[Nothing]。
请提供类型标注：val xs = List.empty[Int]
```

```
-- [E007] Type Mismatch Error ---（启用 -Yexplicit-nulls）
val name: String = javaObject.getName()
^^^^^^^^^^^^^^^^^^^^
Found: String | Null
Required: String
Fix: 显式处理空值情况：
val name: String = Option(javaObject.getName()).getOrElse("unknown")
// 或：val name: String = javaObject.getName().nn
```

```
-- [E172] Type Error ---
val x: Nothing = 42
^^
Found: Int
Required: Nothing
Fix: Nothing 没有值。你不能给 Nothing 赋值。
若想要发散表达式，请用 throw 或 ???。
```

## 用例交叉引用

- 见 [非法状态不可表示](../usecases/invalid-states.md)：在 sealed 层级中用 `Nothing` 表示不可能状态。
- 见 [领域建模](../usecases/domain-modeling.md)：领域模型中的空集合类型与协变拓宽。
- 见 [错误处理](../usecases/error-handling.md)：总是抛出异常的错误处理函数使用 `Nothing` 返回类型。
- 见 [可空性](../usecases/nullability.md)：`Null` 类型与 explicit nulls 用于空安全 API。
- 见 [变体](../usecases/variance.md)：底类型与变体在泛型容器设计中的交互。

# 引用

- [Scala 3 Reference: Type Hierarchy](https://docs.scala-lang.org/scala3/book/types-introduction.html)
- [Scala 3 Reference: Explicit Nulls](https://docs.scala-lang.org/scala3/reference/experimental/explicit-nulls.html)
- [Scala API: Nothing](https://www.scala-lang.org/api/3.x/scala/Nothing.html)
- [Scala API: Null](https://www.scala-lang.org/api/3.x/scala/Null.html)
