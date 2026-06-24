---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC10-encapsulation.md
title: 访问与封装（Access and Encapsulation）
description: 控制可见性并防止对内部实现的无权访问，编译器强制模块边界，客户端无法依赖不应看到的表示。
tags:
- 封装
- 可见性
- opaque types
- export
- open
- transparent trait
- 作用域限定
- Scala 3
- vibe-types
- UC10
timestamp: '2026-06-24T12:05:06Z'
---

# 访问与封装（Access and Encapsulation）

## 约束目标

控制可见性并防止对内部实现的无权访问。模块边界由编译器强制——客户端无法依赖它们不应看到的表示，扩展点被显式声明。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 不透明类型（Opaque types） | 完全隐藏底层表示 | [T03 newtypes-opaque](../catalog/newtypes-opaque.md) |
| Export 子句 | 无需继承的选择性委托 | [T21 encapsulation](../catalog/encapsulation.md) |
| `open` 修饰符 | 显式选择加入跨模块继承 | [T21 encapsulation](../catalog/encapsulation.md) |
| Transparent trait | 控制 trait 身份是否泄漏到推断类型中 | [T21 encapsulation](../catalog/encapsulation.md) |
| 上下文函数（Context functions） | 将能力限定在某个块内而不全局暴露 | [T42 context-functions](../catalog/context-functions.md) |

## 模式

### 模式 1 — 用不透明类型隐藏表示

在定义作用域之外，客户端无法访问或模式匹配底层类型。抽象是完全的且零成本的。

```scala
object money:
  opaque type USD = BigDecimal

  object USD:
    def apply(amount: BigDecimal): USD = amount
    val Zero: USD = BigDecimal(0)

  extension (a: USD)
    def +(b: USD): USD   = a + b   // 在作用域内是 BigDecimal + BigDecimal
    def *(n: Int): USD   = a * n
    def show: String     = f"$$${a}%.2f"

// 在 `money` 对象之外：
import money.*

val total = USD(9.99) + USD(4.50)
total.show // "$14.49"
// total + BigDecimal(1)   // 编译错误——在外部 USD ≠ BigDecimal
// val raw: BigDecimal = total // 编译错误
```

### 模式 2 — 用 export 实现选择性委托

暴露被包装对象 API 的精选子集，无需继承，也无需手动转发每个方法。

```scala
object db:
  class Connection private[db] (host: String):
    def query(sql: String): List[String] = ???
    def execute(sql: String): Int = ???
    def unsafeRawSocket: java.net.Socket = ??? // 内部

  class SafeConnection(private val conn: Connection):
    export conn.{query, execute}
    // `unsafeRawSocket` 未被导出——对客户端不可见

val safe = SafeConnection(Connection("localhost"))
safe.query("SELECT 1") // 可编译
// safe.unsafeRawSocket // 编译错误——未导出
```

### 模式 3 — 用 `open` 修饰符控制跨模块继承

默认情况下（在 `-source:future` 或 `open` 特性告警下），没有 `open` 的类不应在其定义文件之外被继承。这使扩展点显式化。

```scala
// 库代码
open class Template: // 显式可扩展
  def header: String = ""
  def body: String = ""   // 默认实现——预期被覆写
  def footer: String = ""

class InternalHelper: // 未标记 open——在此文件之外继承
  def run(): Unit = ()    // 会触发告警或错误

// 客户端代码（不同文件/模块）
class MyPage extends Template: // OK——Template 是 open 的
  override def body: String = "<p>hello</p>"

// class MyHelper extends InternalHelper // 告警：InternalHelper 不是 open 的
```

### 模式 4 — 通过作用域限定符实现包私有

Scala 的访问修饰符接受作用域限定符，以将可见性限制在特定的外层包或类中。

```scala
package com.example.app

package db:
  class Schema:
    private[db]  def migrate(): Unit = ()     // 在 `db` 包内可见
    private[app] def snapshot(): Unit = ()     // 在 `app` 包内可见
    private      def internalOnly(): Unit = () // 仅在 Schema 内可见

package api:
  import db.Schema
  class Endpoint:
    val s = Schema()
    // s.migrate()      // 编译错误——private[db]
    s.snapshot()        // 可编译——private[app] 包含 api
    // s.internalOnly() // 编译错误——private
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 隐藏表示 | `private[this]` 构造器 + 伴生 `apply`——仍会通过模式匹配或 `.copy` 泄漏；value class 存在装箱问题 | 不透明类型——在定义作用域外完全不透明，零成本，无 `.copy` 泄漏 |
| 选择性委托 | 手写转发方法——繁琐且易错 | `export` 子句——编译器生成转发器，可选或通配 |
| 控制继承扩展 | `sealed`（仅同文件）或 `final`（完全不可扩展）；没有中间地带 | `open` 修饰符——跨文件继承需要显式选择加入；非 open 类会告警 |
| Transparent trait | 不可用——推断类型总是包含 trait 身份 | `transparent trait`——编译器从推断类型中省略该 trait，减少 API 表面 |
| 作用域限定符 | `private[scope]`——相同语法和语义 | Scala 3 中未变 |

## 何时选择哪个特性

**不透明类型** 是数据封装最强的工具。每当内部表示必须对客户端不可见时使用——领域原语、句柄、令牌。它们替代了 value class 和手工包装模式。

**Export 子句** 替代了"为委托而继承"。当你持有一个服务的引用并希望暴露其部分 API 时，`export` 比继承更干净。使用选择性导出（`export x.{a, b}`）保持表面精简。

**`open` 修饰符** 是一个库设计工具。当扩展是契约的一部分（模板方法、插件钩子）时标记 `open`；当扩展会破坏不变量时不标记。在 `-source:future` 下，非 open 类被其他文件继承时会产生告警。

**Transparent trait** 适用于不应出现在推断类型中的标记 trait 或实现细节混入（如 `Product`、`Serializable`）。标记为 `transparent` 以保持 API 签名整洁。

**作用域限定符**（`private[pkg]`）仍然是包内 API 的正确工具——在一个模块内跨类共享但对消费者隐藏的功能。与不透明类型组合以实现分层封装。

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC10-encapsulation.md
- 相关用例：[extensibility](extensibility.md)、[builder-config](builder-config.md)
