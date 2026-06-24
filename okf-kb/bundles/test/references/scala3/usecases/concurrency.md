---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC21-concurrency.md
title: 并发（通过库）（UC21）
description: 通过 ZIO、Cats Effect、Akka Typed 与 Ox 等库在类型层面跟踪并发效应并强制结构化并发。
tags:
- 并发
- ZIO
- Cats Effect
- Akka Typed
- Ox
- 效应跟踪
- 结构化并发
- UC21
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:09:50Z'
---

# 并发（通过库）（UC21）

## 约束目标

在类型层面跟踪并发效应、强制结构化并发，并在类型层面防止数据竞争。Scala 3 没有内建的 `Send`/`Sync` 标记，但库生态——ZIO、Cats Effect、Akka Typed 与 Ox——将并发纪律编码进各自的类型系统。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 效应跟踪 | 库效应类型（`IO`、`ZIO`、`Task`）将副作用编码进类型签名 | [T12 effect-tracking](../catalog/effect-tracking.md) |
| 类型类 | `Concurrent`、`Async`、`Temporal` 层级约束函数可使用哪些效应 | [T05 type-classes](../catalog/type-classes.md) |
| 上下文函数 | 将线程能力（作用域、运行时）隐式穿透调用链 | [T42 context-functions](../catalog/context-functions.md) |
| Opaque types | 为 fiber ID、ref、作用域 token 提供零开销包装 | [T03 newtypes-opaque](../catalog/newtypes-opaque.md) |

## 模式

### 模式 1：用 ZIO 效应类型实现类型化并发

ZIO 编码了环境、错误通道与成功类型。并发组合子是类型安全的。

```scala
import zio.*

// ZIO[R, E, A]: needs environment R, may fail with E, succeeds with A
val fetchUser: ZIO[Any, Throwable, String] = ZIO.attempt("Alice")
val fetchOrder: ZIO[Any, Throwable, Int] = ZIO.attempt(42)

// Run in parallel — types compose:
val both: ZIO[Any, Throwable, (String, Int)] =
  fetchUser.zipPar(fetchOrder)

// Fibers are typed:
val forked: ZIO[Any, Nothing, Fiber[Throwable, String]] =
  fetchUser.fork

// Structured concurrency with scoped fibers:
val scoped: ZIO[Scope, Throwable, String] =
  ZIO.scoped {
    for
      fiber <- fetchUser.forkScoped
      result <- fiber.join
    yield result
  }
```

### 模式 2：带 Concurrent 类型类的 Cats Effect

Cats Effect 使用类型类层级约束函数可执行哪些效应。

```scala
import cats.effect.*
import cats.effect.implicits.*
import cats.syntax.all.*

// Only requires Concurrent — works with IO or any effect type
def fetchBoth[F[_]: Concurrent](
    fa: F[String],
    fb: F[Int]
): F[(String, Int)] =
  (fa, fb).parTupled

// Ref for safe shared mutable state:
def counter[F[_]: Concurrent]: F[Ref[F, Int]] =
  Ref.of[F, Int](0)

// Resource for structured lifecycle:
def managed[F[_]: Async]: Resource[F, String] =
  Resource.make(Async[F].delay("acquired"))(r => Async[F].delay(()))
```

### 模式 3：用 Akka Typed 实现消息类型化并发

Akka Typed actor 只接受匹配其声明协议类型的消息。

```scala ignore
import akka.actor.typed.*
import akka.actor.typed.scaladsl.*

enum Command:
  case Greet(name: String, replyTo: ActorRef[Greeting])
  case Stop
case class Greeting(message: String)

val greeter: Behavior[Command] = Behaviors.receive { (ctx, msg) =>
  msg match
    case Command.Greet(name, replyTo) =>
      replyTo ! Greeting(s"Hello, $name!")
      Behaviors.same
    case Command.Stop =>
      Behaviors.stopped
}
// greeter ! "raw string" // compile error — Command expected
```

### 模式 4：用 Ox 在虚拟线程上实现结构化并发

Ox 使用 Scala 3 上下文函数与 scoped value，在 JDK 21+ 虚拟线程上实现结构化并发。

```scala ignore
import ox.*

// Structured scope — all forks must complete before the scope exits:
val result: (String, Int) = supervised {
  val f1 = fork(fetchName())
  val f2 = fork(fetchAge())
  (f1.join(), f2.join())
}
def fetchName(): String = "Alice"
def fetchAge(): Int = 30

// Racing — first to complete wins, others are cancelled:
val fastest: String = supervised {
  raceSuccess(
    () => { Thread.sleep(100); "slow" },
    () => "fast"
  )
}
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 效应类型 | ZIO 与 Cats Effect 可在 2.12/2.13 上工作；模式相同 | 同样的库以 Scala 3 为目标；上下文函数简化了能力传递 |
| Akka Typed | 自 Akka 2.6 起在 Scala 2 上可用 | 相同 API；`enum` 让协议定义更整洁 |
| 结构化并发 | 仅库（ZIO scope、Cats Resource） | Ox 利用 Scala 3 上下文函数 + JDK 21 虚拟线程 |
| 线程安全标记 | 无内建 Send/Sync；基于约定 | 仍无内建标记；capture checking（实验性）可能引入编译器跟踪的能力 |

## 何时选择哪个特性

- **使用 ZIO** 当你想要一个内置齐全的效应系统，具备类型化错误、依赖注入的 layer 以及内建并发原语。适合完全投入 ZIO 生态的应用。
- **使用 Cats Effect** 当你想编写对效应类型多态的代码。适合库或已使用 Typelevel 技术栈的团队。
- **使用 Akka Typed** 用于基于 actor 的系统，其中并发被建模为长生命周期实体之间的类型化消息传递。
- **使用 Ox** 在虚拟线程上实现直接的结构化并发，无需完整效应系统的开销。适合 JDK 21+ 上偏好命令式风格并需要安全保证的应用。

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC21-concurrency.md
