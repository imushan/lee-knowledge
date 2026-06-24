---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC11-effect-tracking.md
title: 效果追踪（Effect Tracking）
description: 在类型层面追踪副作用——IO、异常、变异、能力；函数签名声明它能做什么，编译器拒绝未声明的效果。
tags:
- 效果追踪
- CanThrow
- 能力
- 上下文函数
- tagless final
- 捕获检查
- Scala 3
- vibe-types
- UC11
timestamp: '2026-06-24T12:05:25Z'
---

# 效果追踪（Effect Tracking）

## 约束目标

在类型层面追踪副作用——IO、异常、变异、能力。函数签名声明它能做什么；编译器拒绝执行未声明效果的代码。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 捕获检查（Capture checking） | 追踪值捕获了哪些能力；实验性效果系统 | [T12 effect-tracking](../catalog/effect-tracking.md) |
| 上下文函数（Context functions） | 在调用链中传递隐式能力 | [T42 context-functions](../catalog/context-functions.md) |
| Givens / Using | 通过隐式解析提供并要求能力 | [T05 type-classes](../catalog/type-classes.md) |
| 不透明类型（Opaque types） | 以零成本包装效果证据 | [T03 newtypes-opaque](../catalog/newtypes-opaque.md) |
| CanThrow | 通过能力实现 checked exceptions | [T12 effect-tracking](../catalog/effect-tracking.md) |

## 模式

### 模式 1 — 用 CanThrow 实现 checked exceptions

Scala 3 的 `CanThrow` 机制把异常转化为能力。抛出异常的函数必须声明该能力；调用方必须提供它。

```scala
import language.experimental.saferExceptions

class ValidationError(msg: String) extends Exception(msg)
class IOError(msg: String) extends Exception(msg)

// 声明可能抛出 ValidationError
def parseAge(s: String)(using CanThrow[ValidationError]): Int =
  val n = s.toIntOption.getOrElse:
    throw ValidationError(s"Not a number: $s")
  if n < 0 then throw ValidationError("Age cannot be negative")
  n

// 声明两种可能的异常
def readAndParseAge(path: String)(
  using CanThrow[IOError], CanThrow[ValidationError]
): Int =
  val content = // ... 读文件，可能抛出 IOError
    "25"
  parseAge(content)

// 在边界处——转换为 Either
val result: Either[ValidationError, Int] =
  try Right(parseAge("42"))
  catch case e: ValidationError => Left(e)
// CanThrow[ValidationError] 由 `try` 提供
```

### 模式 2 — 基于能力的 IO 追踪

将 IO 建模为显式能力。执行 IO 的函数要求该能力；纯函数则不提及它。

```scala
trait IO:
  def println(msg: String): Unit
  def readLine(): String

// 纯函数——不要求 IO 能力
def validate(name: String): Either[String, String] =
  if name.nonEmpty then Right(name) else Left("empty")

// 有副作用——要求 IO
def greet(using io: IO): Unit =
  io.println("What is your name?")
  val name = io.readLine()
  validate(name) match
    case Right(n) => io.println(s"Hello, $n!")
    case Left(e)  => io.println(s"Error: $e")

// 在程序边界提供能力
@main def run() =
  given IO with
    def println(msg: String) = scala.Predef.println(msg)
    def readLine() = scala.io.StdIn.readLine()
  greet // 此处解析 IO 能力
```

### 模式 3 — 用上下文函数编码 Reader/Writer 效果

上下文函数让你无需在每个调用点显式传递依赖，即可将其穿引通过整个计算。

```scala
type Config = Map[String, String]
type Configured[A] = Config ?=> A

def dbUrl: Configured[String] =
  summon[Config].getOrElse("db.url", "jdbc:h2:mem:")

def poolSize: Configured[Int] =
  summon[Config].getOrElse("db.pool", "10").toInt

def connectInfo: Configured[String] =
  s"${dbUrl} (pool=${poolSize})"

// 在边界处提供上下文
val info = connectInfo(using Map("db.url" -> "jdbc:postgresql://localhost/mydb"))
// "jdbc:postgresql://localhost/mydb (pool=10)"
```

### 模式 4 — 用 givens 实现 tagless final

将效果编码为类型构造器，并通过 `given` 提供解释器。业务逻辑对效果类型是多态的。

```scala
trait Store[F[_]]:
  def get(key: String): F[Option[String]]
  def put(key: String, value: String): F[Unit]

trait Logger[F[_]]:
  def info(msg: String): F[Unit]

def program[F[_]](using store: Store[F], logger: Logger[F], m: cats.Monad[F]): F[Unit] =
  import cats.syntax.flatMap.*
  import cats.syntax.functor.*
  for
    _ <- logger.info("Starting")
    v <- store.get("counter")
    _ <- store.put("counter", v.fold("1")(n => (n.toInt + 1).toString))
    _ <- logger.info("Done")
  yield ()

// 在边界装配解释器：
// given Store[IO] = ...
// given Logger[IO] = ...
// program[IO].unsafeRunSync()
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| Checked exceptions | 不可用——所有异常非受检；第三方基于 `Either` 的模式 | `CanThrow` 能力——异常在类型中追踪；`try` 提供能力 |
| 能力传递 | 隐式参数（`implicit io: IO`）——思路相同，仪式更多 | `using` / `given` + 上下文函数——更轻的语法，上下文函数类型 `IO ?=> A` |
| Reader/Writer 效果 | Monad transformer 或 `Reader[Config, A]`——运行时开销、复杂栈 | 上下文函数（`Config ?=> A`）——编译器脱糖，运行时无包装类型 |
| Tagless final | 在 `implicit` 下工作良好——原则不变 | `given` / `using` 语法更轻；`transparent inline given` 可消除抽象开销 |
| 捕获检查 | 不可用 | Scala 3 实验性——编译器在类型中追踪捕获的引用 |

## 何时选择哪个特性

**CanThrow** 是在不放弃 `throw`/`catch` 的前提下追踪异常的正确起点。它增量地增加类型安全——不必把所有错误处理都改写为 `Either`。在与抛出异常的 Java 库集成时使用。

**能力 trait**（如上面的 `IO` 模式）适用于显式标记有副作用代码并通过替换实现进行测试的场景。它们简单、无需框架，且适用于任何效果类型。

**上下文函数** 替代 Reader monad 用于依赖注入。当某个值需要在整个调用链中"在作用域内"可用、但你不想手动传递时使用。它们天然组合且无运行时包装。

**Tagless final** 仍然是抽象效果系统本身的工具——当同一业务逻辑需要在不同运行时（如 `IO`、`Future`、测试用的 `Id`）上运行时使用。它需要一个 monad 库。

**捕获检查**（实验性）是最严格的方式：编译器追踪闭包捕获了*哪些*能力，防止能力泄漏。待该特性稳定后，可考虑用于安全关键代码。

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC11-effect-tracking.md
- 相关用例：[error-handling](error-handling.md)、[state-machines](state-machines.md)
