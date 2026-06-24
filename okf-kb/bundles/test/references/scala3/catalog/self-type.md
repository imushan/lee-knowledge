---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T33-self-type.md
title: 自身类型 (Self Types)
description: 自身类型注解声明 trait 对其他能力的依赖关系而不建立继承链，是 Cake 模式与模块化组合的基础。
tags:
- Scala 3
- vibe-types
- T33
- 自身类型
- self type
- Cake 模式
- 依赖注入
- trait 组合
timestamp: '2026-06-24T12:06:50Z'
---

# 自身类型 (Self Types)

> **引入版本：** Scala 3.0（继承自 Scala 2；语法不变）

## 简介

trait 或 class 上的**自身类型注解**（`self: T =>`）声明：该 trait 的任何具体实现也必须是 `T` 的子类型，但实际上并不继承 `T`。在被注解的 trait 内部，`this` 的类型为 `T & Self`，可访问 `T` 的全部成员。这与继承（`extends T`）不同：trait 在类型层级中不会成为 `T` 的子类型，`T` 也不出现在该 trait 的线性化（linearization）中。自身类型表达的是一种**需求**（"我需要 `T` 的能力"），而非建立 "是一个" 的关系。该机制是 Scala 独有的 Cake 模式与模块化组合模式的基础。

## 可表达的约束

**自身类型注解约束 `this`，使得任何混入该 trait 的类必须同时混入（或继承）所需类型；该约束在实例化点而非定义点强制。** 这让 trait 可以依赖其不继承的能力，实现正交组合：`Logging` trait 可以要求 `HasConfig` 而不继承它，编译器则确保任何混入 `Logging` 的具体类也提供 `HasConfig`。

## 最小示例

**基础自身类型：**

```scala
trait HasLogger:
  def log(msg: String): Unit

trait UserService:
  self: HasLogger =>
  def createUser(name: String): Unit =
    log(s"Creating user: $name") // OK —— self: HasLogger 保证 log 存在
    // ... 实际创建逻辑
```

**具体类必须满足自身类型约束：**

```scala
// OK：满足 HasLogger 要求
class AppService extends UserService with HasLogger:
  def log(msg: String): Unit = println(msg)

// 错误：非法继承 —— UserService 要求 HasLogger
// class BrokenService extends UserService
```

**自身类型 vs 继承：**

```scala
trait A:
  def hello: String = "A"

// 继承：B 是一个 A
trait B extends A:
  def greet: String = hello

// 自身类型：C 要求一个 A，但本身不是 A
trait C:
  self: A =>
  def greet: String = hello // OK —— A 的成员可访问

val b: A = new B {} // OK：B <: A
// val c: A = new C with A {} // C 不是 <: A；必须用 (C with A)
val c: C & A = new C with A {} // OK
```

**Cake 模式（模块化组合）：**

```scala
trait DatabaseComponent:
  def query(sql: String): List[Map[String, Any]]

trait UserRepositoryComponent:
  self: DatabaseComponent =>
  def findUser(id: Int): Option[Map[String, Any]] =
    query(s"SELECT * FROM users WHERE id = $id").headOption

trait EmailComponent:
  def sendEmail(to: String, body: String): Unit

trait NotificationComponent:
  self: UserRepositoryComponent & EmailComponent =>
  def notifyUser(id: Int, msg: String): Unit =
    findUser(id).foreach: user =>
      sendEmail(user("email").toString, msg)

// 把所有东西装配在一起：
object ProductionApp
  extends NotificationComponent
  with UserRepositoryComponent
  with DatabaseComponent
  with EmailComponent:
  def query(sql: String) = ??? // 真实 DB
  def sendEmail(to: String, body: String) = ??? // 真实邮件
```

**命名自身引用：**

```scala
trait Outer:
  outer => // 把 `this` 命名为 `outer` 以消除歧义
  trait Inner:
    def enclosing: Outer = outer // 指向 Outer 的 this
```

## 与其他特性的交互

