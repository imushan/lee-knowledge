---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T06-derivation.md
title: 类型类派生（Type-Class Derivation）
description: 通过 derives 子句让编译器基于类型的编译期结构自动生成类型类实例，免除手写模板并保证结构一致性。
tags:
- T06
- Scala 3
- vibe-types
- 类型类派生
- derives
- Mirror
- 编译期生成
timestamp: '2026-06-24T12:05:06Z'
---

# 类型类派生（Type-Class Derivation）

> **引入版本：** Scala 3.0

## 简介

类型类派生是一种编译器支持机制，可为代数数据类型自动生成类型类的 given 实例。在类、trait、enum 或 object 上写 `derives TC`，编译器会在伴生对象中生成一个委托给 `TC.derived` 的 given 定义。`derived` 方法通常通过 `Mirror` 实例——编译器生成的、对类型积字段或和备选项的类型级描述——在编译期检查类型结构，无需数据类型作者编写任何模板即可组装出正确的类型类实现。

## 可表达的约束

**可以要求每个声明了派生的积/和类型都存在类型类实例，其实现完全由类型的编译期结构生成。** `derives` 子句转移了义务：无需手写 `Eq[MyTree]`、`Ordering[MyTree]` 或 `Show[MyTree]` 的 given，而是声明意图并让编译器合成实例。这保证结构一致性——派生实例始终反映当前字段或 case 集合——且当构成类型缺少所需实例时在编译期失败。

## 最小示例

```scala
// 带有 derived 入口点的类型类 trait
trait Eq[T]:
  def eqv(x: T, y: T): Boolean

object Eq:
  // 'derived' 借助 Mirror 生成实现
  inline def derived[T](using scala.deriving.Mirror.Of[T]): Eq[T] = ??? // macro 或 inline 逻辑

// 数据类型选择加入
enum Tree[T] derives Eq:
  case Leaf(value: T)
  case Branch(left: Tree[T], right: Tree[T])

// 编译器在 Tree 的伴生对象中生成：
// given [T: Eq] => Eq[Tree[T]] = Eq.derived
```

为不归你所有的类型手动派生：

```scala
// `Option` 在标准库中——无法为其添加 `derives` 子句，故手写实例。
given [T: Ordering] => Ordering[Option[T]] =
  (a, b) =>
    (a, b) match
      case (None, None)       => 0
      case (None, Some(_))    => -1
      case (Some(_), None)    => 1
      case (Some(x), Some(y)) => summon[Ordering[T]].compare(x, y)
```

## 与其他特性的交互

| 特性 | 组合方式 |
|---|---|
| Mirror 类型 | `Mirror.Product` 暴露字段类型（`MirroredElemTypes`）与标签；`Mirror.Sum` 暴露 case 类型与 `ordinal` 方法。派生逻辑对这些 mirror 做模式匹配以按结构构建实例。 |
| inline / 元编程 | `derived` 方法通常为 `inline def`，使用 `inline match`、`summonInline`、`erasedValue` 在编译期递归遍历以元组编码的元素类型。 |
| [枚举与 ADT](algebraic-data-types.md) | `derives` 在 `enum` 上尤为自然：编译器为 enum 生成 `Mirror.Sum`，为每个 case 生成 `Mirror.Product`，实现全自动派生。 |
| [上下文边界 / given 实例](type-classes.md) | 当类型类参数 kind 为 `*` 时，`Tree[T]` 的派生实例自动要求 `[T: TC]`，将约束沿类型结构向下传播。 |
| CanEqual | `CanEqual` 有特殊派生规则：生成带有独立左右类型参数的双参数实例，支持在 sum 层级内的跨类型相等检查。 |

## 注意事项与局限

- **Mirror 可用性。** Mirror 自动为 enum、enum case、case object 及（有条件地）case class 与密封层级生成。非密封 trait、无可见构造器的 class 与 Java class 无法合成 mirror。
- **递归类型。** `derived` 中的 lazy `val` 模式（如 `lazy val elemInstances = ...`）对防止积字段反向引用外围和类型时的无限展开至关重要。
- **编译期开销。** 因 `derived` 通常为 `inline`，在大量类型上重度使用会增加编译时间；Shapeless 3 等库通过摊销 inline 工作来缓解。
- **仅单一类型参数。** 标准派生适用于单一类型参数的类型类（外加 `CanEqual` 特例）；多参数类型类无法通过内建机制派生。
- **kind 匹配。** 当类型类参数与派生类型 kind 不同时，编译器使用 type lambda 对齐；kind 结构复杂时可能产生意外的生成签名。
- **默认无运行时足迹。** Mirror 类型成员是纯类型，无运行时表示，除非被显式使用；这使实例在编译期解析时保持零开销。

## 推荐库

| 库 | 作用 | 链接 |
|---|---|---|
| circe-generic | 通过 `derives ConfiguredCodec` 为 case class 与 enum 自动派生 JSON 编解码 | [circe.github.io/circe](https://circe.github.io/circe/) |
| tapir | 从 case class schema 派生端点；生成 OpenAPI 文档与服务端/客户端代码 | [tapir.softwaremill.com](https://tapir.softwaremill.com/) |
| magnolia | 轻量、快速的类型类派生，无宏复杂度；编译期开销极小 | [github.com/softwaremill/magnolia](https://github.com/softwaremill/magnolia) |

## 用例交叉引用

- 为领域模型自动派生编解码（JSON、二进制），参见[效果追踪](../usecases/effect-tracking.md)。
- ADT 的结构相等与排序，参见[状态机](../usecases/state-machines.md)。
- 面向积/和形状的泛型编程，用于空安全。
- 从 case class mirror 在编译期生成 schema，参见[序列化](../usecases/serialization.md)。

# 引用

- [T06-derivation.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T06-derivation.md)
