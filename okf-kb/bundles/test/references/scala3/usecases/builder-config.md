---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC09-builder-config.md
title: DSL 与构建器模式（DSL and Builder Patterns）
description: 构建类型安全的 DSL 与流式 API，让编译器强制约束正确的使用方式，非法构造序列或缺字段即为编译错误。
tags:
- DSL
- 构建器
- Builder
- 幻影类型
- 上下文函数
- 扩展方法
- GADT
- Scala 3
- vibe-types
- UC09
timestamp: '2026-06-24T12:04:44Z'
---

# DSL 与构建器模式（DSL and Builder Patterns）

## 约束目标

构建类型安全的 DSL 与流式 API，让编译器强制正确使用。非法的构造序列、缺失的必填字段以及类型错误的组合都必须是编译错误。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 上下文函数（Context functions） | 带隐式接收者的作用域 DSL 块 | [T42 context-functions](../catalog/context-functions.md) |
| 扩展方法（Extension methods） | 无需继承或包装的流式链式调用 | [T19 extension-methods](../catalog/extension-methods.md) |
| 依赖函数类型（Dependent function types） | 返回类型依赖于参数值/类型 | [T53 path-dependent-types](../catalog/path-dependent-types.md) |
| 不透明类型（Opaque types） | DSL 令牌与标识符的轻量级包装 | [T03 newtypes-opaque](../catalog/newtypes-opaque.md) |
| Inline | 编译期 DSL 验证与展开 | [T16 compile-time-ops](../catalog/compile-time-ops.md) |
| GADT | 带类型安全求值的类型化表达式树 | [T01 algebraic-data-types](../catalog/algebraic-data-types.md) |

## 模式

### 模式 1 — 用上下文函数实现作用域 DSL 块

使用上下文函数类型（`A ?=> B`）创建一个构建器隐式可用的代码块。

```scala
import scala.collection.mutable.ListBuffer

class HtmlBuffer:
  private val parts = ListBuffer[String]()
  def addTag(tag: String)(content: String): Unit =
    parts += s"<$tag>$content"
  def result: String = parts.mkString("\n")

type Html[A] = HtmlBuffer ?=> A

def html(build: Html[Unit]): String =
  val buf = HtmlBuffer()
  build(using buf)
  buf.result

def div(content: Html[Unit]): Html[Unit] =
  summon[HtmlBuffer].addTag("div")("")
  content

def p(text: String): Html[Unit] =
  summon[HtmlBuffer].addTag("p")(text)

def h1(text: String): Html[Unit] =
  summon[HtmlBuffer].addTag("h1")(text)

val page = html:
  h1("Title")
  div:
    p("Hello")
    p("World")

// p("orphan") —— 在 html 块之外无法编译（作用域内无 HtmlBuffer）
```

### 模式 2 — 用幻影类型构建器强制必填字段

使用幻影类型追踪哪些字段已被设置。`build` 方法仅在所有必填字段都存在时才可用。

```scala
sealed trait Yes
sealed trait No

case class ServerConfig(host: String, port: Int, maxConn: Int)

class ServerBuilder[HasHost <: Yes | No, HasPort <: Yes | No](
  host: String = "", port: Int = 0, maxConn: Int = 100
):
  def withHost(h: String): ServerBuilder[Yes, HasPort] =
    new ServerBuilder(h, port, maxConn)
  def withPort(p: Int): ServerBuilder[HasHost, Yes] =
    new ServerBuilder(host, p, maxConn)
  def withMaxConn(m: Int): ServerBuilder[HasHost, HasPort] =
    new ServerBuilder(host, port, m)
  def build(using HasHost =:= Yes, HasPort =:= Yes): ServerConfig =
    ServerConfig(host, port, maxConn)

object ServerBuilder:
  def apply(): ServerBuilder[No, No] = new ServerBuilder()

val cfg = ServerBuilder()
  .withHost("0.0.0.0")
  .withPort(8080)
  .withMaxConn(500)
  .build // 可编译——两个必填字段都已设置

// ServerBuilder()
//   .withPort(8080)
//   .build // 编译错误——host 未设置
```

