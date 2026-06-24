---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T25-coherence-orphan.md
title: 连贯性与实例作用域（Coherence & Instance Scoping）
description: Scala 3 无孤儿规则，通过给定实例的作用域与 import 规则实现“每个使用点至多一个实例”的局部连贯性，歧义时报错而非静默选择。
tags:
- T25
- Scala 3
- vibe-types
- 连贯性
- 孤儿规则
- given 作用域
- 导入优先级
timestamp: '2026-06-24T12:05:18Z'
---

# 连贯性与实例作用域（Coherence & Instance Scoping）

**起始版本：** Scala 3.0 | **最新变更：** Scala 3.6（新 given 语法、细化优先级规则）

## 简介

Scala 3 **没有孤儿规则**。与 Rust 不同（Rust 禁止在不拥有 trait 或类型之一的情况下为某类型实现某 trait），Scala 允许在任何地方为任意类型类/类型组合定义 `given` 实例。连贯性——即每个类型至多有一个可用实例的保证——转而通过 **作用域与 import 规则** 维护：given 实例并非全局可见；它们必须被显式 import 或通过伴生对象的隐式作用域发现。

这是一个刻意的权衡。Rust 的孤儿规则提供 _全局_ 连贯性（整个程序中恰有一个 `impl Trait for Type`）。Scala 提供 _局部_ 连贯性（每个使用点至多有一个无歧义的 given 在作用域内）。这赋予 Scala 更大的灵活性——可以在不同作用域定义替代实例——但需要自律以避免冲突实例。

## 可表达的约束

**Scala 的 given 作用域规则确保：在任何使用点，编译器对每个类型至多找到一个 given 实例。若两个同类型实例以相同优先级出现在作用域内，编译器会以歧义错误拒绝程序，而非静默选择其一。**

## 最小示例

```scala
trait Ordering[T]:
  def compare(x: T, y: T): Int

// Instance in companion object — always in implicit scope
object Ordering:
  given Ordering[Int]:
    def compare(x: Int, y: Int) = x - y

// Alternative instance in a separate object — must be imported
object ReverseOrdering:
  given Ordering[Int]:
    def compare(x: Int, y: Int) = y - x

def sorted[T: Ordering](xs: List[T]): List[T] =
  xs.sortWith((a, b) => summon[Ordering[T]].compare(a, b) < 0)

// Default: uses companion instance
sorted(List(3, 1, 2)) // List(1, 2, 3)

// Override: import the alternative
{
  import ReverseOrdering.given
  sorted(List(3, 1, 2)) // List(3, 2, 1)
}
// Outside the block, the default is back in effect
```

## Scala 如何在没有孤儿规则的情况下避免冲突实例

### 1. 基于 import 的可见性

Given 实例 **不会** 被 `import M.*` 导入。它们需要显式 `import M.given` 或 `import M.{given Ordering[?]}`。这意味着不同模块中的冲突实例除非被显式带到一起，否则不会互相干扰。

### 2. 伴生作用域作为默认

编译器会自动搜索目标类型所涉及类型的伴生对象。对于 `Ordering[MyClass]`，它会搜索 `Ordering` 与 `MyClass` 的伴生。把"规范"实例放在这些伴生之一中即可使其成为默认而无需任何 import。

### 3. 优先级排序

当发现多个实例时，由特异性规则消解冲突：

- **本地/import 的** 优于 **伴生作用域的**。
- **更具体的类型** 优于 **更一般的**（`given Ordering[Int]` 优于 `given [T] => Ordering[T]`）。
- **子类** 实例优于 **超类** 实例。
- **具名 import** 优于 **通配 given import**。

### 4. 用 export 做受控再暴露

`export` 子句让模块有选择地从另一模块再暴露 given 实例，创建精心策划的"实例包"，而不引入全部。

```scala
trait Ordering[T]:
  def compare(x: T, y: T): Int
trait Show[T]:
  def show(t: T): String

object Ordering:
  given Ordering[Int] = (x, y) => x - y   // companion given to re-export

object MyCustomInstances:
  given Show[Int] = _.toString
  given Show[Boolean] = if _ then "yes" else "no"

object Defaults:
  export Ordering.given                       // re-export companion givens
  export MyCustomInstances.{given Show[?]}    // only Show instances
```

## 与其他特性的交互

