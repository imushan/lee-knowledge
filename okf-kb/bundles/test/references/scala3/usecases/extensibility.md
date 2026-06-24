---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC14-extensibility.md
title: 扩展性（Extensibility）
description: 设计扩展点——控制什么可扩展、什么不可扩展，用显式契约替代 Scala 2 隐式开放的继承模型。
tags:
- 扩展性
- open
- export
- 扩展方法
- 类型类派生
- transparent trait
- givens
- Scala 3
- vibe-types
- UC14
timestamp: '2026-06-24T12:06:37Z'
---

# 扩展性（Extensibility）

## 约束目标

**设计扩展点——控制什么可以扩展、什么不可以扩展。**
库作者需要表达："此类型专为子类化而设计"对比"仅通过类型类扩展"对比"组合，而非继承"。Scala 3 用显式控制取代了 Scala 2 类的隐式开放性。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| Open 类 | 将类标记为可在其文件之外被继承；无 `open` 时，在 `-source:future` 下继承会产生告警 | [T21 encapsulation](../catalog/encapsulation.md) |
| Export 子句 | 显露组合对象的成员，以委托替代继承 | [T21 encapsulation](../catalog/encapsulation.md) |
| 扩展方法（Extension methods） | 为你不拥有的类型添加操作，带或不带类型类证据 | [T19 extension-methods](../catalog/extension-methods.md) |
| 类型类派生（Type-class derivation） | 为 ADT 机械地派生实例，无需子类化即可提供扩展性 | [T06 derivation](../catalog/derivation.md) |
| Transparent trait | 将实现混入从推断类型中隐藏，使其不泄漏到公共 API | [T21 encapsulation](../catalog/encapsulation.md) |
| Givens | 提供追溯扩展行为的类型类实例 | [T05 type-classes](../catalog/type-classes.md) |

## 模式

### 模式 A：用于追溯扩展的类型类模式

定义一个 trait，提供 given 实例，并使用扩展方法获得语法。新类型只需定义新的 given 即可获得该行为——无需修改既有代码。

```scala
trait Show[A]:
  extension (a: A) def show: String

given Show[Int] with
  extension (a: Int) def show: String = a.toString

given Show[Double] with
  extension (a: Double) def show: String = f"$a%.2f"

// 追溯：为第三方类型添加 Show
case class Point(x: Double, y: Double)
given Show[Point] with
  extension (p: Point) def show: String = s"(${p.x.show}, ${p.y.show})"

def log[A: Show](a: A): Unit = println(a.show)
// log(Point(1.0, 2.5)) => (1.00, 2.50)
```

### 模式 B：对第三方类型的扩展方法

当你不需要完整的类型类间接层时，普通扩展方法可直接添加操作。

```scala
extension (s: String)
  def words: List[String] = s.split("\\s+").toList
  def initials: String = s.words.map(_.head.toUpper).mkString

// "ada lovelace".initials => "AL"

// 条件扩展：仅当存在 Ordering 时可用
extension [A](xs: List[A])(using Ordering[A])
  def median: A =
    val sorted = xs.sorted
    sorted(sorted.size / 2)

// List(3, 1, 2).median => 2
// List("x", "y").median —— 仅因 Ordering[String] 存在才可编译
```

### 模式 C：用 export 实现组合优于继承

Export 子句转发组合对象的选定成员，使委托与继承一样简洁，但不与超类耦合。

```scala
class Logger:
  def info(msg: String): Unit  = println(s"[INFO] $msg")
  def error(msg: String): Unit = println(s"[ERROR] $msg")

class Metrics:
  def count(event: String): Unit        = println(s"count: $event")
  def gauge(name: String, v: Double): Unit = println(s"$name=$v")

class Service:
  private val logger = Logger()
  private val metrics = Metrics()
  export logger.*                                // info、error 在 Service 上可用
  export metrics.{count, gauge as measure}       // count + 重命名的 gauge

// val s = Service()
// s.info("started")           —— 转发给 logger
// s.measure("cpu", 0.42)      —— 转发给 metrics.gauge
```

### 模式 D：用 `open` 修饰符实现受控继承

无 `open` 时，在 `-source:future` 下从另一个文件继承一个类会触发告警。使用 `open` 表示一个类专为子类化设计；省略它则抑制临时扩展。

```scala
// 库代码
open class Renderer:
  def render(node: Node): String = node.toString
  // 子类可覆写 render 以自定义输出。

class Node(val tag: String, val children: List[Node])

// 客户端代码——OK，Renderer 是 open 的
class HtmlRenderer extends Renderer:
  override def render(node: Node): String =
    s"<${node.tag}>${node.children.map(render).mkString}"

// 对比：无 `open` 时此扩展会告警
class Formatter:
  def format(s: String): String = s.trim

// class FancyFormatter extends Formatter // 在 -source:future 下告警：Formatter 不是 open 的
```

使用 `final` 完全禁止扩展。当你既不打算也不禁止扩展、但也不承诺稳定的扩展契约时，使用默认（无修饰符）。

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 控制继承 | 所有非 `final` 类隐式 open；没有编译期信号表明某类专为扩展而设计 | `open` 修饰符使契约显式。从另一个文件继承非 open、非 final 类在 `-source:future` 下告警 |
| 委托 / 组合 | 需要手工转发方法或基于宏的委托 | `export` 子句自动生成转发器，保持完整类型保真 |
| 为类型添加方法 | 隐式类（`implicit class RichString(s: String)`），需要包装分配（除非是 value class） | `extension` 块：无包装、无隐式类样板。通过 `using` 实现条件扩展 |
| 类型类语法 | 用隐式类做语法 + 隐式 def 做实例。"Pimp my library" 惯用法 | `given`/`using` 做实例，`extension` 做语法，`derives` 做机械派生 |
| 从推断类型隐藏混入 | 不可能；所有超类型都出现在推断签名中 | `transparent` trait 将自身从推断类型中抑制 |

## 何时选择哪个特性

| 如果你需要…… | 推荐 |
|---|---|
| 对你不拥有的类型的追溯多态 | **类型类模式**（模式 A）：trait + given + extension。将行为与类型层次结构解耦 |
| 第三方类型上的几个便利方法 | **普通扩展方法**（模式 B）。无需 trait 或 given |
| 无继承耦合的复用 | **Export 子句**（模式 C）。严格优于从工具类继承 |
| 专为客户端扩展而设计的超类 | **`open` 修饰符**（模式 D）。记录契约并消除告警 |
| 不应出现在推断类型中的混入 | **`transparent` trait**。保持公共 API 签名整洁 |
| 为 case class / enum 机械生成实例 | **类型类派生**（`derives`）。避免为标准形状手写 given 实例 |

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC14-extensibility.md
- 相关用例：[encapsulation](encapsulation.md)、[builder-config](builder-config.md)
