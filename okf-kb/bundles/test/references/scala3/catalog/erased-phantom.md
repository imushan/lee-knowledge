---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T27-erased-phantom.md
title: 抹除定义（Erased Definitions / Phantom Evidence）
description: 用 erased 修饰参数或 val 使其仅存在于编译期并在代码生成前被完全抹除，实现零成本的类型级证据与幻影类型状态机。
tags:
- T27
- Scala 3
- vibe-types
- erased
- 抹除定义
- 幻影类型
- 零开销证据
- CanThrow
timestamp: '2026-06-24T12:05:56Z'
---

# 抹除定义（Erased Definitions / Phantom Evidence）

**状态：** Experimental | **起始版本：** Scala 3.0

## 简介

抹除定义是一项实验性特性（`import scala.language.experimental.erasedDefinitions`），允许把参数与 `val` 定义标记为 `erased`，表示它们只存在于编译期，并在代码生成之前被完全移除。一个 erased 参数充当编译期证据——编译器验证它可以被构造，但运行时永远不会分配或传递任何对象。这使得零成本的类型级编程成为可能：类型类见证、状态机令牌、能力标记等证据类型完全不携带运行时开销。

## 可表达的约束

**一个函数可以要求任意类型级性质的编译期证明（证据），而无需为该证明付出任何运行时代价。** `erased` 修饰符保证证据值在编译期被检查后即被彻底剥离，生成的字节码中不留任何证据参数的痕迹。

## 最小示例

```scala
import scala.language.experimental.erasedDefinitions

// State machine: only valid transitions compile
sealed trait State
final class On extends State
final class Off extends State

class IsOff[S <: State]
object IsOff:
  inline given IsOff[Off]()
class IsOn[S <: State]
object IsOn:
  inline given IsOn[On]()

class Machine[S <: State]:
  def turnOn (using erased IsOff[S]): Machine[On]  = Machine[On]()
  def turnOff(using erased IsOn[S]):  Machine[Off] = Machine[Off]()

@main def test =
  val m  = Machine[Off]()
  val m1 = m.turnOn    // ok
  val m2 = m1.turnOff  // ok
  // m1.turnOn   // error: State must be Off
  // m2.turnOff  // error: State must be On
```

运行时 `turnOn` 与 `turnOff` 不接收任何参数——`IsOff`/`IsOn` 证据被抹除。

## 与其他特性的交互

- **Given 实例与上下文绑定。** erased 参数与 `using` 子句天然协作。当某类型类继承 `compiletime.Erased` 时，其实例被隐式抹除，因此上下文绑定如 `[T: CanSerialize]` 会展开为 `(using erased CanSerialize[T])`。
- **Inline 与纯表达式。** 传给 erased 参数的实参必须是 _纯表达式_（常量、非惰性不可变 val、或无初始化器的构造器应用）。内联后的 inline given 满足该要求，这正是 erased 证据通常使用 `inline given` 的原因。
- **`CanThrow` 能力。** 用于更安全异常的 `CanThrow[E]` 类继承 `Erased`，使异常能力在运行时零开销。
- **`CanEqual`（多元宇宙相等性）。** 用于相等性检查的 `CanEqual` 证据是成为 `Erased` 的候选，可移除其运行时足迹。
- **函数类型。** erased 参数反映在函数类型中：`(erased T, U) => R` 与 `(T, U) => R` 是不同类型，二者之间无子类型关系。
- **重写。** erased 与非 erased 参数在重写时必须精确匹配；不能在重写中把参数从 erased 改为非 erased 或反之。

## 注意事项与局限

1. **纯度要求。** 传给 erased 参数的实参必须是纯的。有副作用的表达式、非 inline 方法调用、惰性 val 都会被拒绝。这防止了通过 `null.asInstanceOf[Evidence]` 或递归定义来"伪造"证据。
2. **不能在计算中使用 erased 值。** erased 参数不能出现在非 erased 表达式中。它只能被转发给另一个 erased 参数，或用于依赖类型的路径中。
3. **不支持 `lazy val`、`var`、`object`。** `erased` 修饰符不能出现在惰性 val、可变变量或 object 定义上。
4. **不能传名调用。** erased 参数不能是传名的（`erased` 不能与 `=> T` 组合）。
5. **多态函数字面量。** 带 erased 参数的多态函数字面量尚不支持（实现限制）。
6. **`erasedValue` vs `unsafeErasedValue`。** `compiletime.erasedValue[T]` 是一个必须在内联中被消除的 erased 引用；它不是纯表达式，不能作为 erased 证据保留。逃生口 `scala.caps.unsafe.unsafeErasedValue[T]` 被视为纯，但仅应在安全性可由其它手段证明时使用。
7. **抹除后的重载冲突。** 仅在 erased 参数上不同的方法在抹除后可能发生签名冲突，因为 erased 参数会被移除。

## 用例交叉引用

- 类型类证据（如 `CanEqual`、`Ordering`）可被抹除以实现零开销约束，见 [编译期](../usecases/compile-time.md)。
- 显式 null：erased 能力与 null 安全类型组合实现全面的静态检查，见 [可空性](../usecases/nullability.md)。
- `CanThrow` 能力用于更安全的异常是抹除定义的旗舰用例，见 [错误处理](../usecases/error-handling.md)。
- 幻影类型/状态机用 erased 证据以零运行时代价强制合法状态转换，见 [状态机](../usecases/state-machines.md)。

# 引用

- 原始资料：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T27-erased-phantom.md
