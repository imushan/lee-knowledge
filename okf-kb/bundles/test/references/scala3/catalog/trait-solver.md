---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T37-trait-solver.md
title: Given/隐式解析 (Trait Solver)
description: Scala 3 的 given 解析算法在定义良好的作用域中搜索并按特异性选择唯一最佳 given 实例，保证能力注入的无歧义性。
tags:
- Scala 3
- vibe-types
- T37
- given 解析
- 隐式解析
- 类型类
- using
- 上下文参数
timestamp: '2026-06-24T12:06:52Z'
---

# Given/隐式解析 (Trait Solver)

> **引入版本：** Scala 3.0 | **最近变更：** Scala 3.6（新 given 语法，简化优先级规则）

## 简介

given 解析是编译器算法，在 `using` 参数需要填充时查找并选择 **given 实例**（Scala 3 对 Scala 2 implicit 的替代）。它类似于 Rust 的 trait solver 或 Haskell 的 instance resolution：编译器在一组定义良好的作用域中搜索，按特异性排序候选，然后要么提供唯一最佳匹配，要么报错。在 Scala 3 中，规则被重新设计得比 Scala 2 的隐式搜索更简单、更可预测，具有更清晰的优先级排序和更好的歧义报告。

该解析算法决定了类型类实例来自哪里、能力注入如何工作，以及两个竞争的 given 定义是引发歧义错误还是按特异性解析。理解该算法对调试 "no given instance found" 与 "ambiguous given instances" 错误至关重要。

## 可表达的约束

**given 解析保证对于每个 `using` 参数，作用域中至多存在一个无歧义的 given 实例。编译器要么找到唯一最佳候选，要么拒绝程序，防止静默选择非预期实例。**

## 最小示例

```scala
trait Show[T]:
  extension (t: T) def show: String

// 伴生对象——对 Show[Int] 始终在隐式作用域中
object Show:
  given Show[Int]:
    extension (t: Int) def show = t.toString

// 本地作用域——优先级高于伴生对象
object CustomInstances:
  given Show[Int]:
    extension (t: Int) def show = s"int($t)"

def printIt[T: Show](x: T): Unit = println(x.show)

// 不导入时：使用伴生对象实例
printIt(42) // "42"

// 导入后：本地导入胜过伴生对象
import CustomInstances.given
printIt(42) // "int(42)"
```

## 与其他特性的交互

| 特性 | 组合方式 |
|---------|-----------------|
| **类型类 / given**（见 [type-classes](type-classes.md)） | given 解析是类型类分派的*引擎*。每个 `[T: Ord]` 上下文绑定都会触发解析算法查找 `Ord[T]` 实例。 |
| **上下文函数**（见 [context-functions](context-functions.md)） | 上下文函数应用 `T ?=> U` 会为 `T` 参数触发解析。搜索遵循相同的作用域与优先级规则。 |
| **转换 / 强制**（见 [conversions-coercions](conversions-coercions.md)） | 隐式转换（`given Conversion[A, B]`）由同一解析机制查找，但仅当否则会发生类型不匹配时才应用。 |

## 编译器查找的位置（搜索作用域）

编译器按以下顺序查找 given 实例：

1. **本地作用域。** 在包围块、方法或类中定义或导入的 given。
2. **显式导入。** `import M.given`、`import M.{given Show[?]}` 或 `import M.specificInstance`。
3. **通配导入。** `import M.given`（通配 given 导入）——但**不是** `import M.*`，后者排除 given。
4. **隐式作用域（伴生对象）。** 目标类型涉及的所有类型的伴生对象。对于 `Show[List[Int]]`，编译器搜索 `Show`、`List` 与 `Int` 的伴生。
5. **包对象与顶层 given。** 在包含调用点的包顶层定义的 given。

## 优先级规则

当找到多个候选时，编译器应用**特异性（specificity）**选择：

