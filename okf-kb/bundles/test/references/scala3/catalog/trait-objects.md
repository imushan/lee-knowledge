---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T36-trait-objects.md
title: 基于 trait 的动态分派 (Trait Objects)
description: Scala 3 的 trait 与抽象类通过 JVM 虚方法分派提供运行时多态，sealed/open/Matchable 控制扩展与匹配边界。
tags:
- Scala 3
- vibe-types
- T36
- trait
- 动态分派
- sealed
- open
- Matchable
timestamp: '2026-06-24T12:06:51Z'
---

# 基于 trait 的动态分派 (Trait Objects)

> **引入版本：** Scala 2（trait 与抽象类）；Scala 3 用 `open`、`sealed`、`Matchable` 限制加以细化

## 简介

在 Scala 3 中，**trait** 与**抽象类**通过 JVM 虚方法分派提供运行时多态。一个以 trait 类型声明的变量可以持有任何扩展该 trait 的类实例，方法调用在运行时通过 JVM 的 vtable 机制解析。与 Rust 不同（Rust 中 trait 引用需要显式 `dyn Trait` 标记并携带胖指针），Scala 中**所有** trait 引用默认都是动态分派的——通过超类型引用的 trait 方法调用没有 "静态分派" 模式。

trait 可以声明抽象方法（无方法体）、具体方法（带默认方法体）以及通过 `val`/`var` 定义的态。抽象类增加了单继承限制但可接受构造器参数。它们共同构成 Scala 面向对象多态的骨干，是类型类与 given 实例提供的编译期多态的运行时对应物。

## 可表达的约束

**trait 引用保证所持有的值实现了该 trait 的所有抽象成员，具体调用的方法在运行时由对象的实际类决定。** `sealed` 修饰符限制哪些类可以扩展该 trait（仅同文件），启用穷尽模式匹配。`open` 修饰符标记一个类是为扩展而设计的。`Matchable` 控制一个 trait 引用是否可作为模式匹配的 scrutinee。

## 最小示例

```scala
trait Animal:
  def name: String
  def sound: String
  def greet: String = s"I'm $name and I say $sound" // 具体默认

class Dog(val name: String) extends Animal:
  def sound = "Woof"

class Cat(val name: String) extends Animal:
  def sound = "Meow"

// 动态分派：运行时类型决定调用哪个 `sound`
val pets: List[Animal] = List(Dog("Rex"), Cat("Whiskers"))
pets.map(_.greet)
// List("I'm Rex and I say Woof", "I'm Whiskers and I say Meow")
```

## 与其他特性的交互

| 特性 | 组合方式 |
|---------|-----------------|
| **类型类 / given**（见 [type-classes](type-classes.md)） | 类型类提供编译期（ad-hoc）多态；trait 提供运行时（子类型）多态。需要在不修改既有类型的情况下回溯性合规时选类型类；需要为异构集合提供公共超类型时选 trait。 |
| **ADT / 枚举**（见 [algebraic-data-types](algebraic-data-types.md)） | `sealed trait` + `case class` 是标准 ADT 编码。sealing 把子类限制在定义文件内，启用穷尽匹配。 |
| **类型收窄 / Matchable**（见 [type-narrowing](type-narrowing.md)） | 对 trait 引用做模式匹配会收窄类型。`Matchable` 控制引用是否允许匹配，保护不透明类型抽象。 |
| **封装**（见 [encapsulation](encapsulation.md)） | `sealed` vs `open` vs 默认（ad-hoc 扩展警告）让库作者细粒度控制谁可扩展 trait。`final` 阻止所有扩展。 |
| **交集类型**（见 [union-intersection](union-intersection.md)） | 一个值可被声明为 `Printable & Serializable`，要求同时实现两个 trait。这是 Scala 对多 trait 约束的回应。 |

## 注意事项与局限

1. **没有静态分派选项。** 与 Rust 对泛型的单态化不同，Scala 在通过超类型引用调用 trait 方法时始终通过 vtable 分派。JIT 编译器可能对热点调用点去虚化，但这不保证。
2. **菱形继承。** 一个类可混入多个定义了相同方法的 trait。Scala 用**线性化（linearization）**解决冲突：`extends` 子句中最右侧的 trait 胜出，`super` 调用遵循线性化顺序。这对来自单继承语言的开发者可能意外。
3. **sealed 不等于 final。** `sealed` trait 仍可被扩展——但只能在同一源文件内。文件外的代码无法新增子类型，从而启用穷尽匹配。
4. **trait 初始化顺序。** 含 `val` 定义的 trait 在子类于 `val` 初始化前访问它时可能引发 `NullPointerException`。在 trait 中用 `lazy val` 或 `def` 可避免初始化顺序陷阱。
5. **抽象类 vs trait。** 抽象类可有构造器参数，在 JVM 上略高效（单 vtable 而非接口分派）。但一个类只能继承一个抽象类，却可混入多个 trait。
6. **Matchable 限制。** 在 `-language:strictEquality` 或显式 `Matchable` 约束下，不能对 `Any` 类型引用做模式匹配。需要安全向下转型的 trait 应扩展 `Matchable`。

## 入门心智模型

把 trait 视为一个**带内置名牌的契约**。任何签署契约（扩展该 trait）的类必须填写所有空行（抽象方法）。当你持有以该 trait 类型声明的引用时，你可以调用契约中的任何方法，JVM 在运行时查看名牌以找到正确实现。你不知道（也无需知道）实际签署的是哪个类——你只信任契约。

## 示例 A —— 用于穷尽匹配的 sealed trait

```scala
sealed trait Shape:
  def area: Double

case class Circle(radius: Double) extends Shape:
  def area = math.Pi * radius * radius

case class Rect(w: Double, h: Double) extends Shape:
  def area = w * h

def describe(s: Shape): String = s match
  case Circle(r)   => s"Circle with radius $r"
  case Rect(w, h)  => s"Rectangle ${w}x$h"
// 无需默认分支——编译器知道匹配是穷尽的
```

## 示例 B —— 用于框架扩展的 open 类

```scala
case class Request(path: String)
case class Response(status: Int, body: String)

open class HttpHandler:
  def handle(req: Request): Response =
    Response(200, "OK")

// 另一文件中的客户端代码可以扩展，因为有 `open`
class LoggingHandler extends HttpHandler:
  override def handle(req: Request): Response =
    println(s"Handling ${req.path}")
    super.handle(req)
```

## 用例交叉引用

- 见 [可扩展性](../usecases/extensibility.md)：trait 定义扩展点；`open` / `sealed` 控制可扩展性边界。
- 见 [非法状态不可表示](../usecases/invalid-states.md)：sealed trait 把居民限制为已知子类型，使非法状态不可表示。

# 引用

- [Scala 3 Reference — Traits](https://docs.scala-lang.org/scala3/reference/other-new-features/trait-parameters.html)
- [Scala 3 Reference — Open Classes](https://docs.scala-lang.org/scala3/reference/other-new-features/open-classes.html)
- [Scala 3 Reference — Matchable](https://docs.scala-lang.org/scala3/reference/other-new-features/matchable.html)
- [Scala 3 Book — Traits](https://docs.scala-lang.org/scala3/book/domain-modeling-tools.html#traits)
