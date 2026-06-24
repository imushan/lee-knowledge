---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC01-invalid-states.md
title: 屏蔽非法状态
description: 在编译期让非法状态不可表达，使任何能够构造出来的值都天然合法，从而消除运行时校验。
tags:
- UC01
- Scala 3
- vibe-types
- 非法状态
- 代数数据类型
- 不透明类型
- 幻影类型
- GADT
timestamp: '2026-06-24T12:07:15Z'
---

# 屏蔽非法状态

## 约束目标

让非法状态在编译期不可表达（make illegal states unrepresentable）。只要某个值能够被构造出来，它就一定是合法的——无需运行时检查，也不会出现非法的组合。状态空间的封闭由类型系统强制保证，而非靠纪律或测试。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| Enums / ADTs / GADTs | 封闭层级，编译器强制穷尽匹配 | [代数数据类型](../catalog/algebraic-data-types.md) |
| 不透明类型 | 在相同底层表示上构造互不兼容的独立类型 | [不透明类型](../catalog/newtypes-opaque.md) |
| 联合类型 | 表达“多选一”而无需共同父类型 | [联合与交集类型](../catalog/union-intersection.md) |
| 匹配类型 | 在类型层面计算类型、按类型细化 | [匹配类型](../catalog/match-types.md) |
| erased 定义 | 零运行时成本的幻影值 | [erased/phantom](../catalog/erased-phantom.md) |
| inline | 编译期求值与分支 | [编译期运算](../catalog/compile-time-ops.md) |

## 模式

### 1 — 用 ADT 封闭状态空间并穷尽匹配

用 `enum` 关闭状态空间，编译器会拒绝不完整的匹配。

```scala
enum PaymentStatus:
  case Pending
  case Charged(receiptId: String)
  case Refunded(reason: String)
  case Failed(error: String)

def nextAction(s: PaymentStatus): String = s match
  case PaymentStatus.Pending      => "charge the card"
  case PaymentStatus.Charged(id)  => s"send receipt $id"
  case PaymentStatus.Refunded(_)  => "close ticket"
  case PaymentStatus.Failed(err)  => s"alert ops: $err"
// 删除任一分支都是编译告警（在 -Werror 下为错误）
```

### 2 — 用幻影类型跟踪状态机

把协议的状态机编码进类型系统，跳过步骤的转换无法编译。

```scala
sealed trait DoorState
sealed trait Open extends DoorState
sealed trait Closed extends DoorState
sealed trait Locked extends DoorState

class Door[S <: DoorState] private ():
  def close(using S =:= Open): Door[Closed] = new Door()
  def lock(using S =:= Closed): Door[Locked] = new Door()
  def unlock(using S =:= Locked): Door[Closed] = new Door()
  def open(using S =:= Closed): Door[Open] = new Door()

object Door:
  def apply(): Door[Closed] = new Door()

val d = Door()    // Door[Closed]
val ok = d.lock   // Closed -> Locked，编译通过
// d.open.lock    // 编译错误 —— 不能锁一扇 Open 的门
// d.lock.lock    // 编译错误 —— 已 Locked，不是 Closed
```

### 3 — 用不透明类型防止值被混用

两个 ID 共享相同的运行时表示，但在编译期互不兼容。

```scala
import scala.annotation.targetName

object ids:
  opaque type UserId = Long
  opaque type OrderId = Long
  object UserId:
    def apply(v: Long): UserId = v
  object OrderId:
    def apply(v: Long): OrderId = v

  // 两个 extension 擦除后都是 (Long): Long，因此需要不同的 targetName
  // 才能在同一作用域中共存。
  extension (id: UserId)
    @targetName("userIdValue") def value: Long = id
  extension (id: OrderId)
    @targetName("orderIdValue") def value: Long = id

import ids.*
def lookupOrder(uid: UserId, oid: OrderId): String = ???

val u = UserId(1)
val o = OrderId(2)
lookupOrder(u, o)   // 编译通过
// lookupOrder(o, u) // 编译错误 —— OrderId ≠ UserId
```