- 定义在**子类**中的 given 胜过定义在**超类**中的。
- 类型参数**更具体**的 given 胜出（例如 `given Show[Int]` 胜过 `given [T] => Show[T]`）。
- **本地或导入**的 given 胜过通过**隐式作用域**（伴生对象）找到的。
- **命名**导入胜过**通配** given 导入。

若两个候选特异性相同，编译器报**歧义错误**。

## Scala 3 相对 Scala 2 的变化

- **`given` 取代 `implicit val/def/object`。** 新关键字让意图显式。
- **given 导入是独立的。** `import M.*` 不会导入 given。请用 `import M.given`。
- **更简单的优先级。** Scala 2 有基于继承与 "非继承" 规则的复杂隐式优先级。Scala 3 使用更清晰的特异性排序。
- **歧义传播。** 在 Scala 2 中，搜索深处的歧义可能静默导致顶层 "not found" 错误。Scala 3 把歧义向上传播，产生更好的错误信息。
- **`-explain` 标志。** 用 `-explain` 编译可查看编译器的搜索轨迹，显示检查了哪些作用域以及候选为何被接受或拒绝。

## 注意事项与局限

1. **`import M.*` 不导入 given。** 这是 Scala 2 迁移者最常见的意外。你必须写 `import M.given` 或 `import M.{given, *}`。
2. **伴生作用域最后搜索。** 伴生对象中的 given 是后备，而非默认。任何同类型的本地或导入 given 都会遮蔽它。
3. **发散检测。** 若解析递归触发自身（如 `given [T: Show] => Show[List[T]]` 无基例），编译器检测到循环并报错而非死循环。
4. **按名上下文参数。** 声明为 `=> T`（按名）的 `using` 参数允许编译器通过推迟求值打破递归 given 搜索中的环。这对相互递归的类型类实例至关重要。
5. **匿名 given 冲突。** 两个结构相似的匿名 given 可能获得相同的编译器生成名，导致二进制兼容问题。请显式命名公开的 given。
6. **`summon` vs 直接访问。** `summon[T]` 在调用点触发解析。若你已通过 `using` 参数持有实例，请直接访问以避免冗余搜索。

## 入门心智模型

把编译器视为一个在找书（given 实例）的**图书管理员**。它先查你的桌面（本地作用域），再查你的私人书架（导入），然后走到参考区（伴生对象）。若找到唯一匹配的书，就交给你。若找到两本同样好的匹配，它要求你说得更具体（歧义错误）。若什么也没找到，它告诉你书缺失（"no given instance found"）。

## 示例 A —— 用 `-explain` 调试

```scala
trait Codec[T]:
  def encode(t: T): String

object Codec:
  given Codec[String]:
    def encode(t: String) = s"\"$t\""

object JsonCodecs:
  given Codec[String]:
    def encode(t: String) = s"""{"value":"$t"}"""

import JsonCodecs.given
// 用以下命令编译：scalac -explain MyFile.scala
// 编译器显示：
// - 在 JsonCodecs 中找到 given Codec[String]（通过导入）
// - 在 Codec 伴生中找到 given Codec[String]（通过隐式作用域）
// - 选中：JsonCodecs 实例（导入胜过伴生）
def test = summon[Codec[String]].encode("hi") // {"value":"hi"}
```

## 用例交叉引用

- 见 [可扩展性](../usecases/extensibility.md)：given 解析决定了第三方类型类实例如何被发现与排序。
- 见 [编译期](../usecases/compile-time.md)：解析完全在编译期发生；理解搜索算法有助于诊断编译期错误。

# 引用

- [Scala 3 Reference — Given Instances](https://docs.scala-lang.org/scala3/reference/contextual/givens.html)
- [Scala 3 Reference — Given Imports](https://docs.scala-lang.org/scala3/reference/contextual/given-imports.html)
- [Scala 3 Reference — Implicit Resolution](https://docs.scala-lang.org/scala3/reference/changed-features/implicit-resolution.html)
- [Scala 3 Migration Guide — Implicit Resolution Changes](https://docs.scala-lang.org/scala3/guides/migration/incompat-other-changes.html)
