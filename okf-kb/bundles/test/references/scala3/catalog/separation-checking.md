---
type: Reference
resource: https://docs.scala-lang.org/scala3/reference/experimental/capture-checking/separation-checking.html
title: 分离检查（Separation Checking）
description: 基于捕获检查的实验性扩展，通过 SharedCapability 和 ExclusiveCapability 追踪程序中哪些部分可以修改数据，防止并发数据竞争并区分只读与可写效果。
tags:
- Scala 3
- 分离检查
- 并发安全
- 能力追踪
- 实验性
- SharedCapability
- ExclusiveCapability
- Capture Checking
timestamp: '2026-06-25T12:58:17Z'
---

# 分离检查（Separation Checking）

## 简介

分离检查是 Scala 3 的实验性特性，基于捕获检查（Capture Checking）构建。它引入了 `SharedCapability`（只读）和 `ExclusiveCapability`（可写）来追踪程序中哪些部分可以修改数据。这有助于防止并发程序中的数据竞争，并实现只读与可写效果的分离追踪。

## 核心概念

### Mutable 与 ExclusiveCapability

分离检查提供了 `caps.Mutable`。扩展它的类可以定义带有 `update` 修饰符的方法。`update def` 表示该方法会修改类的状态（或外部资源），这些方法不能在只读上下文中调用。

```scala
import language.experimental.captureChecking
import caps.*

class Ref(init: Int) extends Mutable:
  private var x = init
  def read(using SharedCapability[this.type]): Int = x
  update def set(newValue: Int)(using ExclusiveCapability[this.type]): Unit =
    x = newValue
```

这里，`any`（`caps.any`）是一个**顶层能力**，本质上与捕获检查中的通用能力（`cap`）相同，但在分离检查中，每次出现的 `any` 都被视为不同且排他的。（`any.rd` 是 `any` 的只读版本：它授予读取权限但禁止修改（即调用 `update` 方法）。）

每次出现的 `any` 都被视为一个独立的排他能力。例如，在 `def swap(a: Ref^, b: Ref^)` 中，`a` 获得 `Ref^{any₁}`，`b` 获得 `Ref^{any₂}`——两个不同的能力，因此编译器知道它们不会相互别名。

编写参数类型时，`Ref` 扩展为 `Ref^{any.rd}`（只读访问）。`Ref^` 扩展为 `Ref^{any}`（包括修改在内的完全访问）。

```scala
def readRef(r: Ref): Int = r.read  // 只读访问
def writeRef(r: Ref^): Unit = r.set(42)  // 需要完全访问
```

在 `read` 中调用 update 方法是不允许的：

```scala
def readOnly(r: Ref): Unit =
  r.set(42)  // 错误：无法在只读上下文中调用 update 方法
```

### 分离检查

考虑一个 `par` 函数，它并行执行两个函数。如果一个参数对资源调用了 update 方法，另一个参数就不能访问该资源：

```scala
def par[A, B](f: () => A, g: () => B): (A, B) = ???

// 错误：两个参数都试图修改同一个资源
val r = Ref(0)
par(() => r.set(1), () => r.set(2))
```

这个约束可能看起来过于严格。对于顺序执行的 `seq` 函数，这样的限制不应该是必需的。这是通过一个称为 *Hide* 的机制处理的。

```scala
def seq[A, B](f: () => A, g: () => B): (A, B) =
  val a = f()
  val b = g()
  (a, b)
```

### 移动语义

在分离检查中，`T^`（`T^{any}`）代表一种特殊类型：一个不与任何人共享的独立能力。

将变量 `y` 赋值给 `T^` 意味着 *y* 被排他能力 *x* 隐藏了。只要 *x* 还存活，原始的 *y* 就不能被访问（否则 *x* 和 *y* 就会共享同一个能力）。

这防止了通过别名引用进行意外修改：

```scala
val r = Ref(0)
val f: () => Unit = () => r.set(1)
val g: () => Unit = () => r.set(2)

// 当调用 par(() => r.set(1), () => r.set(2)) 时：
// - () => r.set(1) 被 f 隐藏（传递地，这个闭包捕获的 r 也被 f 隐藏）
// - () => r.set(2) 试图访问 r，但它被 f 隐藏了——因此失败
```

可以通过显式授予 *g* 访问被 *f* 隐藏的能力来解决：

```scala
def grantAccess[A](f: () => A)(g: () => A): A =
  val a = f()
  g()
```

### 消费参数

你可能认为可以通过从函数返回 `Ref^` 来绕过隐藏。考虑一个就地更新函数：

```scala
def incr(r: Ref^): Ref^ =
  r.set(r.read + 1)
  r
```

从函数返回具有顶层能力的值只有在参数不再使用时才是安全的（因为函数可能创建并返回一个别名）。所以上面的 `incr` 定义实际上会产生错误：

```scala
// 错误：参数 r 在返回后可能仍被使用
val r = Ref(0)
val r2 = incr(r)
r.read  // 这应该被允许吗？
```

要编译这个，参数必须标记为 `consume`，明确表示参数将被隐藏（移动语义！）：

```scala
def incr(r: Ref^ { consume }): Ref^ =
  r.set(r.read + 1)
  r
```

## 与其他特性的交互

- **捕获检查**：分离检查建立在捕获检查之上，使用相同的捕获集语法（`T^{c1, c2}`）来追踪能力。参见 [捕获检查](./effect-tracking.md)。
- **纯函数类型**：`A -> B` 表示不捕获任何能力的纯函数，与分离检查结合可以保证函数不会修改外部状态。
- **能力类**：继承 `caps.SharedCapability` 的类型自动获得只读语义，继承 `caps.Mutable` 的类型支持修改操作。
- **子类型关系**：更小的捕获集产生子类型，只读能力是排他能力的子类型。

## 设计动机

编写大规模软件时，处理可变数据是最棘手的部分之一。数据可能在意外的地方被修改，资源可能在错误的时机被使用。Rust 通过所有权和生命周期来缓解这些问题，但 Scala 作为 GC 语言需要不同的方案。分离检查的目标是：在保留 GC 内存管理的同时，选择性地引入类似 Rust 的约束——追踪对资源的访问权限（能力），而非管理内存。

## 注意事项与局限

1. **高度实验性**：分离检查仍在积极开发中，API 和语义可能随 Scala 版本变化。
2. **性能影响**：分离检查可能增加编译时间，因为需要额外的类型检查。
3. **迁移成本**：现有代码可能需要修改才能通过分离检查。
4. **工具支持**：IDE 和构建工具对分离检查的支持可能还不完善。

## 推荐阅读

- [捕获检查](./effect-tracking.md)：分离检查的基础
- [能力追踪](../usecases/effect-tracking.md)：更广泛的效果追踪概念
- [并发安全](../usecases/concurrency.md)：并发编程中的安全保证

# 引用

- https://virtuslab.com/blog/scala/introduction-to-scala-3-checking
- https://docs.scala-lang.org/scala3/reference/experimental/cc.html
- https://docs.scala-lang.org/scala3/reference/experimental/capture-checking/separation-checking.html
- https://capless.cc/
- https://2025.workshop.scala-lang.org/details/scala-2025/6/