### 4 — 用 GADT 在匹配分支中细化类型

编译器在每个分支内收窄类型参数，从而排除不可能的情况。

```scala
enum Expr[A]:
  case IntLit(value: Int) extends Expr[Int]
  case BoolLit(value: Boolean) extends Expr[Boolean]
  case Add(a: Expr[Int], b: Expr[Int]) extends Expr[Int]
  case IfThenElse[T](
      cond: Expr[Boolean], thenE: Expr[T], elseE: Expr[T]
  ) extends Expr[T]

def eval[A](e: Expr[A]): A = e match
  case Expr.IntLit(v)        => v                       // 此处 A =:= Int
  case Expr.BoolLit(v)       => v                       // 此处 A =:= Boolean
  case Expr.Add(a, b)        => eval(a) + eval(b)
  case Expr.IfThenElse(c, t, f) => if eval(c) then eval(t) else eval(f)
```

### 5 — 解析而非校验（Parse, don't validate）

不要检查条件后丢弃证据，而应返回携带保证的细化类型。解析器是一个从结构较弱的输入产出结构更强的输出的函数——不只是字符串解析。

```scala
// 校验：检查后丢弃证据
def validateNonEmpty[A](xs: List[A]): Unit =
  if xs.isEmpty then throw IllegalArgumentException("empty list")

// 解析：检查并把证据保留在返回类型里
import cats.data.NonEmptyList
def parseNonEmpty[A](xs: List[A]): Either[String, NonEmptyList[A]] =
  NonEmptyList.fromList(xs).toRight("list cannot be empty")

// 用不透明类型实现智能构造器（解析）
object domain:
  opaque type PortNumber = Int
  object PortNumber:
    def parse(n: Int): Either[String, PortNumber] =
      if n > 0 && n < 65536 then Right(n)
      else Left(s"invalid port: $n")
  extension (p: PortNumber) def value: Int = p

import domain.*
def connect(port: PortNumber): Unit =
  println(s"Connecting to port ${port.value}") // 永远合法，下游无需重新校验
```

**核心洞见：** 返回 `Unit` 或抛异常的检查属于校验——它们丢弃信息；返回细化类型（`Either[E, A]`、`Option[A]`、不透明类型）的属于解析——它们保留信息。优先选择解析。

参考：[Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 封闭层级 | `sealed trait` + `case class/object`——思路相同，样板更多 | `enum`——单一构造，派生 `ordinal`、`values` |
| 幻影类型 | 可行，但需要 `sealed trait` 树和哑 implicit 证据 | 编码相同，但 [erased 定义](../catalog/erased-phantom.md)可彻底消除运行时开销 |
| 防止值混用 | 值类（`extends AnyVal`）——受限、有装箱陷阱、不支持多字段 | 不透明类型——可组合、单态使用下无装箱；与任何类型一样，作为类型参数使用底层为基础类型时不透明类型会装箱（如 `List[UserId]`），开销不高于底层类型 |
| GADT | 支持但匹配常需强制转换；类型推断有限 | 匹配中的一等 GADT 支持；编译器无需转换即可细化类型 |
| 穷尽性 | `sealed` 可用，但非穷尽匹配默认只是告警 | 默认告警（`-Werror` 下为错误）；需用 `@nowarn` 显式静默 |

## 何时选择哪个特性

- **当状态集合小且固定时，首选 `enum` / ADT。** 这是默认工具——简单、穷尽、易于理解。
- **当需要跨方法调用强制一个协议或状态机（而不仅是单个值上的匹配）时，使用幻影类型。**
- **只要两个值共享底层类型却不可互换（ID、计量单位、领域原语），就用不透明类型。** 它们在运行时零成本。
- **当数据结构的不同分支携带不同的类型信息、并希望编译器把这些信息传播进匹配分支时，使用 GADT。**
- **当决策必须完全发生在编译期（例如按输入类型选择返回类型）时，才用匹配类型与 inline。**

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC01-invalid-states.md
