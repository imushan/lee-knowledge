---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T26-refinement-types.md
title: 细化类型（Refinement Types）
description: 用谓词收窄基础类型，使带谓词的值只能在通过编译期或运行期检查后才能构造，把校验编入类型本身。
tags:
- T26
- Scala 3
- vibe-types
- 细化类型
- Iron
- refined
- 谓词
- 编译期校验
timestamp: '2026-06-24T12:05:38Z'
---

# 细化类型（Refinement Types）

**起始版本：** 库级实现（refined、Iron），支持 Scala 2/3 | **语言基础：** opaque types + inline 提供底层支撑

## 简介

细化类型是用一个谓词收窄后的基础类型——例如 `Refined[Int, Positive]` 类型的值是一个已被证明为正的 `Int`。Scala 3 本身没有内建细化类型，但有两个库提供带编译期检查的实现：

- **[refined](https://github.com/fthomas/refined)** —— 原始的细化类型库。定义 `Refined[T, P]`，其中 `P` 是谓词类型。生态成熟，与 Circe、Doobie、PureConfig 等集成。
- **[Iron](https://github.com/Iltotore/iron)** —— Scala 3 原生库，使用 opaque types 与 inline 实现零开销细化，直接利用 Scala 3 的编译期能力。

两者都把谓词编码进类型，使细化值携带"谓词成立"的编译期保证。

## 可表达的约束

**细化值只能通过检查才能构造（字面量在编译期、动态值在运行期）。谓词是类型的一部分，因此接受 `PosInt` 的函数无法接收未检查的 `Int`。**

## 最小示例

### 使用 Iron（Scala 3 原生）

```scala
import io.github.iltotore.iron.*
import io.github.iltotore.iron.constraint.numeric.*

type PosInt = Int :| Positive

val x: PosInt = 42 // OK — literal checked at compile time
// val y: PosInt = -1 // compile error: -1 does not satisfy Positive

def safeDivide(a: Int, b: Int :| Positive): Int = a / b
// safeDivide(10, 0) // compile error: 0 does not satisfy Positive (Iron's Positive is strictly > 0)
```

### 使用 refined

```scala ignore
import eu.timepit.refined.api.Refined
import eu.timepit.refined.numeric.Positive
import eu.timepit.refined.auto.*

type PosInt = Int Refined Positive

val x: PosInt = 42 // OK — macro checks literal at compile time
// val y: PosInt = -1 // compile error

// Runtime refinement for dynamic values
import eu.timepit.refined.refineV
val input: Int = getUserInput()
val result: Either[String, PosInt] = refineV[Positive](input)
```

## 与其他特性的交互

| 特性 | 如何组合 |
|---|---|
| **不透明类型**（[newtypes-opaque](newtypes-opaque.md)） | Iron 内部使用 opaque types——细化值零运行时开销。 |
| **Inline**（[compile-time-ops](compile-time-ops.md)） | Iron 使用 `inline` 对字面量做编译期谓词检查。 |
| **ADT**（[algebraic-data-types](algebraic-data-types.md)） | 细化类型与 ADT 互补：ADT 建模存在哪些状态，细化约束每个状态内取值的范围。 |
| **类型类派生**（[derivation](derivation.md)） | 两个库都提供 Codec/Encoder/Decoder 实例，使细化类型能与 JSON、数据库库集成。 |

## 注意事项与局限

1. **编译期检查仅对字面量有效。** `val x: PosInt = 42` 在编译期检查，但 `val x: PosInt = someVar` 需要通过 `refineV`（refined）或 `.refine`（Iron）做运行期校验，返回 `Either`。
2. **两套生态。** `refined` 集成更广（Circe、Doobie、PureConfig、http4s）。Iron 较新且 Scala 3 原生，但其集成生态仍在成长。每个项目择一即可。
3. **谓词组合。** 两个库都支持组合谓词（refined 中 `Positive And LessEqual[100]`，Iron 中 `StrictlyPositive & Less[100]`），但语法不同。
4. **非结构化细化。** 这些是 _值_ 细化（对值的谓词），而非 Scala 的结构类型（`T { def name: String }`）。结构类型请见 [structural-typing](structural-typing.md)。

## 初学者心智模型

把细化类型看作 **自带编译期校验器的 newtype**。你不必自己写智能构造器，库提供了通用机制：你声明谓词（`Positive`、`NonEmpty`、`MatchesRegex["^[a-z]+$"]`），库来强制——字面量在编译期，动态值在运行期（返回 `Either`）。

## 示例 A —— 带细化字段的领域模型

```scala
import io.github.iltotore.iron.*
import io.github.iltotore.iron.constraint.all.*

type Username = String :| (MinLength[1] & MaxLength[32])
type Port = Int :| Interval.OpenClosed[0, 65535]
type Email = String :| Match["^[\w.+-]+@[\w-]+\.[\w.]+$"]

case class ServerConfig(
  host: String,
  port: Port,
  adminEmail: Email
)

val cfg = ServerConfig("localhost", 8080, "admin@example.com")
// ServerConfig("localhost", 0, "admin@example.com") // compile error: 0 not in (0, 65535]
```

## 示例 B —— 用细化类型"解析而非校验"

```scala
import io.github.iltotore.iron.*
import io.github.iltotore.iron.constraint.numeric.*

// Runtime parsing returns Either — the "parse, don't validate" pattern
def parsePort(s: String): Either[String, Int :| Interval.OpenClosed[0, 65535]] =
  s.toIntOption match
    case Some(n) => n.refineEither[Interval.OpenClosed[0, 65535]]
    case None    => Left(s"not an integer: $s")

// Once parsed, the refined type flows through the system
def connect(port: Int :| Interval.OpenClosed[0, 65535]): Unit =
  println(s"Connecting to port $port") // always valid, no re-check needed
```

## 推荐库

| 库 | Scala 版本 | 风格 | 关键优势 |
|---|---|---|---|
| [Iron](https://github.com/Iltotore/iron) | Scala 3 | opaque types + inline | 零开销，Scala 3 原生 |
| [refined](https://github.com/fthomas/refined) | Scala 2 & 3 | `Refined[T, P]` 包装 | 生态成熟，集成广泛 |

## 用例交叉引用

- 细化类型让非法值无法构造，见 [非法状态构造](../usecases/invalid-states.md)。
- 带内建约束的领域原语（端口、邮箱、用户名），见 [领域建模](../usecases/domain-modeling.md)。

# 引用

- 原始资料：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T26-refinement-types.md
- Iron 文档：https://iltotore.github.io/iron/docs/
- refined GitHub：https://github.com/fthomas/refined
- Iron GitHub：https://github.com/Iltotore/iron
