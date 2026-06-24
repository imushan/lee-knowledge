---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC13-state-machines.md
title: 协议状态机（Protocol State Machines）
description: 在编译期强制合法调用顺序与协议合规，让调用序列违背成为类型错误而非运行时异常。
tags:
- 状态机
- 协议
- 幻影类型
- GADT
- 依赖类型
- 上下文函数
- erased
- Scala 3
- vibe-types
- UC13
timestamp: '2026-06-24T12:06:15Z'
---

# 协议状态机（Protocol State Machines）

## 约束目标

**在编译期强制合法调用顺序与协议合规。**
构建器必须按既定序列被调用；网络通道必须遵循握手协议；资源必须先获取再使用、用后释放。
违背应为类型错误，而非运行时异常。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| GADT | 将协议步骤编码为类型索引的构造器；编译器追踪你处于哪一步 | [T01 algebraic-data-types](../catalog/algebraic-data-types.md) |
| 经由 Opaque 的幻影类型 | 零运行时成本的轻量级状态标签；状态仅存在于类型系统中 | [T03 newtypes-opaque](../catalog/newtypes-opaque.md) |
| 依赖函数类型 | 返回类型依赖于当前协议状态，将状态穿引通过各操作 | [T53 path-dependent-types](../catalog/path-dependent-types.md) |
| 上下文函数（Context functions） | 将能力（如打开的连接）限定在块内，防止其逃逸 | [T42 context-functions](../catalog/context-functions.md) |
| Erased definitions | 在运行时移除状态标签证据，使协议强制真正零开销 | [T27 erased-phantom](../catalog/erased-phantom.md) |

## 模式

### 模式 A：幻影类型状态机（构建器）

使用不透明类型作为状态标签。构建器类型携带其状态，每一步返回处于下一状态的构建器。只有 `Complete` 构建器才能调用 `build`。

```scala
object BuilderState:
  opaque type Empty    = Unit
  opaque type HasName  = Unit
  opaque type HasAge   = Unit
  opaque type Complete = Unit

import BuilderState.*

class PersonBuilder[S]:
  private var name: String = ""
  private var age: Int = 0

  def setName(n: String): PersonBuilder[HasName] =
    name = n
    this.asInstanceOf[PersonBuilder[HasName]]

  def setAge(a: Int)(using S =:= HasName): PersonBuilder[Complete] =
    age = a
    this.asInstanceOf[PersonBuilder[Complete]]

  def build(using S =:= Complete): Person = Person(name, age)

case class Person(name: String, age: Int)

// 用法：
// PersonBuilder[Empty]().setName("Ada").setAge(36).build // 可编译
// PersonBuilder[Empty]().setAge(36)              // 错误：无法证明 S =:= HasName
// PersonBuilder[Empty]().setName("Ada").build    // 错误：无法证明 S =:= Complete
```

### 模式 B：协议步骤的 GADT 编码

将协议编码为 GADT，每个构造器代表一个步骤。类型参数追踪当前状态，序列化通过对 GADT 的匹配来强制。

```scala
enum State:
  case Disconnected, Connected, Authenticated

enum Protocol[S <: State, Next <: State]:
  case Connect(host: String)
    extends Protocol[State.Disconnected.type, State.Connected.type]
  case Auth(token: String)
    extends Protocol[State.Connected.type, State.Authenticated.type]
  case Query(sql: String)
    extends Protocol[State.Authenticated.type, State.Authenticated.type]
  case Disconnect()
    extends Protocol[State.Authenticated.type, State.Disconnected.type]

def run[S <: State, N <: State](step: Protocol[S, N]): Unit = step match
  case Protocol.Connect(h)  => println(s"connecting to $h")
  case Protocol.Auth(t)     => println("authenticating")
  case Protocol.Query(sql)  => println(s"running: $sql")
  case Protocol.Disconnect() => println("disconnecting")

// 类型参数阻止：在 Connect 之前 Auth、在 Auth 之前 Query 等。
```

