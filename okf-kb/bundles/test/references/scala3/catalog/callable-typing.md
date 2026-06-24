---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T22-callable-typing.md
title: 可调用类型与重载（Callable Types & Overloading）
description: 以函数类型、SAM 转换、eta 展开、重载、传名参数与上下文函数类型精确表达一次计算所需的输入、上下文与求值策略，并由编译器在调用处强制匹配。
tags:
- T22
- Scala 3
- vibe-types
- 函数类型
- SAM
- eta 展开
- 重载
- 传名参数
- 上下文函数
timestamp: '2026-06-24T12:04:27Z'
---

# 可调用类型与重载（Callable Types & Overloading）

**起始版本：** Scala 3.0

## 简介

Scala 3 拥有一套远超简单函数字面量的丰富可调用类型体系。**函数类型**（`A => B`）是 `scala.FunctionN` trait 实例的语法糖。**SAM（Single Abstract Method）类型** 允许任何恰有一个抽象方法的 trait 或抽象类用 lambda 实例化。**Eta 展开** 自动把方法引用转换为函数值。**方法重载** 允许多个同名但参数类型不同的方法共存。**传名参数**（`=> T`）延迟参数求值直至被使用。**上下文函数类型**（`A ?=> B`）通过 lambda 体传播 given 实例。这些特性共同构成了一套灵活且类型安全的可调用抽象层。

## 可表达的约束

**可调用类型让你精确表达一次计算需要什么（输入类型、隐式上下文、求值策略）以及产出什么（输出类型），编译器在每个调用处强制签名匹配。** 函数类型编码了元数与参数/返回类型。SAM 类型允许在接受 lambda 语法的同时要求一个具体接口。传名参数在类型层面强制惰性求值。上下文函数在无需显式传递的情况下线程化能力（capabilities）。

## 最小示例

**函数类型：**

```scala
val add: (Int, Int) => Int = (a, b) => a + b
val transform: String => Int = _.length
// Function types are traits: Function2[Int, Int, Int]
// with variance: Function2[-A, -B, +R]
```

**SAM（Single Abstract Method）转换：**

```scala
trait Comparator[A]:
  def compare(x: A, y: A): Int

// Lambda auto-converts to SAM type:
val byLength: Comparator[String] = (x, y) => x.length - y.length
```

**Eta 展开（方法到函数的自动转换）：**

```scala
def double(x: Int): Int = x * 2
val f: Int => Int = double        // eta-expanded automatically
List(1, 2, 3).map(double)         // also eta-expanded
```

**方法重载：**

```scala
object Show:
  def show(x: Int): String              = x.toString
  def show(x: String): String           = s"'$x'"
  def show(x: Double, precision: Int): String = s"%.${precision}f".format(x)

import Show.show
show(42)        // "42"
show("hello")   // "'hello'"
show(3.14, 2)   // "3.14"
```

**传名参数：**

```scala
def logging[A](msg: => String)(body: => A): A =
  println(s"START: $msg")
  val result = body   // evaluated here, not at call site
  println(s"END: $msg")
  result

logging("heavy computation") {
  Thread.sleep(1000)
  42
}
```

**上下文函数类型：**

```scala
import scala.concurrent.ExecutionContext
type Executable[A] = ExecutionContext ?=> A

val task: Executable[Int] =
  summon[ExecutionContext]   // available via ?=>
  42

given ExecutionContext = ExecutionContext.global
val result: Int = task       // context supplied automatically
```

## 与其他特性的交互

| 特性 | 如何组合 |
|---|---|
| **泛型与边界**（[generics-bounds](generics-bounds.md)） | 函数类型与泛型组合：`def map[A, B](f: A => B): List[B]`。多态函数类型 `[A] => A => A` 允许全称量化的函数值。 |
| **上下文函数**（[context-functions](context-functions.md)） | 上下文函数类型 `A ?=> B` 是一种独特的函数种类：编译器从 given 实例提供参数，支持能力传递模式。 |
| **方差**（[variance-subtyping](variance-subtyping.md)） | `FunctionN` 对参数类型逆变、对返回类型协变：`Function1[-A, +B]`。因此 `Animal => Cat` 是 `Cat => Animal` 的子类型。 |
| **依赖函数类型**（[path-dependent-types](path-dependent-types.md)） | `(x: A) => x.T` 允许返回类型依赖参数值，把类型安全的提取器/解释器做成一等值。 |
| **Given 实例**（[type-classes](type-classes.md)） | SAM 转换与 given 交互：若为某 SAM 类型定义了 given 实例，lambda 字面量即可满足该 given 要求。 |
| **扩展方法**（[extension-methods](extension-methods.md)） | 对函数类型的扩展方法可添加组合子：`extension [A, B](f: A => B) def andThen[C](g: B => C): A => C`。 |