| 特性 | 如何组合 |
|---|---|
| **类型类 / given**（[type-classes](type-classes.md)） | 连贯性规则决定编译器为每个 `using` 参数选择哪个 given 实例。作用域规则 _就是_ 连贯性机制。 |
| **上下文函数**（[context-functions](context-functions.md)） | 上下文函数（`T ?=> U`）会为 `T` 触发 given 解析。相同的作用域与优先级规则适用。 |
| **Given 解析**（[trait-solver](trait-solver.md)） | 该条目详述解析算法，本条目聚焦从这些规则中涌现的连贯性性质。 |
| **封装**（[encapsulation](encapsulation.md)） | 访问修饰符与 `export` 子句控制哪些 given 实例可见，提供类型类实例的模块级封装。 |

## 与 Rust 孤儿规则的对比

| 方面 | Rust | Scala 3 |
|---|---|---|
| **规则** | 不能为外来类型实现外来 trait | 无限制——任何地方都可定义 given |
| **连贯性作用域** | 全局（整个程序） | 局部（每个使用点） |
| **冲突实例** | 在 impl 定义处即编译错误 | 在使用点报歧义错误（若两者都在作用域内） |
| **Newtype 变通** | 替代实例所必需 | 不需要——在不同作用域定义即可 |
| **权衡** | 安全换取灵活性 | 灵活性换取自律 |

## 注意事项与局限

1. **无全局唯一性保证。** 两个库都可在各自伴生对象中定义 `given Ordering[Int]`。若用户同时 import 两者，会得到歧义错误。Scala 依赖约定（把规范实例放伴生）而非强制。
2. **菱形 import。** 从两个传递包含同一实例的模块 import given 可能导致意外歧义。请用按类型 import（`import M.{given Ordering[?]}`）以精确控制。
3. **伴生作用域总会被搜索。** 你无法"退出"伴生对象实例。若伴生提供了 given 而你又 import 了替代品，编译器会发现两者——但 import 因优先级胜出。若两者特异性相同，则发生歧义。
4. **从 Scala 2 迁移。** Scala 2 的 `implicit` 定义会被 `import M.*` 找到，但 Scala 3 的 `given` 定义不会。这种差异在迁移时可能造成令人困惑的破坏。
5. **无连贯性检查器。** 与 Rust 编译器在定义时即拒绝不连贯程序不同，Scala 只在使用点检测冲突。未被 import 的模块中的冲突实例在有人 import 之前不会报错。
6. **密封类型类。** 一种获得更强连贯性的模式：把类型类 trait 设为 `sealed`，或将其放入受控 export 的包中，使只有被授权的模块能定义实例。

## 初学者心智模型

把 given 实例想象成档案柜里的 **名片**。每个类型类都有一个"默认"柜（其伴生对象）放一张名片。其他模块可以印自己的名片（替代实例），但这些名片在有人显式取出（import）之前一直待在自己的柜子里。任一时刻，你对每种类型只能手持一张名片。若你不小心抓了两张，编译器会让你放回一张（歧义错误）。相比之下，Rust 一开始就只允许印一张名片。

## 示例 A —— 作用域化的替代实例

```scala
trait JsonFormat[T]:
  def write(t: T): String

object JsonFormat:
  given JsonFormat[java.time.LocalDate]:
    def write(d: java.time.LocalDate) = s""""${d.toString}""""

object IsoFormat:
  given JsonFormat[java.time.LocalDate]:
    def write(d: java.time.LocalDate) =
      s""""${d.format(java.time.format.DateTimeFormatter.ISO_DATE)}""""

object AmericanFormat:
  given JsonFormat[java.time.LocalDate]:
    def write(d: java.time.LocalDate) =
      s""""${d.format(java.time.format.DateTimeFormatter.ofPattern("MM/dd/yyyy"))}""""

// Each module imports exactly the format it needs — no conflict
object EuropeanService:
  import IsoFormat.given
  def serialize(d: java.time.LocalDate) = summon[JsonFormat[java.time.LocalDate]].write(d)

object AmericanService:
  import AmericanFormat.given
  def serialize(d: java.time.LocalDate) = summon[JsonFormat[java.time.LocalDate]].write(d)
```

## 用例交叉引用

- 作用域化实例让第三方扩展免受孤儿规则摩擦，见 [可扩展性](../usecases/extensibility.md)。

# 引用

- 原始资料：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T25-coherence-orphan.md
- Scala 3 Reference — Given Imports: https://docs.scala-lang.org/scala3/reference/contextual/given-imports.html
- Scala 3 Reference — Implicit Resolution: https://docs.scala-lang.org/scala3/reference/changed-features/implicit-resolution.html
- Scala 3 Reference — Givens: https://docs.scala-lang.org/scala3/reference/contextual/givens.html
- Scala 3 Reference — Export Clauses: https://docs.scala-lang.org/scala3/reference/other-new-features/export.html