### 模式 3 — 用扩展方法实现流式链式调用

在不使用包装的情况下为现有类型添加领域方法，从而得到自然易读的管道。

```scala
case class Query(table: String, filters: List[String] = Nil, lim: Option[Int] = None)

extension (q: Query)
  def where(predicate: String): Query =
    q.copy(filters = q.filters :+ predicate)
  def limit(n: Int): Query =
    q.copy(lim = Some(n))
  def sql: String =
    val base  = s"SELECT * FROM ${q.table}"
    val wheres = if q.filters.isEmpty then "" else q.filters.mkString(" WHERE ", " AND ", "")
    val lim    = q.lim.fold("")(n => s" LIMIT $n")
    base + wheres + lim

val query = Query("users")
  .where("age > 18")
  .where("active = true")
  .limit(100)
  .sql
// "SELECT * FROM users WHERE age > 18 AND active = true LIMIT 100"
```

### 模式 4 — 基于 GADT 的表达式 DSL（类型安全求值）

构建一棵类型化表达式树，其中每个节点携带其结果类型。求值是完全且类型安全的。

```scala
enum Expr[A]:
  case Lit(value: Int) extends Expr[Int]
  case Str(value: String) extends Expr[String]
  case Gt(lhs: Expr[Int], rhs: Expr[Int]) extends Expr[Boolean]
  case If[T](
    cond: Expr[Boolean], yes: Expr[T], no: Expr[T]
  ) extends Expr[T]
  case Concat(a: Expr[String], b: Expr[String]) extends Expr[String]

def eval[A](e: Expr[A]): A = e match
  case Expr.Lit(v)     => v
  case Expr.Str(v)     => v
  case Expr.Gt(l, r)   => eval(l) > eval(r)
  case Expr.If(c, y, n) => if eval(c) then eval(y) else eval(n)
  case Expr.Concat(a, b) => eval(a) + eval(b)

val program: Expr[String] =
  Expr.If(
    Expr.Gt(Expr.Lit(10), Expr.Lit(5)),
    Expr.Str("big"),
    Expr.Str("small")
  )

val result: String = eval(program) // "big"

// Expr.If(Expr.Gt(Expr.Lit(1), Expr.Lit(2)), Expr.Lit(0), Expr.Str("x"))
// —— 编译错误：分支中 Expr[Int] 与 Expr[String] 不匹配
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 作用域 DSL 块 | 隐式参数 + by-name 参数；显式 `implicit` 关键字让 DSL 表面杂乱 | 上下文函数——构建器对用户不可见；自然的块语法 |
| 幻影构建器 | 同样的 `=:=` 证据技巧；可用但到处都需要 `implicit` 关键字 | `using` 子句——更简洁的调用点；联合类型简化了幻影编码 |
| 流式链式调用 | `implicit class` 包装——额外分配、伴生对象杂乱 | `extension`——零成本、无包装对象，可顶层或限定作用域 |
| 类型化表达式树 | 通过 `sealed trait` + `case class` 实现 GADT；模式匹配推断较弱 | `enum` GADT——声明简洁；编译器在匹配分支中可靠地细化类型 |

## 何时选择哪个特性

**使用上下文函数** 当 DSL 具有天然的"作用域"——HTML 构建器、配置块、测试夹具。它们消除显式参数传递，并强制某些操作只能在正确的块内发生。

**使用幻影类型构建器** 当构造过程有必填字段或要求的顺序时。类型参数追踪已配置的内容，`build` 方法要求完整性证据。

**使用扩展方法** 用于面向读取或链式的 DSL，目标是针对现有类型（查询、数据转换、断言）的流式管道。

**使用 GADT** 当 DSL 是一种将被解释或编译的表达式语言时。每个节点上的类型参数确保无法构造类型错误的表达式（如 `if int then string else boolean`）。

**组合使用** 在较大的 DSL 中：上下文函数用于外层作用域，幻影构建器用于资源构造，扩展方法用于链式调用，GADT 用于核心表达式模型。

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC09-builder-config.md
- 相关用例：[encapsulation](encapsulation.md)、[compile-time](compile-time.md)
