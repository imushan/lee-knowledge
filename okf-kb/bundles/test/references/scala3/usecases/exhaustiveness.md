---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC03-exhaustiveness.md
title: 穷尽匹配
description: 确保每个模式匹配都覆盖所有可能情况，编译器拒绝不完整匹配并定义“全部情况”的含义。
tags:
- UC03
- Scala 3
- vibe-types
- 穷尽匹配
- enum
- sealed
- Matchable
- GADT
timestamp: '2026-06-24T12:07:57Z'
---

# 穷尽匹配

## 约束目标

确保每个模式匹配都处理了所有可能的情况。编译器拒绝不完整的匹配，而 `sealed` / `enum` 层级精确定义了“全部情况”的含义。当某个 case 被有意忽略时，用 `@nowarn` 以可审计的注解方式静默告警。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| Enums / sealed traits | 封闭层级定义完整的 case 集合；编译器强制穷尽匹配 | [代数数据类型](../catalog/algebraic-data-types.md) |
| 匹配类型 | 类型层面的模式匹配，对类型 case 也有穷尽性 | [匹配类型](../catalog/match-types.md) |
| Matchable 约束 | 限制通用匹配只能作用于选择加入的类型；禁止对不透明或 erased 类型匹配 | [相等性安全](../catalog/equality-safety.md) |
| @nowarn 注解 | 当非穷尽匹配是有意为之时，静默特定告警 | [编译期运算](../catalog/compile-time-ops.md) |

## 模式

### 1 — 带 sealed trait 的穷尽匹配

`sealed` trait 将其子类型限制在定义文件内，编译器因此知道所有可能情况。

```scala
sealed trait Result
case class Success(value: String) extends Result
case class Failure(error: String) extends Result
case object Pending extends Result

def describe(r: Result): String = r match
  case Success(v) => s"ok: $v"
  case Failure(e) => s"error: $e"
  case Pending    => "waiting"
// 删除任一分支 → 编译告警："match may not be exhaustive"
```

### 2 — enum 的穷尽性

enum 天生是 sealed 的。新增 case 会在编译期破坏所有非穷尽的匹配。

```scala
enum Color:
  case Red, Green, Blue

def hex(c: Color): String = c match
  case Color.Red   => "#FF0000"
  case Color.Green => "#00FF00"
  case Color.Blue  => "#0000FF"
// 若有人新增 `case Yellow`，每个匹配点都必须更新
```

### 3 — 有意为之的部分匹配用 @nowarn

当匹配故意不完整时，`@nowarn` 记录意图并让编译器静默。

```scala
enum Event:
  case Click(x: Int, y: Int)
  case KeyPress(key: Char)
  case Scroll(delta: Int)
  case Resize(w: Int, h: Int)

// 本处理器只关心输入事件
@scala.annotation.nowarn("msg=match may not be exhaustive")
def handleInput(e: Event): String = e match
  case Event.Click(x, y) => s"clicked at ($x, $y)"
  case Event.KeyPress(k) => s"pressed $k"
  case Event.Scroll(d)   => s"scrolled $d"
// Resize 故意不处理 —— 由 @nowarn 记录
```

### 4 — Matchable 约束

`Matchable` trait 控制哪些类型可以被匹配。在严格设置下，对非 `Matchable` 类型匹配是错误，从而防止可能违反 parametricity 的匹配。

```scala
// Any 和 AnyRef 扩展自 Matchable，但自定义抽象可以选择不继承。
def process[A <: Matchable](a: A): String = a match
  case i: Int     => s"int: $i"
  case s: String  => s"str: $s"
  case other      => other.toString

// 用非 Matchable 约束时，匹配受限：
// def unsafe[A](a: A): String = a match // 在 -source:future 下告警
// case _: Int => "int"                  // A 不是 <: Matchable
```

### 5 — GADT 的穷尽性

GADT 模式匹配会细化类型参数。编译器追踪每个类型下哪些 case 可能出现，并拒绝真正不可能的分支。

```scala
enum Expr[A]:
  case IntLit(v: Int) extends Expr[Int]
  case BoolLit(v: Boolean) extends Expr[Boolean]
  case Not(e: Expr[Boolean]) extends Expr[Boolean]

def eval[A](e: Expr[A]): A = e match
  case Expr.IntLit(v)  => v            // A =:= Int
  case Expr.BoolLit(v) => v            // A =:= Boolean
  case Expr.Not(e)     => !eval(e)     // A =:= Boolean
// 穷尽：所有可能的 A 下所有 case 都被覆盖
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 封闭层级 | `sealed trait` + case class——思路相同，穷尽性默认是告警 | `enum`——语法简洁；非穷尽匹配默认告警（`-Werror` 下为错误） |
| 静默 | 在匹配 scrutinee 上加 `@unchecked`——粗粒度，隐藏所有告警 | 带消息过滤的 `@nowarn`——细粒度、可审计 |
| Matchable | 不可用；任何值都可被匹配 | `Matchable` 约束限制匹配；在 `-source:future` 下强制 |
| GADT 穷尽性 | 支持但脆弱；编译器常常无法证明覆盖 | 改进的 GADT 支持；编译器可靠地细化类型并检查穷尽性 |

## 何时选择哪个特性

- **用 `enum`** 处理任何封闭的备选集合。它是默认工具——简洁、穷尽、工具与派生支持良好。
- **用 `sealed trait`** 当你需要 `enum` 不支持的基于类的特性（例如每个 case 混入 trait、复杂继承）。
- **谨慎使用 `@nowarn`**，且仅当部分匹配是有意为之。务必加注释说明省略了哪些 case 以及原因。
- **用 `Matchable`** 在库 API 中阻止客户端对抽象类型做模式匹配，从而保持 parametricity 与未来的灵活性。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC03-exhaustiveness.md