### 模式 C：会话类型通道的依赖类型

对 send/recv 操作建模，其类型依赖于协议位置。依赖函数类型让 `next` 返回一个状态由当前步骤决定的通道。

```scala
// 通道以当前协议步骤 S 参数化，S 作为值可用。
trait Channel[S]:
  val proto: S

trait Send[A]:
  type After
trait Recv[A]:
  type After

object Session:
  type Step1 = Send[String] { type After = Step2 }
  type Step2 = Recv[Int]    { type After = Done }
  type Done  = Unit

// `ch.proto.After` 是通过值 `ch` 读取的路径依赖类型：
// 下一个通道的状态由当前协议步骤计算得出。
// 约束允许仅当步骤是 `Send` 时调用 `send`、仅当是 `Recv` 时调用 `recv`。
def send[A](ch: Channel[? <: Send[A]], msg: A): Channel[ch.proto.After] = ???
def recv[A](ch: Channel[? <: Recv[A]]): (A, Channel[ch.proto.After]) = ???

// 每次操作后通道的类型由协议计算，
// 在编译期阻止乱序的 send/recv。
```

### 模式 D：用上下文函数实现作用域资源协议

上下文函数将能力限定在某个块内。资源在块前打开、块后关闭，且能力令牌无法逃逸。

```scala
import scala.language.experimental.erasedDefinitions

// 能力标记。作为下面的 `erased using` 参数，它零运行时成本——
// 令牌仅存在于类型检查期间。
final class CanUseDb

class DbConnection:
  def query(sql: String)(using erased CanUseDb): List[String] = List(s"result of $sql")
  def execute(sql: String)(using erased CanUseDb): Int = 1

def withDb[A](connStr: String)(block: CanUseDb ?=> A): A =
  val conn = openConnection(connStr)
  try
    given CanUseDb = CanUseDb()
    block
  finally
    conn.close()

def openConnection(s: String): java.io.Closeable = () => ()

// 用法：
@main def demo(): Unit =
  withDb("jdbc:...") {
    val rows = DbConnection().query("SELECT 1")
    val n    = DbConnection().execute("INSERT ...")
  }
// 在 withDb 之外，作用域内没有 CanUseDb——query/execute 无法编译。
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 幻影状态标签 | 用 `Nothing` 居住类型的 sealed trait 层次；每个状态需要一个类，无法保证被擦除 | 不透明类型：零成本，不生成类。也可用 erased definitions |
| GADT 协议 | GADT 在 Scala 2 的 `match` 中可用，但穷尽性检查较弱，GADT 分支内的类型推断脆弱 | 完整的 GADT 支持与可靠的穷尽性。enum 语法让协议 ADT 简洁 |
| 依赖类型 | 通过 `val`/`type` 成员的路径依赖类型，需要对象风格编码。无依赖*函数*类型 | 依赖函数类型（`(x: X) => x.T`）是一等的，简化会话类型编码 |
| 作用域能力 | 用隐式参数传递能力令牌，但无上下文函数语法且无擦除 | 上下文函数（`T ?=> U`）将能力限定在块内。`erased` 移除运行时开销 |

## 何时选择哪个特性

| 如果你需要…… | 推荐 |
|---|---|
| 一个 3-6 状态的线性构建器 | **经 opaque 的幻影类型**（模式 A）。最轻量的编码，零运行时成本 |
| 带分支或循环的复杂协议 | **GADT**（模式 B）。每个构造器是一步；编译器检查穷尽性 |
| 依赖于当前状态的返回类型 | **依赖函数类型**（模式 C）。让协议计算下一个通道类型 |
| 确保资源仅在某作用域内使用 | **上下文函数 + erased**（模式 D）。能力无法逃逸出块 |
| 绝对的零开销状态追踪 | 组合 **不透明类型** 与 **erased definitions**，使标签和证据仅存在于编译期 |

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC13-state-machines.md
- 相关用例：[builder-config](builder-config.md)、[effect-tracking](effect-tracking.md)
