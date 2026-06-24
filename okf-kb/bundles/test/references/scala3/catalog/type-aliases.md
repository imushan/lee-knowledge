---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T23-type-aliases.md
title: 类型别名（Type Aliases）
description: 用 type 为已有类型引入完全透明的别名，或用抽象类型成员声明“存在但未揭示”的类型，不创建新的类型边界。
tags:
- T23
- Scala 3
- vibe-types
- 类型别名
- 抽象类型成员
- 路径依赖类型
timestamp: '2026-06-24T12:04:50Z'
---

# 类型别名（Type Aliases）

**起始版本：** Scala 3.0

## 简介

**类型别名**（`type X = ...`）为已有类型引入一个新名字，但在类型检查层面不创建独立类型。别名完全透明：`X` 与其右侧在所有地方都可互换。Scala 3 支持简单别名（`type Name = String`）、参数化别名（`type Pair[A] = (A, A)`）、trait/类中的抽象类型成员（`type Elem`）以及其身份依赖于外层值的路径依赖类型。类型别名与 **不透明类型**（`opaque type X = ...`）有本质区别——后者在定义作用域之外创建独立类型。

## 可表达的约束

**类型别名让你为复杂类型起有意义的名字，减少重复、提升可读性，同时对类型检查器完全透明。** 它不引入新的类型边界——使用别名与使用底层类型的代码可自由互换。抽象类型成员则提供另一种约束：让 trait 声明"我有一个类型，但不揭示它是什么"，把选择推迟给实现者。

## 最小示例

**简单别名：**

```scala
type UserName = String
type Age = Int

case class User(name: UserName, age: Age)
val u: User = User("Alice", 30)
val n: String = u.name // OK -- UserName is transparent, it IS String
```

**参数化别名：**

```scala
type Pair[A] = (A, A)
type Result[A] = Either[String, A]

def divide(a: Int, b: Int): Result[Int] =
  if b == 0 then Left("division by zero") else Right(a / b)

val p: Pair[Int] = (1, 2) // same as (Int, Int)
```

**抽象类型成员：**

```scala
trait Collection:
  type Elem
  def add(e: Elem): Unit
  def elements: List[Elem]

class IntBuffer extends Collection:
  type Elem = Int
  private val buf = scala.collection.mutable.ListBuffer[Int]()
  def add(e: Int): Unit = buf += e
  def elements: List[Int] = buf.toList
```

**路径依赖类型：**

```scala
trait Graph:
  type Node
  type Edge
  def connect(from: Node, to: Node): Edge

val g1: Graph = ???
val g2: Graph = ???
// g1.Node and g2.Node are distinct types
// val n: g1.Node = g2.newNode() // error: type mismatch
```

**类型别名 vs. 不透明类型：**

```scala
// Transparent alias -- NO type safety
type Meters = Double
type Seconds = Double
val d: Meters = 3.0
val t: Seconds = d   // compiles! Meters and Seconds are both Double

// Opaque type -- full type safety, see T03
object Units:
  opaque type Meters = Double
  opaque type Seconds = Double
// Outside: Meters and Seconds are distinct types
```

## 与其他特性的交互

| 特性 | 如何组合 |
|---|---|
| **不透明类型**（[newtypes-opaque](newtypes-opaque.md)） | 不透明类型是类型别名的"类型安全兄弟"。为便利命名用透明别名；需要防止偶然混用的独立类型时用不透明类型。 |
| **匹配类型**（[match-types](match-types.md)） | 类型别名可定义为匹配类型：`type Elem[X] = X match { case List[t] => t; case Option[t] => t }`，实现类型层面的模式匹配。 |
| **泛型与边界**（[generics-bounds](generics-bounds.md)） | 抽象类型成员可带边界（`type T >: Cat <: Animal`），提供与有界类型参数相同的约束能力，但以路径依赖方式解析。 |
| **依赖类型**（[path-dependent-types](path-dependent-types.md)） | 路径依赖类型（`x.T`）自然源自抽象类型成员，是 Scala 依赖类型能力的基础。 |
| **Given 实例**（[type-classes](type-classes.md)） | 可为类型别名提供 given 实例。由于别名透明，`String` 的实例也服务于 `UserName`（若 `type UserName = String`）。这既是特性也是隐患——不透明类型可避免此问题。 |
| **类型 lambda**（[type-lambdas](type-lambdas.md)） | 命名的参数化类型别名（`type MapTo[V] = [K] =>> Map[K, V]`）通常比内联类型 lambda 更易读。 |

