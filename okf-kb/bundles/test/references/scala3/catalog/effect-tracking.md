---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T12-effect-tracking.md
title: 捕获检查、CanThrow 与纯函数
description: 通过捕获检查为每个值类型附带一个捕获集，静态追踪它可能引用的副作用能力（IO、可变状态、异常），禁止能力逃逸出所属作用域。
tags:
- T12
- Scala 3
- vibe-types
- 捕获检查
- CanThrow
- 纯函数
- 能力追踪
- 实验性
- Capture Checking
timestamp: '2026-06-25T12:57:48Z'
---

# 捕获检查、CanThrow 与纯函数

## 简介

捕获检查（capture checking）是 Scala 3 类型系统的实验性扩展（`import language.experimental.captureChecking`），用于追踪值所持有的**能力**——即对执行副作用（如 I/O、可变状态、抛异常）的对象的引用。每个值的类型都可携带一个**捕获集**，列出它闭合的能力，编译器据此强制能力不得逃逸出预期作用域。在此之上，`CanThrow[E]` 将受检异常建模为能力，而纯函数类型（`A -> B`）表示完全不捕获任何能力的函数。

## 可表达的约束

**函数的类型显式声明它可使用或持有哪些能力（IO 句柄、日志器、异常令牌），编译器静态阻止能力逃逸其所属作用域。** 这使效果追踪、资源安全与纯度可在类型层而非约定上被强制。

## 捕获类型

捕获检查引入了**捕获类型**来在类型层面追踪变量捕获：

```
T^{x_1, ..., x_n}
```

- `T`：**形状类型**（shape type）——该类型的值捕获以下捕获集中的值
- `{x_1, ... x_n}`：**捕获集**（capture set）——该值允许捕获的值的集合

例如，闭包 `increment` 引用了外部定义的 `c`，其类型为 `(() => Unit)^{c}`，表示它捕获了能力 `c`。

### 函数类型语法

捕获检查引入了新的函数类型表示法：

- `A => B`：传统函数类型，表示可能捕获**任意**值的函数（即 `A ->{any} B` 的语法糖）
- `A -> B`：纯函数类型，表示**不捕获任何东西**的函数
- `A ->{c, d} B`：`(A -> B)^{c, d}` 的简写，表示捕获 `c` 和 `d` 的函数

上下文函数同理：`?=>`（非纯）vs `?->`（纯）。

`T^` 是 `T^{any}` 的简写，其中 `any` 是代表所有能力的顶层能力。值必须有非空捕获集才能被追踪。

## 最小示例

```scala
import language.experimental.captureChecking

// 资源安全：阻止文件句柄逃逸
def usingLogFile[T](op: FileOutputStream^ => T): T =
  val logFile = FileOutputStream("log")
  val result = op(logFile)
  logFile.close()
  result

// 安全：能力被即时使用
val xs = usingLogFile { f =>
  List(1, 2, 3).map { x => f.write(x); x * x }
}

// 不安全：能力会在闭包中逃逸——编译错误
// val later = usingLogFile { f => () => f.write(0) }
// error: capability f cannot be included in outer capture set

// 通过 CanThrow 实现受检异常
import language.experimental.saferExceptions
class LimitExceeded extends Exception
def f(x: Double): Double throws LimitExceeded =
  if x < 1e9 then x * x else throw LimitExceeded()

@main def test(xs: Double*) =
  try println(xs.map(f).sum)
  catch case _: LimitExceeded => println("too large")
```

### 引用透明的 map

捕获检查的一个简单用例是实现保证引用透明性的 `map`——确保传入的函数不会执行破坏性修改：

```scala
def map[A, B](xs: List[A])(f: A -> B): List[B] =
  xs.map(f)
```

由于 `f` 的类型是 `A -> B`（纯函数），它不能访问外部可变状态，从而保证了引用透明性。

### 别名追踪

别名不会混淆捕获检查——编译器会追踪它们：

```scala
val c: Counter^ = new Counter
val d: Counter^ = c  // d 和 c 指向同一个对象
// d 的捕获集包含 c，编译器知道它们是别名
```

## 与其他特性的交互