| 特性 | 组合方式 |
|---|---|
| **交集类型**（见 [union-intersection](union-intersection.md)） | 多个自身类型需求用交集表示：`self: A & B =>`。具体类必须混入所有所需类型。 |
| **given 实例**（见 [type-classes](type-classes.md)） | 自身类型可要求一个提供 given 实例的 trait，使能力在 trait 体内可用而无需显式导入。 |
| **不透明类型**（见 [newtypes-opaque](newtypes-opaque.md)） | 自身类型可要求定义了不透明类型的 trait，使需求 trait 能访问那些不透明类型上定义的操作（但不能访问底层表示）。 |
| **枚举 / ADT**（见 [algebraic-data-types](algebraic-data-types.md)） | 自身类型很少与（sealed 的）枚举共用。Cake 模式更适用于服务/模块组合，而非数据建模。 |
| **扩展方法**（见 [extension-methods](extension-methods.md)） | 扩展方法为添加能力提供了自身类型之外的另一种选择：不必通过自身类型要求 trait，可以外部扩展该类型。选择取决于是否需要访问私有成员。 |
| **export 子句**（见 [encapsulation](encapsulation.md)） | export 子句提供另一种无需继承的委托形式。自身类型在类型层面组合 trait；export 在成员层面组合值。两者都避免了继承。 |

## 注意事项与局限

1. **自身类型不建立子类型关系。** `trait A { self: B => }` 并**不**使 `A <: B`。你不能在需要 `B` 的地方传一个 `A`。约束只向内流动（在 `A` 内部 `this` 类型为 `A & B`）以及在实例化时（任何实现 `A` 的类也必须实现 `B`）。
2. **循环自身类型是合法的（且会被使用）。** `trait A { self: B => }` 与 `trait B { self: A => }` 合法。这在 Cake 模式中支持相互依赖，但可能令人困惑且难以测试。
3. **自身类型检查较晚。** 约束只有在具体类被实例化时才被验证。一个自身类型未满足的抽象类可以正常编译；错误只在尝试 `new` 它时出现。
4. **Scala 自身类型 vs Python 的 `Self`。** Python 的 `typing.Self` 标注返回类型以支持流式接口（`def set(self, ...) -> Self`）。Scala 的自身类型注解约束的是 `this`，是根本不同的机制。要在 Scala 中实现类似 Python 的 `Self` 返回类型，请用 F-bounded 多态（见 [generics-bounds](generics-bounds.md)）。
5. **Cake 模式已不再流行。** 虽然自身类型支持 Cake 模式，但现代 Scala 3 惯用法更偏好基于构造器的依赖注入、`given`/`using` 表达能力，或 effect 系统。Cake 模式仍然有效，但被视为重量级。
6. **自身类型注解不能是 `private`。** 自身类型需求对任何阅读 trait 签名的人都可见。没有办法隐藏该依赖。
7. **名字遮蔽。** 自身类型名字（`self`、`this` 或任意标识符）可能遮蔽外层 `this` 引用。在嵌套 trait 中用不同名字（`outer =>`）避免混淆。

## 入门心智模型

把自身类型视为一个**前置条件声明**："我，trait `UserService`，要求谁混入我，谁就得同时带来 `HasLogger`。" 这就像大学课程写 "需要先修 MATH 101"——你不会因为上了这门课就变成 MATH 101，但没有它你无法选课。

这与 `extends HasLogger` 不同，后者说 "我**是**一个 HasLogger"，并把 `HasLogger` 放入继承链。自身类型保持继承链分离，同时确保能力存在。

## 常见类型检查器报错

```
-- [E157] Type Error ---
trait Repo:
  self: Database =>
  def find(id: Int): Option[Row]

class MyRepo extends Repo
^^^^
illegal inheritance: self-type MyRepo does not conform to
Repo's self type Repo & Database
Fix: mix in the required trait:
class MyRepo extends Repo with Database
```

```
-- [E007] Type Mismatch Error ---
trait HasAuth:
  self: HasLogger =>
  def login(): Unit = log("logged in")

val auth: HasLogger = new HasAuth with HasLogger { ... }
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Found: HasAuth & HasLogger
Required: HasLogger
Note: HasAuth is NOT a subtype of HasLogger despite the self-type.
Fix: ascribe to the intersection type, or restructure with inheritance.
```

## 用例交叉引用

- 见 [领域建模](../usecases/domain-modeling.md)：用自身类型需求构建模块化领域服务。
- 见 [封装](../usecases/encapsulation.md)：在不继承的情况下封装模块依赖。
- 见 [effect 追踪](../usecases/effect-tracking.md)：通过自身类型注解表达能力需求。
- 见 [可扩展性](../usecases/extensibility.md)：用 Cake 模式构建可扩展模块系统。

# 引用

- [Scala 3 Reference: Self Types](https://docs.scala-lang.org/scala3/book/domain-modeling-tools.html#traits)
- [Scala 3 Reference: Trait Composition](https://docs.scala-lang.org/scala3/book/domain-modeling-tools.html)
- [Scala Specification: Self Type Annotations](https://scala-lang.org/files/archive/spec/3.4/05-classes-and-objects.html)
