---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T57-typestate.md
title: Typestate 编程
description: Scala 3 中利用 phantom 类型参数将对象状态编码到类型层，使方法仅在正确状态下可调用的 typestate 技术。
tags:
- Typestate
- phantom 类型
- '=:'
- 状态机
- builder
- erased
- T57
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:05:14Z'
---

# Typestate 编程

## 简介

Typestate 编程使用**phantom 类型参数**在类型层面编码对象状态，使方法仅在对象处于正确状态时可调用。`Door[Open]` 有 `enter` 方法；`Door[Closed]` 有 `open` 方法。对 `Door[Closed]` 调用 `enter` 是编译期错误，而非运行时异常。

在 Scala 3 中，typestate 通过 **phantom 类型参数**实现——这些类型参数出现在类型签名中但不携带运行时数据。状态迁移返回一个新对象（或同一对象转型到新状态类型）。`=:=` 类型相等证据可将方法约束到特定状态。借助实验性的 **`erased`** 定义特性（`import scala.language.experimental.erasedDefinitions`），phantom 证据参数在代码生成前被剥离，不产生运行时开销。

Typestate 特别适用于 builder 模式、协议强制（如"必须先认证才能查询"）以及资源生命周期管理（如"必须先 open 才能读，必须用后 close"）。

> **Since:** Scala 3.0（phantom 类型自 Scala 2 起；`erased` 定义自 Scala 3.0 起为实验性，需 `import scala.language.experimental.erasedDefinitions`）

## 可表达的约束

**方法仅在 phantom 类型参数匹配所需状态时可调用。编译器拒绝错误状态下的调用，把协议违规变成类型错误。状态迁移产生新类型，使合法的操作序列在类型签名中可见。**

## 最小示例

```scala
sealed trait DoorState
sealed trait Open    extends DoorState
sealed trait Closed  extends DoorState

class Door[S <: DoorState] private ():
  def open(using S =:= Closed): Door[Open]    = Door()
  def close(using S =:= Open): Door[Closed]   = Door()
  def enter(using S =:= Open): Unit           = println("Entering!")

object Door:
  def closed: Door[Closed] = Door()

val d = Door.closed
// d.enter // 错误：Cannot prove that Closed =:= Open
val opened = d.open
opened.enter // OK
```

## 与其他特性的交互

| 特性 | 组合方式 |
|------|----------|
| **类型类 / givens**（见 [type-classes](type-classes.md)） | `=:=` 证据以 given 提供；`using S =:= Open` 是一个上下文参数，类型匹配时编译器自动供给。 |
| **Opaque types**（见 [newtypes-opaque](newtypes-opaque.md)） | 状态标签可用 opaque type，防止外部代码伪造状态证据。 |
| **Erased definitions** | `erased given` 与 `erased` 参数（实验性，自 Scala 3.0 起，经 `erasedDefinitions`）在代码生成前剥离 phantom 证据——不为 `=:=` 见证分配对象。 |
| **Phantom 类型** | Typestate 是 phantom 类型的一种具体应用，phantom 参数编码了一个有限状态机。 |
| **Union / intersection 类型**（见 [union-intersection](union-intersection.md)） | 形如 `Open | HalfOpen` 的联合状态可表示"任一状态均可"，用于在多种状态下工作的方法。 |
| **Tagless final**（见 [tagless-final](tagless-final.md)） | Typestate 可与 tagless final 结合：代数的方法具有 phantom 状态约束签名，并被解释到不同 effect。 |

## 注意事项与局限