- **捕获类型与捕获集。** 类型 `T^{c1, c2}` 表示"一个可能持有能力 `c1` 和 `c2` 的 `T`"。通用能力 `cap` 覆盖所有其他能力，因此 `T^`（`T^{cap}` 的简写）表示"可捕获任何东西"。纯类型（无捕获集）是所有同底类型捕获类型的子类型。
- **纯函数 vs 非纯函数类型。** `A => B` 是 `A ->{cap} B` 的语法糖（非纯，可捕获任何东西）。`A -> B` 表示不捕获任何东西的纯函数。中间形式如 `A ->{c} B` 只捕获 `c`。上下文函数同理（`?=>` vs `?->`）。
- **CanThrow 与 `throws` 子句。** `CanThrow[E]` 是一个 erased 能力类。`throw Exc()` 要求作用域内存在 `CanThrow[Exc]`。`try` 块为其 catch 子句合成该能力。`throws` 关键字是语法糖：`def m(x: T): U throws E` 脱糖为 `def m(x: T)(using CanThrow[E]): U`。这实现了效果多态的受检异常，而无需修改 `map` 等高阶函数签名。参见 [错误处理](../usecases/error-handling.md)。
- **能力类。** 继承 `caps.SharedCapability` 的类型自动携带捕获集；写 `FileSystem`（其中 `class FileSystem extends SharedCapability`）隐式表示 `FileSystem^`。
- **子类型与子捕获。** 更小的捕获集产生子类型：`T^{c} <: T^{c, d} <: T^{cap}`。纯类型是任何捕获变体的子类型。子捕获关系是传递的，并考虑嵌套能力。
- **逃逸检查与规避。** 能力遵循词法作用域：捕获集不能提及在定义处不可见的能力。当局部能力会出现在结果类型中时，编译器会将其**拓宽**（规避）到最小可见超集。
- **erased 定义。** `CanThrow` 继承 `compiletime.Erased`，因此异常能力零运行时开销。参见 [效果追踪](../usecases/effect-tracking.md)。
- **分离检查。** 捕获检查是分离检查的基础。分离检查在此之上引入 `SharedCapability`（只读）和 `ExclusiveCapability`（可写）来追踪修改权限。参见 [分离检查](./separation-checking.md)。

## 注意事项与局限

1. **高度实验性。** 捕获检查演进迅速；API 与语义可能随 Scala 版本变化。始终使用最新 nightly。
2. **`try` 中的能力逃逸。** 当前 `CanThrow` 模型不阻止能力在返回的闭包中逃逸 `try` 作用域。从 `try` 体返回的闭包可能携带合成的 `CanThrow` 能力，导致后续调用点出现未捕获异常。完全强制有待瞬时能力追踪。
3. **`->` 与 `?->` 是软关键字。** 在类型位置 `->` 表示纯函数类型，但在项位置仍是普通标识符（如 `Map("x" -> 1)` 仍可用）。
4. **方法不直接捕获。** 方法不是值，本身不携带捕获集。它们引用的能力在其所属对象的捕获集中追踪。
5. **lazy val 初始化。** 对捕获检查而言，lazy val 行为类似无参方法：访问 lazy val 会将其所属对象的能力计入当前捕获集。
6. **`unsafeExceptions.canThrowAny`。** 导入该 given 会全局提供 `CanThrow[Exception]`，禁用异常检查。便于迁移但违背 safer exceptions 的初衷。
7. **仅简单 catch 模式。** 编译器只为 `case ex: Ex =>` 形式的 catch 子句生成 `CanThrow` 能力；构造器模式与带守卫的模式在 `saferExceptions` 下不受支持。

## 推荐库

| 库 | 角色 | 链接 |
|----|------|------|
| **cats-effect** | 带基于 fiber 并发、资源安全与取消的 IO monad | [typelevel.org/cats-effect](https://typelevel.org/cats-effect/) |
| **zio** | 内建依赖注入、类型化错误与结构化并发的 ZIO 效果类型 | [zio.dev](https://zio.dev/) |
| **ox** | 直接风格 Scala 3 的结构化并发；基于虚拟线程，无 monad 包装 | [github.com/softwaremill/ox](https://github.com/softwaremill/ox) |

## 用例交叉引用

- 联合类型：`throws E1 | E2` 用联合类型表达多异常能力，参见 [非法状态不可表示](../usecases/invalid-states.md)。
- erased 定义：`CanThrow` 是 erased 能力类的主要消费者，参见 [效果追踪](../usecases/effect-tracking.md)。
- explicit nulls：捕获检查与 null 检查是互补的静态安全层，参见 [可空性](../usecases/nullability.md)。
- 效果系统：捕获检查将效果追踪推广到 I/O、可变状态与代数效果，参见 [效果追踪](../usecases/effect-tracking.md)。
- 纯度强制：`A -> B` 函数类型与捕获检查组合以保证无副作用，参见 [效果追踪](../usecases/effect-tracking.md)。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T12-effect-tracking.md
- https://virtuslab.com/blog/scala/introduction-to-scala-3-checking
- https://docs.scala-lang.org/scala3/reference/experimental/cc.html
- https://capless.cc/
