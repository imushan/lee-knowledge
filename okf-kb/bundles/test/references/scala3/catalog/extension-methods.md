---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T19-extension-methods.md
title: 扩展方法（Extension Methods）
description: 允许在不修改原类型源码的情况下为其追加方法，并可结合 given 实例实现仅在具备类型类证据时才可见的条件化方法。
tags:
- T19
- Scala 3
- vibe-types
- 扩展方法
- 类型类语法
- 条件化扩展
timestamp: '2026-06-24T12:03:25Z'
---

# 扩展方法（Extension Methods）

**起始版本：** Scala 3.0

## 简介

扩展方法允许在类型已经定义之后再为其添加新方法，而无需修改其源码、继承子类或进行包装。一个 `extension` 块引入一个接收者参数以及若干 `def` 成员，这些成员可以在该类型的值上以点号语法调用。编译器会将每个扩展方法翻译成一个普通方法，其第一个参数列表即接收者，因此除普通方法调用外没有任何运行时开销。

## 可表达的约束

**可以为不归你所有的类型附加新操作，并可以令这些操作仅在存在特定类型类证据时才可见。** 普通（无条件）扩展会添加一个始终可用的方法；条件化扩展（带 `using` 子句或上下文绑定的扩展）则添加一个只有当所需 given 实例在作用域内时才可见的方法。这正是把类型类 trait 加上一组 given 实例转变为一等点号语法 API 的机制。

## 最小示例

无条件扩展：

```scala
case class Meters(value: Double)
extension (m: Meters)
  def toFeet: Double = m.value * 3.28084
Meters(10).toFeet // OK -- 32.8084
```

条件化（类型类）扩展：

```scala
trait Ordering[T]:
  def compare(a: T, b: T): Int

extension [T](xs: List[T])(using ord: Ordering[T])
  def sorted: List[T] = xs.sortWith((a, b) => ord.compare(a, b) < 0)
// List(3, 1, 2).sorted -- compiles only when Ordering[Int] is in scope
```

聚合扩展（collective extension），把多个方法分组在一起：

```scala
extension [T](xs: List[T])(using Ordering[T])
  def smallest(n: Int): List[T] = xs.sorted.take(n)
  def largest(n: Int): List[T] = xs.sorted.takeRight(n)
```

## 与其他特性的交互

| 特性 | 如何组合 |
|---|---|
| **Given 实例 / using 子句**（[类型类](type-classes.md)） | 扩展上的 `using` 子句使方法变为条件化。这是定义类型类语法的标准方式（例如 `+` 仅在存在 `Numeric[T]` 时可用）。 |
| **不透明类型**（[newtypes-opaque](newtypes-opaque.md)） | 扩展方法是为不透明类型定义公开 API 的主要手段，因为无法为类型别名添加成员。 |
| **类型类派生**（[derivation](derivation.md)） | 派生出的类型类实例通常配合扩展方法，以点号语法暴露该实例的操作。 |
| **隐式作用域 / 伴生对象** | 定义在伴生对象中（或其中的 given）的扩展方法会被编译器通过隐式作用域查找自动发现，使用者无需 import。 |
| **中缀 / 运算符语法** | 扩展方法可以定义运算符（`<`、`+:` 等）。右结合运算符会交换接收者与参数，符合 Scala 的运算符约定。 |

## 注意事项与局限

- **与已有成员冲突。** 若接收者类型已定义同名成员，则成员永远胜出。扩展方法只在普通成员查找失败后才被尝试。
- **import 歧义。** 在同一嵌套层级从两个来源 import 同名扩展方法会报错——除非其中只有一个 import 能产生良态的展开，此时选择那一个。
- **类型参数位置。** `extension` 关键字上的类型参数只能在以非扩展（前缀）形式调用时显式传递，例如 `sumBy[String](list)(_.length)`。在点号调用形式下只能传递方法自身的类型参数。
- **无法持有状态。** 扩展方法不能添加字段。它们纯粹是外部函数的语法糖。
- **聚合扩展的作用域。** 在聚合 `extension` 块内部，一个扩展方法可以直接调用另一个（接收者被隐式应用），看起来像成员调用，实则是共享接收者的再次应用。
- **软关键字。** `extension` 是软关键字：只有当它出现在语句开头且后跟 `[` 或 `(` 时才被识别为关键字，其它位置都是普通标识符。

## 用例交叉引用

- 类型安全的构建器 API 可使用条件化扩展，见 [非法状态构造](../usecases/invalid-states.md)。
- 不透明类型配合扩展方法形成 newtype 风格的封装，见 [封装](../usecases/encapsulation.md)。
- 通过扩展定义领域专用运算符，见 [编译期](../usecases/compile-time.md)。
- 以扩展语法事后补充类型类实例，见 [可扩展性](../usecases/extensibility.md)。

# 引用

- 原始资料：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T19-extension-methods.md
