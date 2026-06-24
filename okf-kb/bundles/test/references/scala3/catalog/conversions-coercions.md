---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T18-conversions-coercions.md
title: 隐式转换、by-name 上下文参数与 deferred givens
description: 通过 Conversion 类型类控制隐式拓宽、用 by-name 上下文参数打破循环 given 依赖、用 deferred givens
  跨 trait 层级传播类型类要求。
tags:
- T18
- Scala 3
- vibe-types
- 隐式转换
- Conversion
- by-name 上下文参数
- deferred givens
- magnet 模式
timestamp: '2026-06-24T12:06:33Z'
---

# 隐式转换、by-name 上下文参数与 deferred givens

## 简介

本文档涵盖三个相关机制，用于控制编译器如何解析与提供隐式证据：

- **隐式转换**在 Scala 3 中是 `scala.Conversion[-T, +U]` 抽象类的 given 实例。当编译器遇到需要 `U` 却给出 `T`（或 `T` 无成员 `m` 但 `U` 有）时，自动应用转换。与 Scala 2 的 `implicit def` 不同，`Conversion` 类型类使转换显式、可发现且受导入控制。
- **by-name 上下文参数**（`using` 子句中的 `=> T`）让编译器推迟 given 参数求值，关键是能在隐式搜索中打破循环。合成的参数仅在自引用会导致发散时由局部 `lazy val` 支撑。
- **deferred givens**（`given T = deferred`）允许 trait 声明一个 given，其实现由任何继承类自动填充——或转发构造器提供的 using 参数，或在子类作用域中隐式搜索。

## 可表达的约束

**你可以控制隐式拓宽（哪些类型可静默转换为哪些类型）、用惰性证据打破循环 given 依赖，并在无样板代码的情况下通过 trait 层级传播类型类要求。**

- `Conversion[T, U]` 约束编译器可执行*哪些*自动强制转换：仅有显式 given 实例支撑的。
- by-name 上下文参数约束证据*何时*被物化，允许递归或相互依赖的 given 结构（如 `Codec[Option[T]]` 依赖 `Codec[T]`）终止。
- deferred givens 约束 given *在哪里*被提供：trait 声明要求；实现类满足——显式或由编译器从类自身作用域合成。

## 最小示例

**隐式转换：**

```scala
case class Token(value: String)
given Conversion[String, Token] = Token(_)

val t: Token = "hello" // OK —— 应用 Conversion[String, Token]
```

**by-name 上下文参数：**

```scala
trait Codec[T]:
  def write(x: T): Unit

given intCodec: Codec[Int] = ???
given optionCodec: [T] => (ev: => Codec[T]) => Codec[Option[T]]:
  def write(xo: Option[T]) = xo match
    case Some(x) => ev.write(x) // ev 按需求值
    case None    =>
```

**deferred given：**

```scala
trait Ord[A]:
  def compare(x: A, y: A): Int

trait Sorted:
  type Element : Ord // 脱糖为：given Ord[Element] = deferred

class SortedSet[A : Ord] extends Sorted:
  type Element = A
  // 编译器自动填充：override given Ord[Element] = summon[Ord[A]]
```

## 与其他特性的交互

| 特性 | 组合方式 |
|------|----------|
| **given 实例 / using 子句**（见 [type-classes](type-classes.md)） | `Conversion` 实例是 given，遵循所有常规作用域、导入与优先级规则。by-name 上下文参数是 `using` 子句上的修饰符。 |
| **extension 方法**（见 [extension-methods](extension-methods.md)） | 当 `T` 无成员 `m` 时，编译器尝试 extension 方法*和*隐式转换到带 `m` 的类型。转换在 extension 失败后尝试。 |
| **opaque types**（见 [newtypes-opaque](newtypes-opaque.md)） | 可从 opaque 类型的伴生对象定义 `Conversion`，允许受控拓宽同时保持底层类型隐藏。 |
| **类型类派生**（见 [derivation](derivation.md)） | 递归派生（如为递归 ADT 派生 `Eq`）依赖 by-name 上下文参数防止隐式搜索发散。 |
| **trait 中的上下文边界** | 抽象类型成员上的上下文边界脱糖为 deferred givens，让 trait 声明类型类要求，子类通过自身构造器参数满足。 |

## 注意事项与局限

### 转换

- **导入要求。** 使用 `Conversion` 实例触发特性警告，除非导入 `scala.language.implicitConversions`（或设置 `-language:implicitConversions` 标志）。
- **三个触发点。** 转换在类型不匹配、缺失成员与不可应用成员时触发。与 Scala 2 相同，但 `Conversion` 类型类使机制更可见。
- **magnet 模式。** 转换可通过“magnet”枚举模拟重载，在正常重载不可能时（如 erased 泛型参数）有用。

### by-name 上下文参数

- **非立即可用。** 搜索期间创建的占位 given 不是当前层级隐式解析的候选。它仅在*嵌套* by-name 搜索中可用。这正是阻止无限循环的机制。
- **仅在需要时用 lazy val。** 编译器仅在展开自引用时用 `lazy val` 支撑合成参数；否则直接求值。

### deferred givens

- **需要 override 修饰符。** 由于 `deferred` 算作具体右侧，子类中任何显式实现必须用 `override`。
- **取代抽象 given。** 抽象 given（无体的 `given name: T`）仍受支持，但自 Scala 3.6 起被视为被 deferred givens 取代。
- **搜索作用域。** 合成实现在继承类由其参数增强的环境中搜索，但*不*在其自身成员中（以避免循环解析）。

## 用例交叉引用

- newtype 与底层表示之间的受控强制转换，参见 [封装](../usecases/encapsulation.md)。
- 带 by-name 证据的递归编解码器派生，参见 [效果追踪](../usecases/effect-tracking.md)。
- 通过 deferred givens 实现 trait 级类型类要求，参见 [相等性](../usecases/equality.md)。
- 带 Conversion 实例的 magnet 模式 API，参见 [类型算术](../usecases/type-arithmetic.md)。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T18-conversions-coercions.md
