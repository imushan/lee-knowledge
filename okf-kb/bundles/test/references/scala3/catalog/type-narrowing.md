---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T14-type-narrowing.md
title: Matchable 与 TypeTest
description: Matchable 限制哪些值可作为模式匹配的 scrutinee，TypeTest 通过显式见证保证对抽象类型的运行时类型检查是可靠的。
tags:
- T14
- Scala 3
- vibe-types
- Matchable
- TypeTest
- 模式匹配
- 抽象类型
- 类型收窄
timestamp: '2026-06-24T12:04:37Z'
---

# Matchable 与 TypeTest

## 简介

`Matchable` 是 Scala 3 类型层级中位于 `Any` 与具体根类 `AnyVal`、`AnyRef` 之间的通用标记 trait，控制哪些值可作为模式匹配的 scrutinee。`TypeTest` 是 `scala.reflect` 中的类型类，提供对抽象类型进行安全、编译器验证的运行时类型检查——取代 Scala 2 中不可靠的 `ClassTag.unapply` 机制。二者分工：`Matchable` 限制模式匹配**在哪里**允许，`TypeTest` 治理对抽象类型的类型检查**如何**可靠地执行。

## 可表达的约束

**`Matchable` 防止模式匹配破坏类型抽象（opaque types、无界类型参数），而 `TypeTest` 通过要求显式见证而非仅依赖擦除的类信息，确保对抽象类型的运行时类型检查是可靠的。**

## 最小示例

### Matchable

```scala
object IArrayDemo:
  opaque type IArray[+T] = Array[? <: T]
  def break(imm: IArray[Int]): Unit =
    imm match
      case a: Array[Int] => a(0) = 1
// Warning: pattern selector should be an instance of Matchable,
// but it has unmatchable type IArray[Int]
```

当需要匹配时，用 `Matchable` 约束类型参数：

```scala
def process[T <: Matchable](x: T): String = x match
  case s: String => s
  case i: Int    => i.toString
  case _         => "other"
```

### TypeTest

```scala
import scala.reflect.TypeTest
trait Peano:
  type Nat
  type Zero <: Nat
  type Succ <: Nat
  given zeroTest: TypeTest[Nat, Zero]
  given succTest: TypeTest[Nat, Succ]
  def safeDiv(m: Nat, n: Succ): (Nat, Nat)

def divOpt(m: Nat, n: Nat)(using TypeTest[Nat, Zero], TypeTest[Nat, Succ]): Option[(Nat, Nat)] =
  n match
    case _: Zero => None        // 安全 —— TypeTest 为检查提供见证
    case s: Succ => Some(safeDiv(m, s))
```

`Typeable[T]` 别名在源类型为 `Any` 时简化上下文边界：

```scala
import scala.reflect.Typeable
def f[T: Typeable]: Boolean =
  "abc" match
    case _: T => true
    case _    => false
f[String] // true
f[Int]    // false
```

## 与其他特性的交互

| 特性 | 交互 |
|------|------|
| **Opaque types** | `Matchable` 的存在正是为了保护 opaque 类型抽象不被通过模式匹配绕过。opaque 类型除非其边界是，否则不是 `Matchable`。参见 [newtypes-opaque](newtypes-opaque.md)。 |
| **无界类型参数** | 仅以 `Any` 为界的类型参数 `T` 不是 `Matchable`。要对其模式匹配，需用 `T <: Matchable` 约束。参见 [generics-bounds](generics-bounds.md)。 |
| **通用相等 / `equals`** | `equals(that: Any)` 重写必须在匹配前将 `that.asInstanceOf[Matchable]`，表明通用相等在抽象类型下本质不可靠。参见 [equality-safety](equality-safety.md)。 |
| **多元相等** | `strictEquality` 与 `Matchable` 互补，将不相关类型间的 `==` 变为编译错误，解决同类抽象破坏问题。 |
| **透明 trait** | `Matchable` 自动被视为透明，因此会从推断的交叉类型中丢弃。参见 [encapsulation](encapsulation.md)。 |
| **ClassTag（遗留）** | `TypeTest` 取代 `ClassTag.unapply`。`ClassTag` 只检查类成分，对参数化或抽象类型不可靠——此类检查会产生 `unchecked` 警告（未废弃）。 |
| **inline match** | `inline match` 在编译期执行类型检查，不需要 `TypeTest` 实例，因为不发生运行时检查。参见 [compile-time-ops](compile-time-ops.md)。 |

## 注意事项与局限

- **`Matchable` 警告受门控。** 在 Scala 3.x 中，该警告需要 `-source future-migration` 或更高。它将在未来版本中成为默认警告。
- **`equals` 与 `Matchable`。** 由于 `equals` 接收 `Any`，每个对 `that` 模式匹配的重写都需要 `that.asInstanceOf[Matchable]`。该转换在运行时总是成功，因为两者都擦除为 `Object`。
- **`TypeTest` 并未完全解决擦除。** 编译器合成的 `TypeTest` 实例在目标类型含有擦除类型参数时（如 `TypeTest[Any, List[Int]]`）可能产生 unchecked 警告。
- **`TypeTest` 在 S 上逆变。** `TypeTest[-S, T]` 意味着 `TypeTest[Any, T]`（即 `Typeable[T]`）可在任何需要 `TypeTest[S, T]` 的地方使用。
- **合成实例。** 当作用域内无显式 `TypeTest` 时，编译器生成一个内部做标准 `isInstanceOf` 类检查的实例，对泛型类型可能 unchecked。
- **`Matchable` 无方法。** 它是纯标记 trait。`getClass` 与 `isInstanceOf` 目前仍在 `Any` 上，但未来可能迁移到 `Matchable`。

## 用例交叉引用

- 保护 opaque 类型不变量不被模式匹配绕过，参见 [封装](../usecases/encapsulation.md)。
- 在 cake 模式或模块系统中对抽象类型成员进行安全的运行时分派，参见 [状态机](../usecases/state-machines.md)。
- 密封层级在内部使用抽象类型时的 ADT 穷尽性，参见 [可空性](../usecases/nullability.md)。
- 在泛型代码中用 `TypeTest` 取代基于 `ClassTag` 的类型检查以保证可靠性，参见 [错误处理](../usecases/error-handling.md)。
- 在严格 Matchable 检查下正确实现 `equals`，参见 [相等性](../usecases/equality.md)。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T14-type-narrowing.md
