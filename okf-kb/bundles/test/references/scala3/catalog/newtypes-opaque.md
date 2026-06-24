---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T03-newtypes-opaque.md
title: 不透明类型别名（Opaque Types）
description: 通过不透明类型别名创建与表示同构但在外部完全抽象的新类型，零运行时开销地防止语义不同值混用。
tags:
- T03
- Scala 3
- vibe-types
- 不透明类型
- newtype
- 零开销
- 抽象屏障
timestamp: '2026-06-24T12:04:03Z'
---

# 不透明类型别名（Opaque Types）

> **引入版本：** Scala 3.0

## 简介

不透明类型别名引入一个新的具名类型：在定义作用域*内部*，它与底层表示完全相同；在该作用域*外部*，它表现为一个完全抽象、互不相关的类型。这带来了包装类的类型安全收益（防止共享表示但语义不同的值被意外混用），且零运行时开销——无装箱、无额外分配、无间接。`opaque` 修饰符可应用于对象、类、trait 的成员或顶层类型别名。

## 可表达的约束

**可以创建与底层运行时表示相同但在外部不可互换的新类型，使混用成为编译期错误，同时不付出任何性能代价。**

在定义作用域内，别名是透明的（可在不透明类型与其表示之间自由赋值）；在外部，别名是不透明的：编译器将其视为抽象类型，仅可见其声明的上下界。这让你精细控制表示与抽象之间的转换在何处被允许，从而由类型系统强制一道抽象屏障。

## 最小示例

```scala
object Units:
  opaque type Meters  = Double
  opaque type Seconds = Double

  object Meters:
    def apply(d: Double): Meters = d   // 内部：透明

  object Seconds:
    def apply(d: Double): Seconds = d

  extension (m: Meters)
    def value: Double = m              // 内部：Meters 即 Double
    def +(other: Meters): Meters = m + other

val d: Units.Meters = Units.Meters(3.0) // OK
// val bad: Double = d                  // 错误：found Meters, required Double
// val wrong: Units.Seconds = d         // 错误：found Meters, required Seconds
```

带边界（子类型关系在外部可见）：

```scala
object Access:
  opaque type Permissions = Int
  opaque type Permission <: Permissions = Int

  val Read: Permission  = 1
  val Write: Permission = 2

  extension (p: Permissions)
    def has(required: Permissions): Boolean = (p & required) == required

// 外部：
val r: Access.Permissions = Access.Read // OK —— Permission <: Permissions
```

## 与其他特性的交互

| 特性 | 组合方式 |
|---|---|
| 扩展方法 | 扩展方法是为不透明类型定义公共 API 的标准方式（因为不能给类型别名添加成员）；在同一作用域内定义扩展可使用透明视图。 |
| [given 实例 / 类型类](type-classes.md) | 可在不透明类型的定义对象内提供类型类实例（如 `Ordering[Meters]`），借助透明别名委托到底层类型的实例。 |
| 隐式转换 | 可定义 `Conversion[Meters, Double]` 以允许外部受控、显式的拓宽，同时保持意外混用为编译错误。 |
| 多重相等 | 标注 `derives CanEqual` 的不透明类型获得自己的相等域；比较 `Meters == Seconds` 需要显式 `CanEqual[Meters, Seconds]` 实例。 |
| [枚举 / ADT](algebraic-data-types.md) | enum 在值层限制取值，不透明类型在类型层限制取值；enum case 包装不透明类型可同时获得两种约束。 |
| [类型类派生](derivation.md) | 不透明类型没有 `Mirror` 实例（它们是别名而非类），派生不直接适用；需手动提供实例或委托到底层类型实例。 |

## 注意事项与局限

- **透明性作用域。** 别名在 enclosing class/object 的 `private[this]` 作用域（或顶层定义的 enclosing 文件）内透明。同一文件内的嵌套对象与类*不能*看穿顶层不透明类型。
- **基于 class 的不透明类型。** 当不透明类型定义在 class（非 object）内时，不同 class 实例产生互不兼容的类型：`log1.Logarithm` 与 `log2.Logarithm` 是不同类型，即便同属一个 class。
- **不能用 context function 作右值。** 不透明类型别名的右侧不能是 context function 类型。
- **不能为 `private`。** 不透明类型别名不能加 `private` 访问修饰符，也不能在子类中被覆盖。
- **不能局部定义。** 不透明类型必须是 class、trait、object 的成员或顶层，不能出现在局部块中。
- **相等转换。** 用 `==` 比较两个不透明类型值，在类型检查后被映射到底层类型（如 `Int`）的相等运算，避免装箱；若期望引用相等语义可能产生意外。
- **transparent inline 方法。** 若不透明类型由定义在不透明作用域内的 `transparent inline` 方法返回，内联返回类型可能以交叉类型（如 `Seconds & String`）泄漏底层表示；建议对返回表达式加显式类型标注。
- **类型参数。** 不透明类型可带单一类型参数列表（`opaque type F[T] = (T, T)` 合法），但不能将类型参数与右侧的 type lambda 组合。

## 用例交叉引用

- [封装](../usecases/encapsulation.md)：为领域基本类型提供零开销包装。
- [编译期](../usecases/compile-time.md)：无运行时开销的量纲。
- 扩展性：在库 API 中封装内部表示。
- [变型](../usecases/variance.md)：带子类型边界的不透明类型实现权限系统。

# 引用

- [T03-newtypes-opaque.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T03-newtypes-opaque.md)