## 注意事项与局限

1. **SAM 转换要求恰有一个抽象方法。** 若 trait 有两个抽象方法，lambda 语法不适用。默认方法和具体方法不计入该限额。
2. **eta 展开与重载。** 当方法被重载时，eta 展开需要期望类型来消歧：若 `show` 被重载，`val f: Int => Int = show` 会失败。请用类型标注或 `show(_: Int)`。
3. **传名参数不是函数值。** `=> T` 与 `() => T` 不同。不能把传名参数存入 `val`（它会立即求值）。如需延迟，显式包装：`val thunk: () => T = () => param`。
4. **重载解析优先级。** Scala 的重载解析使用特异性规则，可能有出人意料之处。接收 `String` 的方法比接收 `Any` 的更具体，但涉及泛型时可能出现歧义。编译器会报告 "ambiguous overloaded method" 错误。
5. **函数元数上限。** 标准库中 `FunctionN` 定义到 `N = 22`。Scala 3 可通过元组表示自动生成超过 22 的函数，但部分库可能无法处理高元数函数。
6. **SAM 类型与序列化。** 由 lambda 创建的 SAM 实例可能不可序列化。若 SAM trait 继承 `Serializable`，lambda 必须只捕获可序列化的值。
7. **不能仅凭返回类型重载。** Scala 不支持仅在返回类型上不同的重载方法。参数列表必须不同。

## 初学者心智模型

可以把 Scala 的可调用类型视为一个 **精确度** 的谱系：

- `A => B` 最简单："给我一个 A，得到一个 B。"
- `=> T`（传名）表示："我会在需要时才求值这个表达式。"
- `A ?=> B`（上下文函数）表示："通过 given 系统隐式给我一个 A。"
- SAM 类型表示："我接受 lambda，但我是一个有名字、可能还有其它具体成员的完整接口。"

编译器在安全处自动在这些形式之间转换（eta 展开、SAM 转换），并在类型不匹配时拒绝转换。

## 常见类型检查器报错

```
-- [E134] Type Error ---
val f: Int => String = show
^^^^
Ambiguous overload. Both method show(x: Int): String
and method show(x: String): String match expected type Int => String
Fix: disambiguate with a lambda: val f: Int => String = show(_: Int)
```

```
-- [E007] Type Mismatch Error ---
def twice(f: => Int): Int = f + f
twice { () => 42 }
^^^^^^^^^
Found: () => Int
Required: Int
Fix: by-name parameters are not Function0. Remove the () =>:
twice { 42 }
```

```
-- Error ---
trait Handler[A]:
  def handle(a: A): Unit
  def reset(): Unit
val h: Handler[String] = s => println(s)
^^^^^^^^^^^^^^^^
Handler is not a single abstract method type (has 2 abstract methods)
Fix: provide a full implementation with `new Handler[String] { ... }`
or add a default implementation for reset().
```

```
-- [E081] Type Error ---
def process(f: String => Int) = f("hello")
process(_.length + _.toInt)
^
Missing parameter type for expanded function.
Wrong number of parameters: expected 1, found 2.
Fix: the underscore syntax creates one parameter per _. Use an
explicit lambda: process(s => s.length + s.toInt)
```

## 用例交叉引用

- SAM 类型用于领域专用回调与事件处理器，见 [领域建模](../usecases/domain-modeling.md)。
- 上下文函数把能力线程化穿过状态机转换，见 [状态机](../usecases/state-machines.md)。
- 传名参数用于惰性配置与构建器模式，见 [构建器配置](../usecases/builder-config.md)。
- 线程化能力的效应追踪系统中的函数类型，见 [效应追踪](../usecases/effect-tracking.md)。

# 引用

- 原始资料：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T22-callable-typing.md
- Scala 3 Reference: Function Types — https://docs.scala-lang.org/scala3/reference/new-types/type-lambdas-spec.html
- Scala 3 Reference: Context Functions — https://docs.scala-lang.org/scala3/reference/contextual/context-functions.html
- Scala 3 Reference: SAM Conversions — https://docs.scala-lang.org/scala3/reference/changed-features/eta-expansion-spec.html
- Scala 3 Reference: Automatic Eta Expansion — https://docs.scala-lang.org/scala3/reference/changed-features/eta-expansion.html
