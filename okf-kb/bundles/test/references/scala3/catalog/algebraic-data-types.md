---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T01-algebraic-data-types.md
title: 代数数据类型（Enum / ADT / GADT）
description: 通过 enum 将值空间封闭为编译器可知的有限备选项，实现穷尽模式匹配并按分支细化类型信息。
tags:
- T01
- Scala 3
- vibe-types
- 代数数据类型
- 枚举
- GADT
- 模式匹配
- 密封类型
timestamp: '2026-06-24T12:03:28Z'
---

# 代数数据类型（Enum / ADT / GADT）

> **引入版本：** Scala 3.0

## 简介

Scala 3 的 `enum` 关键字将简单枚举、代数数据类型（ADT）与广义代数数据类型（GADT）统一在单一语法构造之下。简单枚举定义一组具名的单例值（类似 Java 枚举）；ADT 通过带参数的 `case` 成员对"积之和"建模；GADT 则通过显式 `extends` 子句在各 case 中细化类型参数，使编译器能在模式匹配的分支中收窄类型。在底层，`enum` 编译为一个继承 `scala.reflect.Enum` 的 `sealed` class，每个 case 要么编译为 val（单例），要么编译为 case class（带参数）。

## 可表达的约束

**可以将一个类型的取值集合限制为封闭、编译器已知的有限备选项，从而获得穷尽的模式匹配；并通过 GADT 在不同分支中细化类型信息，让类型检查器强制执行因分支而异的不变量。**

- 枚举将取值约束为固定列表，编译器对非穷尽匹配发出警告。
- ADT 约束数据的形状：每个 case 恰好携带其声明的字段。
- GADT 约束类型参数与 case 之间的关系：匹配某个 case 会细化类型参数，从而支持按分支类型安全的操作。

## 最小示例

简单枚举：

```scala
enum Direction:
  case North, South, East, West

def describe(d: Direction): String = d match
  case Direction.North => "up"
  case Direction.South => "down"
  case Direction.East  => "right"
  case Direction.West  => "left"
// 穷尽匹配——无警告
```

ADT（积之和）：

```scala
enum Expr:
  case Lit(value: Int)
  case Add(a: Expr, b: Expr)
  case Neg(e: Expr)

def eval(e: Expr): Int = e match
  case Expr.Lit(v)     => v
  case Expr.Add(a, b)  => eval(a) + eval(b)
  case Expr.Neg(e)     => -eval(e)
```

GADT（按 case 细化类型）：

```scala
enum Expr[A]:
  case IntLit(value: Int)           extends Expr[Int]
  case BoolLit(value: Boolean)      extends Expr[Boolean]
  case Add(a: Expr[Int], b: Expr[Int]) extends Expr[Int]
  case Cond(test: Expr[Boolean], ifTrue: Expr[A], ifFalse: Expr[A])

def eval[A](e: Expr[A]): A = e match
  case Expr.IntLit(v)  => v           // 此处 A 被细化为 Int
  case Expr.BoolLit(v) => v           // 此处 A 被细化为 Boolean
  case Expr.Add(a, b)  => eval(a) + eval(b)
  case Expr.Cond(t, a, b) => if eval(t) then eval(a) else eval(b)
```

## 与其他特性的交互

| 特性 | 组合方式 |
|---|---|
| [类型类派生](derivation.md) | `enum Tree[T] derives Eq, Ordering` 借助 `Mirror.Sum` 与 `Mirror.Product` 自动为每个 case 生成实例。 |
| 多重相等 | 对 enum 标注 `derives CanEqual` 会将 `==` 限定在该 enum（或兼容类型）内部，阻止跨层比较。 |
| 模式匹配 / match 类型 | enum case 是模式匹配的主要目标；GADT 在分支中细化类型。match 类型可在类型层对类似密封层级做分派。 |
| 扩展方法 | 可在 enum 或其 case 事后添加方法；常见做法是通过 extension 提供语法，而不是污染 enum 主体。 |
| [不透明类型](newtypes-opaque.md) | enum 与不透明类型目标重叠（都限制取值），但 enum 工作在值层，不透明类型工作在类型层；当 enum case 包装一个不透明类型时二者可组合。 |

## 注意事项与局限

- **类型 widening。** enum case 构造应用的结果类型会被拓宽到父 enum 类型，而非具体 case 类型。要获得精确类型，使用 `new` 或显式类型标注：`val x: Option.Some[Int] = Option.Some(1)`。
- **变型与 case。** 带参数的 case 继承父 enum 的变型标注。若变型产生矛盾（例如逆变类型被协变地用于某字段），编译器要求显式 `extends` 子句并提供新的、不变型类型参数。
- **enum case 的作用域。** enum case 声明位于 enum 模板主体之外，不能访问 enum class 的内部成员；对伴生对象的引用必须完全限定（如 `Planet.earthMass`）。
- **case 无伴生。** 不能在 enum 主体内为 enum case 定义伴生对象；模板内同名对象是无关的独立对象。
- **Java 兼容性。** 要将 Scala enum 用作 Java 枚举，需继承 `java.lang.Enum[E]`；带参数的 ADT case 与 Java 枚举不兼容。
- **穷尽性。** 编译器对所有 `sealed` 层级（所有 enum 都是密封的）检查穷尽性。向 enum 新增 case 会在所有非穷尽匹配处产生警告，形成编译期契约。
- **ordinal 与辅助方法。** 每个 enum 值都有 `ordinal: Int`；伴生对象获得 `values: Array[E]`、`valueOf(name: String): E`、`fromOrdinal(n: Int): E`。

## 推荐库

| 库 | 作用 | 链接 |
|---|---|---|
| circe | 为 ADT 提供 JSON 编解码；对 enum/密封层级自动派生 | [circe.github.io](https://circe.github.io/circe/) |
| enumeratum | 增强枚举，提供穷尽辅助与 JSON/Play 集成（Scala 2 兼容；Scala 3 原生 enum 已覆盖多数场景） | [github.com/lloydmeta/enumeratum](https://github.com/lloydmeta/enumeratum) |
| iron | 在 ADT 之上构建细化类型；对 enum 包装的值施加编译期约束 | [github.com/Iltotore/iron](https://github.com/Iltotore/iron) |

## 从 Lean 迁移

Scala 3 的 `enum` 配合 GADT 对应 Lean 的*索引归纳族*。Lean 写 `inductive Expr : Type → Type where | intLit : Int → Expr Int`，Scala 写 `case IntLit(v: Int) extends Expr[Int]`。两者都能在模式匹配中实现按分支的类型细化。关键差异：Lean 的归纳族可以按*值*索引（如 `Vec α n`，其中 `n : Nat`），而 Scala 的 GADT 只能细化*类型参数*。

## 用例交叉引用

- [领域建模](../usecases/domain-modeling.md)：以封闭类型层级进行领域建模。
- [编译期](../usecases/compile-time.md)：类型安全的表达式树（GADT 解释器）。
- [状态机](../usecases/state-machines.md)：穷尽的命令/事件处理。
- 序列化：为 sum 类型派生编解码。

# 引用

- [T01-algebraic-data-types.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T01-algebraic-data-types.md)
