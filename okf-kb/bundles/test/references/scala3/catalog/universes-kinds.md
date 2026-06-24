---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T35-universes-kinds.md
title: Kind 多态 (Universes & Kinds)
description: Scala 3 通过 AnyKind 上界允许类型参数跨任意 kind 抽象，可统一处理正当类型、一阶与高阶类型构造器。
tags:
- Scala 3
- vibe-types
- T35
- kind 多态
- AnyKind
- 高阶类型
- Type
timestamp: '2026-06-24T12:06:51Z'
---

# Kind 多态 (Universes & Kinds)

> **引入版本：** Scala 3.0

## 简介

Scala 3 的 kind 多态允许类型参数跨越任意 kind 的类型——正当类型（如 `Int`）、一元类型构造器（如 `List`）、二元类型构造器（如 `Map`）或任何高阶形状。这通过特殊类型 `scala.AnyKind` 实现，可作为类型参数的上界。以上界为 `AnyKind` 约束的类型参数称为 **any-kinded 类型**，可接受任意 kind 的类型实参，从而实现跨 kind 谱系的统一抽象。

## 可表达的约束

**`AnyKind` 让你编写对其类型参数的 *kind* 泛型的定义——你可以抽象掉某物是正当类型、`* -> *` 构造器、`* -> * -> *` 构造器还是其他形状，而不绑定到特定元数。**

## 最小示例

```scala
import scala.reflect.TypeTest

// 适用于任意 kind 类型的类型标签
def typeInfo[T <: AnyKind]: String =
  "some type"

typeInfo[Int]             // T 是正当类型（kind: *）
typeInfo[List]            // T 是一元构造器（kind: * -> *）
typeInfo[Map]             // T 是二元构造器（kind: * -> * -> *）
typeInfo[[X] =>> String]  // T 是类型 lambda（kind: * -> *）
```

一个更实用的例子——跨 kind 工作的通用 `TypeTag` 式 given：

```scala
// quotes 系统中的 Type[T] 已经使用了 AnyKind：
// abstract class Type[T <: AnyKind]
// 这使 Type 可以统一表示 Int、List、Map 等。
import scala.quoted.*
def showType[T <: AnyKind : Type](using Quotes): String =
  Type.show[T]
```

## 与其他特性的交互

| 特性 | 交互方式 |
|---|---|
| **`Type[T]`（quotes）** | `Type` 被声明为 `Type[T <: AnyKind]`，这是 kind 多态的标准用例。它允许宏统一处理类型、类型构造器与高阶类型。 |
| **given 实例 / 类型类** | kind 多态允许定义适用于任意 kind 类型的 given 实例。例如通用 `Type.of` given 定义为 `given of: [T <: AnyKind] => Quotes => Type[T]`。 |
| **match 类型** | match 类型 scrutinee 可以是任意 kind 的，允许按类型实参的 kind 进行分派。 |
| **类型 lambda** | 类型 lambda（`[X] =>> F[X]`）产生的高阶类型可传给任意 kind 参数。 |
| **不透明类型** | 不透明类型可以有任意 kind 上界，尽管实践中很少需要。 |
| **子类型** | `AnyKind` 是所有类型的超类型（无论其 kind）。它与所有其他类型 kind 兼容，但没有类型参数也没有成员。 |

## 注意事项与局限

- **使用严重受限。** any-kinded 类型变量不能用作值的类型，不能用类型参数实例化，也不能出现在需要正当类型的位置。你唯一能做的是把它传给另一个 any-kinded 类型参数。
- **没有成员。** `AnyKind` 是一个合成的类，完全没有成员。它不能被实例化或继承（`abstract final`）。
- **在通常意义上不是 `Any` 的超类型。** 虽然 `AnyKind` 在 kind 层级中位于所有类型之上，但正常类型层级（`Any`、`AnyVal`、`AnyRef`）是独立的。`AnyKind` 是一个由编译器处理的特殊构造。
- **隐式解析限制。** 由于 any-kinded 类型没有结构，隐式搜索无法检查它。有用的模式通常需要把 `AnyKind` 上界与其他机制（如宏中的 `Type` 实例）结合。
- **`-Yno-kind-polymorphism` 标志已废弃**，自 Scala 3.7.0 起无效并将被移除。kind 多态现在是稳定特性。

## 从 Lean 迁移

Scala 的 `AnyKind` 大致对应 Lean 的 `Sort u`——两者都允许类型参数跨越任意 "层级"。但 Lean 的 universe 层级是本质性的（防止悖论），而 Scala 的 kind 多态是便利特性。Lean 有 `Prop : Sort 0`、`Type 0 : Sort 1`、`Type 1 : Sort 2` 等。Scala 有 `Type`（正当类型）和 `AnyKind`（任何东西），但没有无限层级。

## 用例交叉引用

- 见 [状态机](../usecases/state-machines.md)：需要通过 `Type[T <: AnyKind]` 表示与操作任意 kind 类型的宏库。
- 见 [类型算术](../usecases/type-arithmetic.md)：对类型构造器元数抽象的泛型类型级编程。
- 见 [编译期](../usecases/compile-time.md)：使用 `type f[X]; f` 模式对高阶类型进行 quote 模式匹配。
- 见 [可扩展性](../usecases/extensibility.md)：定义跨所有 kind 工作的通用类型标签或类型见证。

# 引用

- [Scala 3 Reference: Kind Polymorphism](https://docs.scala-lang.org/scala3/reference/other-new-features/kind-polymorphism.html)
- [Scala API: AnyKind](https://www.scala-lang.org/api/3.x/scala/AnyKind.html)