1. **状态迁移较冗长。** 每次状态迁移返回新对象（或同一对象重定型），要求调用者重新绑定变量：`val opened = door.open`。不如可变状态符合直觉，但这是编译期安全的代价。
2. **要求线性使用。** 状态迁移后，旧引用仍以旧类型存在，没有机制阻止使用陈旧引用。Rust 的所有权系统可防止这一点；Scala 需要纪律或 lint。
3. **`=:=` 证据默认不 erased。** 不使用实验性 `erased` 特性时，`=:=` 见证是每次调用都分配的真实对象。使用 `erased` 可消除开销，但需注意 `erased` 是实验性（自 Scala 3.0，由 `erasedDefinitions` 控制）。
4. **组合爆炸。** 若对象有多个独立状态维度（如已认证 + 已连接 + 已加密），phantom 类型组合数乘性增长。可考虑分离 phantom 参数或使用类型层状态积。
5. **Builder 模式的重复。** Typestate builder（如 `Builder[HasName, NoAge]`）要求每字段一个 phantom 参数，导致大量类型参数。`scala-newtype` 或基于宏的 builder 可减少样板。

## 新手心智模型

把 typestate 想成**登机牌系统**。你的 `Door[Closed]` 就像候机区登机牌——能候机但不能登机。调用 `open` 把你的牌升级为 `Door[Open]`，允许登机。登机口工作人员（编译器）在放行前检查你的牌类型。你无法伪造登机牌——获得 `Door[Open]` 的唯一途径是对 `Door[Closed]` 调用 `open`。这确保所有人都遵循正确序列。

## 示例 A：带 typestate 的 builder 模式

```scala
sealed trait HasName; sealed trait NoName
sealed trait HasAge;  sealed trait NoAge

class PersonBuilder[N, A] private (name: String, age: Int):
  def withName(n: String)(using N =:= NoName): PersonBuilder[HasName, A] =
    new PersonBuilder(n, age)
  def withAge(a: Int)(using A =:= NoAge): PersonBuilder[N, HasAge] =
    new PersonBuilder(name, a)
  def build(using N =:= HasName, A =:= HasAge): (String, Int) =
    (name, age)

object PersonBuilder:
  def apply(): PersonBuilder[NoName, NoAge] = new PersonBuilder("", 0)

val person = PersonBuilder()
  .withName("Alice")
  .withAge(30)
  .build // OK: ("Alice", 30)
// PersonBuilder().withAge(30).build // 错误：Cannot prove NoName =:= HasName
```

## 示例 B：连接协议强制

```scala
sealed trait Disconnected
sealed trait Connected
sealed trait Authenticated

class Connection[S] private (host: String):
  def connect(using S =:= Disconnected): Connection[Connected] =
    println(s"Connecting to $host")
    Connection(host)
  def authenticate(token: String)(using S =:= Connected): Connection[Authenticated] =
    println(s"Authenticating with $token")
    Connection(host)
  def query(sql: String)(using S =:= Authenticated): String =
    s"Result from $host: [$sql]"
  def disconnect(using S =:= Connected | S =:= Authenticated): Connection[Disconnected] =
    println("Disconnecting")
    Connection(host)

object Connection:
  def create(host: String): Connection[Disconnected] = Connection(host)

val result = Connection.create("db.example.com")
  .connect
  .authenticate("secret")
  .query("SELECT 1")
// 无法在未连接、未认证前查询
```

## 用例交叉引用

- Typestate 使非法状态迁移在类型层无法表达——见 [invalid-states](../usecases/invalid-states.md)。
- Typestate builder 强制所有必填字段在构造前都已设置——见 [builder-config](../usecases/builder-config.md)。
- Phantom 状态参数在类型层追踪资源生命周期（开/关、已认证/未认证）——见 [effect-tracking](../usecases/effect-tracking.md)。
- Typestate 是状态机在类型系统中的规范编码——见 [state-machines](../usecases/state-machines.md)。

# 引用

- Scala 3 参考："Type Equality — `=:=`"
- Scala 3 参考："Erased Definitions"
- Scala 3 参考："Phantom Types"（SIP-35）
- [Scala 3 文档 — Opaque Type Aliases](https://docs.scala-lang.org/scala3/reference/other-new-features/opaques.html)
