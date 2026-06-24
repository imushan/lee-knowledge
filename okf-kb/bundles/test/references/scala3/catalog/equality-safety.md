---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T20-equality-safety.md
title: 多元宇宙相等性（Multiversal Equality）
description: 通过二元类型类 CanEqual[L, R] 限定哪些类型对可以用 == 或 != 比较，使语义上无意义的跨类型比较在编译期被拒绝。
tags:
- T20
- Scala 3
- vibe-types
- 相等性
- CanEqual
- strictEquality
timestamp: '2026-06-24T12:03:42Z'
---

# 多元宇宙相等性（Multiversal Equality）

**起始版本：** Scala 3.0

## 简介

多元宇宙相等性是 Scala 通用 `==`/`!=` 运算符的一种可选增强，它使用二元类型类 `CanEqual[L, R]` 来控制哪些类型对可以被比较。在标准 Scala（以及 Java）中，任意两个引用都可以被比较，这会默默接受诸如 `"hello" == 42` 这类无意义的比较。多元宇宙相等性把这种比较变成编译期错误（对声明了 `CanEqual` 实例的类型而言），同时对尚未开启该机制的类型保持完全向后兼容。

## 可表达的约束

**可以限制 `==` 与 `!=`，使只有语义上有意义的比较才能通过编译，在编译期捕获偶然的跨类型相等性检查。** 一旦某类型拥有自反的 `CanEqual` 实例（通过 `derives CanEqual` 或 given 定义），涉及该类型的比较就会被检查：`x == y` 仅当存在类型 `T`、`U` 对应的 `CanEqual[T, U]` 实例时才编译通过。启用 `strictEquality` 会把这一约束扩展到所有类型，彻底移除向后兼容的回退路径。

## 最小示例

```scala
class Name(val value: String) derives CanEqual
val a = Name("Alice")
val b = Name("Bob")
a == b        // OK -- CanEqual[Name, Name] exists
a == "Alice"  // error: Values of types Name and String cannot be compared
```

开启跨类型比较：

```scala
given CanEqual[Int, Long] = CanEqual.derived
42 == 42L // OK
```

完整严格模式：

```scala
import scala.language.strictEquality
1 == 1 // error unless CanEqual[Int, Int] is in scope
```

## 与其他特性的交互

| 特性 | 如何组合 |
|---|---|
| **类型类派生**（[derivation](derivation.md)） | `derives CanEqual` 会生成左右类型参数相互独立的实例，例如 `CanEqual[Box[T], Box[U]]` 要求 `CanEqual[T, U]`，从而把安全相等性传播到泛型包装之中。 |
| **枚举与 ADT**（[algebraic-data-types](algebraic-data-types.md)） | 给枚举加 `derives CanEqual` 可确保同枚举的不同 case 之间可比较，但与无关类型的比较会被拒绝。 |
| **Given 实例**（[type-classes](type-classes.md)） | 可通过显式 given 定义非对称相等性（如 `CanEqual[A, B]` 与 `CanEqual[B, A]`），精确控制哪些跨类型比较被允许。 |
| **不透明类型**（[newtypes-opaque](newtypes-opaque.md)） | 派生 `CanEqual` 的不透明类型会获得独立的相等性域，与其底层表示类型互不相干。 |
| **集合操作** | `CanEqual` 可以传入 `contains`、`indexOf`、`diff` 等方法（通过 `using CanEqual[T, U]` 参数），避免用不可能匹配的参数类型调用它们。 |

## 注意事项与局限

- **向后兼容的回退路径。** 在未启用 `strictEquality` 时，任何两个都缺少 `CanEqual` 实例的类型仍可自由比较。安全网只在至少一方开启时才激活。这是为迁移而设计的，但也意味着遗留类型得不到保护。
- **双类型参数必不可少。** `CanEqual` 取 `[L, R]` 而非单 `[T]`，是为了支持回退规则（"双方都没有自反实例"）。单参数设计会使 `Any` 回退永远可用，违背初衷。
- **预定义实例。** 标准库为数值类型、`Boolean`、`Char`、`Seq`、`Set`、`Null` 提供了 `CanEqual` 实例。数值类型可跨类型比较（如 `Int` 与 `Long`）。两个 `Seq` 子类型在其元素类型可比较时可比较。
- **提升规则。** 未启用 `strictEquality` 时，编译器会先对类型做提升（把协变位置上的抽象类型替换为上界）再判断基于子类型的兼容性，这可能放行表面看似无关的比较。
- **无运行时影响。** `CanEqual` 实例只服务于类型检查器。运行时 `==` 仍照常分派到 `equals`。
- **迁移路径。** 推荐先为自己的类型加 `derives CanEqual`（即便不启用 `strictEquality` 也安全），待生态追上后再全项目启用 `strictEquality`。

## 用例交叉引用

- 在领域模型中防止偶然的相等性比较，见 [领域建模](../usecases/domain-modeling.md)。
- ADT 层级的安全相等性，见 [状态机](../usecases/state-machines.md)。
- 用类型安全的相等性加固集合查找，见 [方差](../usecases/variance.md)。

# 引用

- 原始资料：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T20-equality-safety.md
