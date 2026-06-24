---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC02-domain-modeling.md
title: 领域建模
description: 用精确的领域类型在编译期拒绝非法值，让类型系统携带证明而非靠运行时断言。
tags:
- UC02
- Scala 3
- vibe-types
- 领域建模
- 不透明类型
- 智能构造器
- 交集类型
timestamp: '2026-06-24T12:07:39Z'
---

# 领域建模

## 约束目标

表达精确的领域类型，在编译期拒绝非法值。一个 `NonEmptyString` 永远不会为空；一个 `Email` 永远包含 `@`。证明由类型系统携带，而不是运行时断言。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 不透明类型 | 领域原语的零成本包装 | [不透明类型](../catalog/newtypes-opaque.md) |
| Enums / ADTs | 封闭的领域状态与事件集合 | [代数数据类型](../catalog/algebraic-data-types.md) |
| 联合 / 交集类型 | 无需层级样板即可表达“多选一”或“兼具” | [联合与交集类型](../catalog/union-intersection.md) |
| 细化类型（via inline） | 对字面量值做编译期校验 | [结构化类型](../catalog/structural-typing.md) |
| inline 校验 | `inline` + `compiletime.error` 在编译期拒绝错误字面量 | [编译期运算](../catalog/compile-time-ops.md) |

## 模式

### 1 — 领域原语用不透明类型

包装原始类型以防误用。校验只在边界处发生一次。

```scala
import scala.annotation.targetName

object domain:
  opaque type Email = String
  object Email:
    def parse(raw: String): Either[String, Email] =
      if raw.contains("@") then Right(raw)
      else Left(s"Invalid email: $raw")

  opaque type NonEmptyString = String
  object NonEmptyString:
    def from(s: String): Option[NonEmptyString] =
      Option.when(s.nonEmpty)(s)

  extension (e: Email) def value: String = e
  // 两者擦除后都是 (String): String，用 @targetName 在字节码层消歧。
  extension (s: NonEmptyString) @targetName("nesValue") def value: String = s

import domain.*

case class User(name: NonEmptyString, contact: Email)

// 构造必须经过智能构造器：
val user: Either[String, User] =
  for
    name  <- NonEmptyString.from("Alice").toRight("empty name")
    email <- Email.parse("alice@example.com")
  yield User(name, email)
```

### 2 — 带 inline 校验的智能构造器

当值在编译期已知（字面量）时，在程序运行之前就拒绝非法值。

```scala
object port:
  opaque type Port = Int
  object Port:
    inline def apply(inline p: Int): Port =
      inline if p < 1 || p > 65535 then
        compiletime.error("Port must be between 1 and 65535")
      else p
    def fromInt(p: Int): Option[Port] =
      Option.when(p >= 1 && p <= 65535)(p)
  extension (p: Port) def value: Int = p

import port.*

val http  = Port(80)   // 编译通过
val https = Port(443)  // 编译通过
// val bad = Port(99999) // 编译错误："Port must be between 1 and 65535"
```

### 3 — 用 enum 层级表达领域状态

把领域实体的生命周期建模为封闭层级，每个状态只携带它需要的数据。

```scala
enum OrderStatus:
  case Draft(items: List[String])
  case Submitted(items: List[String], submittedAt: java.time.Instant)
  case Shipped(trackingId: String)
  case Delivered(signature: String)
  case Cancelled(reason: String)

def ship(status: OrderStatus): OrderStatus = status match
  case OrderStatus.Submitted(_, _) =>
    OrderStatus.Shipped(trackingId = "TRK-001")
  case other =>
    throw IllegalStateException(s"Cannot ship from $other")
// 更佳做法：用幻影类型（见 invalid-states）把这种情况变成编译错误
```

### 4 — 用交集类型组合能力

组合细粒度的 trait 能力，而无需绑定到固定的类层级。

```scala
trait HasName:
  def name: String
trait HasEmail:
  def email: String
trait HasRole:
  def role: String

// 需要 name 和 email，但不需要 role 的函数：
def sendWelcome(user: HasName & HasEmail): String =
  s"Welcome ${user.name}, confirmation sent to ${user.email}"

// 需要三者皆备的函数：
def auditLog(user: HasName & HasEmail & HasRole): String =
  s"[${user.role}] ${user.name} <${user.email}>"

case class FullUser(name: String, email: String, role: String)
  extends HasName, HasEmail, HasRole

val u = FullUser("Alice", "alice@example.com", "admin")
sendWelcome(u) // 编译通过 —— FullUser <: HasName & HasEmail
auditLog(u)    // 编译通过 —— FullUser <: HasName & HasEmail & HasRole
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 领域原语 | 值类（`extends AnyVal`）——仅单字段，擦除下有装箱问题 | 不透明类型——可挂多个 extension，单态使用下无装箱；与任何类型一样，作为类型参数使用底层为基础类型时不透明类型会装箱（如 `List[UserId]`），开销不高于底层类型 |
| 智能构造器 | 同样的 `apply`/`from` 模式，但没有 `inline` 校验；检查总在运行期 | `inline` + `compiletime.error` 在编译期拒绝错误字面量 |
| 封闭层级 | `sealed trait` + `case class`——冗长，无内建 `values`/`ordinal` | `enum`——简洁，自动派生实用成员 |
| 能力组合 | 复合类型（`A with B`）——顺序敏感，非真正交集 | 交集类型（`A & B`）——可交换、一等公民 |
| 字面量校验 | 需 Shapeless `Witness` 或 refined 库 | 内建 `inline if` + `compiletime.error`；简单场景无需第三方库 |

## 何时选择哪个特性

- **不透明类型**是任何领域原语的默认选择——ID、数量、校验过的字符串。当你需要零开销且类型只有一个底层表示时，优先于 case class 包装器。
- **inline 校验**适用于代码库中常见字面量的场景（端口、HTTP 状态码、配置常量）。对运行期计算出的值，回退到返回 `Option` 或 `Either` 的智能构造器。
- **enum** 用于建模领域状态。当每个状态携带不同数据时使用带参 case。需要编译器强制合法转换时，考虑基于幻影类型的状态机（见 [屏蔽非法状态](invalid-states.md)）。
- **交集类型**在能力细粒度且临时组合时大放异彩。如果你发现自己在创建深层 trait 层级只为组合行为，交集类型让调用方精确指定所需，而无需固定继承树。
- **联合类型**（`A | B`）适用于不想要共同父类型的“多选一”场景——例如 `String | Int` 作为 JSON 值。当备选项有领域含义且需要穷尽匹配时，优先用封闭 enum。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC02-domain-modeling.md