## 注意事项与局限

1. **透明别名不提供类型安全。** 对编译器而言 `type Meters = Double` 与 `type Seconds = Double` 都是 `Double`。需要独立类型时请用不透明类型（见 [newtypes-opaque](newtypes-opaque.md)）。
2. **循环别名会被拒绝。** `type A = List[A]` 非法——编译器会检测到循环。递归类型需要用类或 trait 定义。
3. **抽象类型成员与方差。** 抽象类型成员不能带显式 `+`/`-` 方差标注。其方差由使用位置决定，可能不如类型参数标注清晰。
4. **路径依赖类型的身份。** 同一类的两个实例产生不同的路径依赖类型：即便 `a` 与 `b` 运行时类相同，`a.T` 与 `b.T` 也不相关。这对类型安全很强，但当你希望它们相同时会令人意外。
5. **错误信息中的别名展开。** 编译器有时在错误信息中展开别名，使其更难读；有时又保留别名名。这种不一致在调试时可能造成困惑。
6. **类型别名无 `Mirror`。** 类型别名没有 `Mirror` 实例（它们不是类），因此类型类派生不适用于它们。派生作用于底层类型（若它是 case class 或 enum）。
7. **通配别名。** `type F[_] = List[Int]` 合法（类型参数被忽略），但可能令人困惑。编译器允许它，但在类型类解析时可能产生意外行为。

## 初学者心智模型

类型别名是一个 **昵称**。就像"Bob"和"Robert"指的是同一个人，`type UserName = String` 意味着 `UserName` 与 `String` 处处是同一类型，编译器会自由替换。这对可读性有用，但不提供防止混用值的保护。若你需要保护——"尽管存储方式相同，但要当作不同类型对待"——请改用不透明类型。

抽象类型成员（`type Elem`）是一个 **承诺**："这个 trait 有一个元素类型，但在有人实现我之前我不会告诉你它是什么。"

## 常见类型检查器报错

```
-- [E007] Type Mismatch Error ---
trait Container:
  type Elem
  def get: Elem
val c1: Container = ???
val c2: Container = ???
val e: c1.Elem = c2.get
^^^^^^
Found: c2.Elem
Required: c1.Elem
Fix: path-dependent types from different values are distinct.
Use a common reference or a type parameter instead.
```

```
-- [E046] Cyclic Reference Error ---
type Tree = List[Tree]
^^^^^^^^^
Recursion limit exceeded. Cyclic alias: type Tree
Fix: use a class or enum for recursive types:
enum Tree:
  case Leaf(value: Int)
  case Branch(children: List[Tree])
```

```
-- Error ---
type Handler = String => Unit
val h: Handler = 42
^^
Found: Int
Required: String => Unit
Note: the alias is expanded in the error. Handler = String => Unit.
```

## 用例交叉引用

- 为复杂领域类型命名以提升可读性，见 [领域建模](../usecases/domain-modeling.md)。
- 用抽象类型成员封装内部表示，见 [封装](../usecases/encapsulation.md)。
- 用路径依赖类型实现模块级类型安全，见 [可扩展性](../usecases/extensibility.md)。
- 用参数化类型别名作为类型级计算的构造块，见 [类型运算](../usecases/type-arithmetic.md)。

# 引用

- 原始资料：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T23-type-aliases.md
- Scala 3 Reference: Type Aliases — https://docs.scala-lang.org/scala3/reference/new-types/type-lambdas.html
- Scala 3 Reference: Abstract Type Members — https://docs.scala-lang.org/scala3/book/types-abstract.html
- Scala 3 Reference: Opaque Types — https://docs.scala-lang.org/scala3/reference/other-new-features/opaques.html
- Scala 3 Reference: Path-Dependent Types — https://docs.scala-lang.org/scala3/book/types-dependent.html
