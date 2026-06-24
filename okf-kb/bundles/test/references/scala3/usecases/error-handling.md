---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC08-error-handling.md
title: 错误处理（Error Handling）
description: 以类型安全的方式处理错误，让编译器追踪可能发生的错误并确保被处理，避免静默吞没异常。
tags:
- 错误处理
- CanThrow
- ADT
- 联合类型
- 能力追踪
- Scala 3
- vibe-types
- UC08
timestamp: '2026-06-24T12:04:20Z'
---

# 错误处理（Error Handling）

## 约束目标

以类型安全的方式处理错误，使编译器能够追踪哪些错误可能发生、确保它们被处理，并防止错误被静默吞没。开发者需要在 checked exceptions、错误 ADT、联合类型通道以及基于能力的追踪之间做出选择。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| CanThrow 能力 | 通过能力参数实现轻量级 checked exceptions | [T12 effect-tracking](../catalog/effect-tracking.md) |
| Enum / ADT | 封闭的错误层次结构，支持穷尽匹配 | [T01 algebraic-data-types](../catalog/algebraic-data-types.md) |
| 联合类型（Union types） | 无需共同父类型的即席错误通道 | [T02 union-intersection](../catalog/union-intersection.md) |
| 上下文函数（Context functions） | 在调用链中隐式传播错误处理能力 | [T42 context-functions](../catalog/context-functions.md) |
| 捕获检查（Capture checking） | 追踪函数捕获了哪些能力，包括错误效果 | [T12 effect-tracking](../catalog/effect-tracking.md) |

## 模式

### 模式 1 — 用 CanThrow 实现轻量级 checked exceptions

Scala 3 实验特性：方法将抛出的异常声明为能力需求，调用方必须提供该能力或处理异常。

```scala
import language.experimental.saferExceptions

class ValidationError(msg: String) extends Exception(msg)
class NetworkError(msg: String) extends Exception(msg)

def validate(input: String)(using CanThrow[ValidationError]): String =
  if input.isEmpty then throw ValidationError("empty input")
  else input.trim

def fetch(url: String)(using CanThrow[NetworkError]): String =
  if !url.startsWith("http") then throw NetworkError(s"bad url: $url")
  else s"content of $url"

def process(url: String)(using CanThrow[ValidationError], CanThrow[NetworkError]): String =
  val clean = validate(url)
  fetch(clean)

// 调用方必须同时处理两种异常：
@main def run() =
  try
    val result = process("http://example.com")
    println(result)
  catch
    case e: ValidationError => println(s"Validation: ${e.getMessage}")
    case e: NetworkError    => println(s"Network: ${e.getMessage}")

// 漏掉某个 catch 分支不会导致编译错误，
// 但在没有 try 包裹的情况下调用 process 会报错。
```

### 模式 2 — 带穷尽匹配的错误 ADT

将错误建模为 `enum`，编译器强制要求处理每个分支。

```scala
enum AppError:
  case NotFound(id: String)
  case Unauthorized(user: String)
  case RateLimited(retryAfter: Int)

case class Result[+A](value: Either[AppError, A]):
  def map[B](f: A => B): Result[B] = Result(value.map(f))
  def flatMap[B](f: A => Result[B]): Result[B] = Result(value.flatMap(a => f(a).value))

def lookup(id: String): Result[String] =
  if id == "42" then Result(Right("found it"))
  else Result(Left(AppError.NotFound(id)))

def handle(r: Result[String]): String = r.value match
  case Right(v) => v
  case Left(AppError.NotFound(id))       => s"$id not found"
  case Left(AppError.Unauthorized(u))    => s"$u denied"
  case Left(AppError.RateLimited(sec))   => s"retry in ${sec}s"

// 删除任何分支都会触发编译告警（在 -Werror 下为错误）
```

### 模式 3 — 联合类型错误通道

使用联合类型组合没有共同基类的互不相关错误类型。

```scala
case class ParseError(msg: String)
case class IoError(path: String, cause: String)
case class Timeout(ms: Long)

type Fallible[A] = A | ParseError | IoError | Timeout

def readConfig(path: String): Fallible[Map[String, String]] =
  if !path.endsWith(".conf") then ParseError(s"not a .conf file: $path")
  else if path.contains("missing") then IoError(path, "file not found")
  else Map("key" -> "value")

def useConfig(path: String): String =
  readConfig(path) match
    case m: Map[?, ?]      => s"loaded ${m.size} keys"
    case ParseError(msg)   => s"parse error: $msg"
    case IoError(p, c)     => s"IO error on $p: $c"
    case Timeout(ms)       => s"timed out after ${ms}ms"
```

### 模式 4 — 基于能力的错误追踪（捕获检查）

在函数类型中追踪错误处理能力，让编译器知道哪些效果会流经计算。

```scala
import language.experimental.captureChecking

trait Logger:
  def log(msg: String): Unit

trait ErrorHandler:
  def handle(e: Exception): Unit

// 返回的闭包类型会捕获其依赖：
def riskyOp(using l: Logger^, h: ErrorHandler^): () ->{l, h} String =
  () =>
    l.log("starting risky operation")
    try
      "success"
    catch
      case e: Exception =>
        h.handle(e)
        "recovered"

// 纯函数不捕获任何能力：
def pureCompute(x: Int): Int = x * 2 // 无需任何能力
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| Checked exceptions | 不可用；Java 的 checked exceptions 被 Scala 类型系统擦除 | `CanThrow` 能力——可选的 checked exceptions，无需 Java 的繁琐 |
| 错误 ADT | `sealed trait` + `case class`；相同模式，样板代码更多 | `enum`——简洁，自带 `ordinal` 与 `values` |
| 联合类型错误 | 无法表达；需要 `Either` 嵌套或 Shapeless 的 `Coproduct` | `A \| E1 \| E2`——直接、扁平、无包装类型 |
| 能力追踪 | 不可用；依赖手工约定或效果库（ZIO、Cats Effect） | 捕获检查在类型中追踪能力；编译器强制 |
| 错误穷尽性 | `sealed` 可用，但告警容易被忽略 | 默认更严格；`enum` + 模式匹配提供可靠穷尽性 |

## 何时选择哪个特性

**使用 `CanThrow`** 当你希望在不把所有逻辑包进 `Either` 的前提下获得轻量级 checked exceptions。最适合异常是自然错误模型、但希望编译器验证其被捕获的应用。注意：该特性仍为实验性。

**使用错误 ADT** 当错误是领域模型的核心组成部分——每个分支都携带有意义的数据，调用方必须处理每种情况。这是最常见、最可移植的做法。

**使用联合类型** 当错误来自不同库或领域、没有共同基类，且你希望避免包装类型时。联合类型天然可组合：只需在返回类型上加 `| NewError`。

**使用捕获检查** 当追踪函数可能执行哪些副作用与追踪其错误模式同等重要时。这是最高级的选项，且为实验性。

**组合使用**：用 ADT 表达领域错误，在多领域交汇的 API 边界使用联合类型，对不应污染领域类型的基础设施异常使用 `CanThrow`。

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC08-error-handling.md
- 相关用例：[effect-tracking](effect-tracking.md)、[exhaustiveness](invalid-states.md)
