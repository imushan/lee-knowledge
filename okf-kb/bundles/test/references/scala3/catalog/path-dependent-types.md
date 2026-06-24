---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T53-path-dependent-types.md
title: 路径依赖类型
description: Scala 中类型成员的身份依赖于访问它的运行时路径（对象实例），编译器将不同实例的类型成员视为不相关类型。
tags:
- 路径依赖类型
- 类型成员
- 依赖函数类型
- 精炼类型
- 类型投影
- T53
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:06:51Z'
---

# 路径依赖类型

> **引入版本：** Scala 2（类型成员与路径依赖类型）；Scala 3 精炼规则——类型投影 `T#Inner` 被限制为仅允许具体类型

## 简介

在 Scala 3 中，trait 或 class 可以用 `type Inner` 声明**类型成员**。该成员的类型取决于你通过哪个具体**实例**访问它：给定 `val x: Outer` 和 `val y: Outer`，类型 `x.Inner` 和 `y.Inner` 是不同的。这就是**路径依赖类型**——"路径"（`x.` 或 `y.`）是类型身份的一部分。

路径依赖类型允许你将类型绑定到特定对象身份而不暴露具体表示。`Graph` trait 中的抽象 `type Node` 意味着每个图实例携带自己的节点类型，编译器阻止混用不同图的节点。这是类型安全异构集合、插件式扩展性以及"cake pattern"（在 Scala 3 中已基本被更简单的惯用法取代）背后的机制。

Scala 3 中，**类型投影**（`T#Inner`）被限制：只能从具体类投影，不能从抽象类型参数投影。这关闭了 Scala 2 中长期存在的健全性漏洞，使路径依赖类型成为处理类型成员的主要方式。

## 可表达的约束

**类型成员的身份依赖于访问它的运行时路径（对象实例）。编译器将 `a.T` 和 `b.T` 视为不相关类型，除非能证明 `a` 和 `b` 是同一对象。**

- 同一类的两个实例默认产生不兼容的类型成员。
- 宽化到外围类的抽象类型成员会擦除路径：`Outer#Inner`（允许时）忘记是哪个实例。
- 类型成员可以是抽象的（无 `=`）、有边界（`>:` / `<:`）或具体的（`= Int`）。

## 最小示例

```scala
trait Cage:
  type Animal
  def resident: Animal
  def admit(a: Animal): Unit

val dogCage = new Cage:
  type Animal = String  // 仅为示例命名
  def resident = "Rex"
  def admit(a: String) = println(s"Welcome $a")

val catCage = new Cage:
  type Animal = Int     // 不同的具体类型
  def resident = 42
  def admit(a: Int) = println(s"Cat #$a admitted")

dogCage.admit(dogCage.resident)  // OK — 类型对齐
// dogCage.admit(catCage.resident)  // 错误：Found catCage.Animal, Required dogCage.Animal
```

## 与其他特性的交互

- **类型别名**：类型成员是作用于实例的类型别名。抽象类型成员是没有右侧的别名——由子类或具体对象填入。
- **依赖函数类型**：方法 `def get(k: Key): k.Value` 通过依赖方法类型使用路径依赖类型。Scala 3 以 `(k: Key) => k.Value` 将其提升为一等。
- **封装**：抽象类型成员隐藏表示。客户端看到 `graph.Node` 而不知道内部是 `Int`——比私有构造器更强。
- **类型类**：抽象类型成员是 trait 上类型参数的替代方案。类型成员避免深层嵌套泛型代码中的"类型参数污染"。
- **Match types**：类型成员可定义为 match type：`type Elem = this.type match { case IntCol => Int; case StrCol => String }`。参见 [match-types](match-types.md)。
- **Opaque types**：Opaque type 概念上是定义在定义作用域外隐藏的类型成员，与路径依赖类型互补用于封装。参见相关章节。

## 注意事项与局限

1. **Scala 3 中类型投影受限。** `T#Inner` 仅当 `T` 是具体类类型时允许。写 `def foo[T <: Outer]: T#Inner` 不再编译。改用路径依赖类型（`(t: T) => t.Inner`）或 match types。
2. **单例类型收窄。** 要在 `val` 上使用路径依赖类型，编译器必须追踪单例类型。赋值给 `var` 或宽化到父类型会丢失路径：`val c: Cage = dogCage` 意味着 `c.Animal` 是抽象的，而非 `String`。
3. **类型成员与类型参数——设计选择。** 类型成员适合"输出型"类型（由实现者决定）；类型参数适合"输入型"类型（由调用者选择）。任意混用会产生混乱的 API。
4. **无通用类型投影逃生口。** Scala 2 中 `Cage#Animal` 可指"任意 cage 的 animal"。Scala 3 中仅对具体外层类型有效。对抽象情况，使用 match types 或多态函数的存在式编码。
5. **路径稳定性。** 路径必须是稳定标识符——`val`、`object` 或 `this`。方法结果和 `var` 不是稳定路径，故 `def getCage: Cage` 不会给你可用的 `getCage.Animal`。
6. **相等性证明。** 要将一个路径的值传给期望另一个路径的方法，可能需要证明路径相等。Scala 3 没有内建路径相等见证；重构代码共享同一路径。

## 入门心智模型

想象每个对象都带着一个**个人的类型手提箱**。当你在类中声明 `type Animal` 时，每个实例把自己的 `Animal` 类型装进手提箱。类型 `myDog.Animal` 字面意思是"myDog 手提箱里的 Animal 类型"。两个不同对象有两个不同手提箱——即使它们是同一类的实例——所以它们的类型不混。

## 示例 A — 类型安全的键值存储

每个键知道自己的值类型，编译器阻止存取错误类型。

```scala
trait Key:
  type Value
  def name: String

def intKey(n: String): Key { type Value = Int } =
  new Key { type Value = Int; def name = n }

def strKey(n: String): Key { type Value = String } =
  new Key { type Value = String; def name = n }

class Store:
  private var data: Map[String, Any] = Map.empty
  def put(k: Key)(v: k.Value): Unit =
    data = data.updated(k.name, v)
  def get(k: Key): Option[k.Value] =
    data.get(k.name).map(_.asInstanceOf[k.Value])

val age = intKey("age")
val name = strKey("name")
val store = Store()
store.put(age)(30)       // OK — age.Value 是 Int
store.put(name)("Alice") // OK — name.Value 是 String
// store.put(age)("thirty")  // 错误：Found String, Required age.Value (Int)
```

## 示例 B — 模块式封装的抽象类型成员

```scala
trait Graph:
  type Node
  type Edge
  def nodes: Set[Node]
  def edges(n: Node): Set[Edge]
  def target(e: Edge): Node

class CityGraph extends Graph:
  type Node = String
  type Edge = (String, String, Int)  // (from, to, distance)
  private val edgeList = Set(("A", "B", 10), ("B", "C", 20))
  def nodes = edgeList.flatMap(e => Set(e._1, e._2))
  def edges(n: String) = edgeList.filter(_._1 == n)
  def target(e: (String, String, Int)) = e._2

def traverse(g: Graph)(start: g.Node): List[g.Node] =
  // 编译器确保我们只用这张图的节点
  g.edges(start).map(g.target).toList

val city = CityGraph()
traverse(city)("A")  // OK — "A" 是 city.Node (String)
// traverse(city)(42)  // 错误：Found Int, Required city.Node
```

## 示例 C — 带精炼的依赖方法类型

```scala
trait TypedColumn:
  type Elem
  def get(row: Int): Elem

val ages: TypedColumn { type Elem = Int } = new TypedColumn:
  type Elem = Int
  def get(row: Int) = row * 10  // 占位

val names: TypedColumn { type Elem = String } = new TypedColumn:
  type Elem = String
  def get(row: Int) = s"user-$row"

def readCell(col: TypedColumn)(row: Int): col.Elem = col.get(row)
val a: Int = readCell(ages)(1)      // 推断为 Int
val n: String = readCell(names)(1)  // 推断为 String
```

## 依赖函数类型与多态函数类型

Scala 3 将路径依赖方法提升为一等函数值。Scala 2 中 `def get(k: Key): k.Value` 这样的方法无法转为值——Scala 3 引入**依赖函数类型**弥合此差距。

```scala
trait Entry:
  type Key
  def key: Key

// 依赖函数类型 — 返回类型依赖参数路径
val extractKey: (e: Entry) => e.Key = (e: Entry) => e.key

// 多态函数类型 — 对类型参数全称量化
val reverser: [A] => List[A] => List[A] =
  [A] => (xs: List[A]) => xs.reverse
```

它们是带更精确 `apply` 方法的精炼 `FunctionN` trait 的语法糖，使保留路径依赖类型关系的回调和高阶函数成为可能：

```scala
trait Key:
  type Value
  def name: String

class Store:
  private var data: Map[String, Any] = Map.empty
  def put(k: Key)(v: k.Value): Unit = data = data.updated(k.name, v)
  def get(k: Key): Option[k.Value] =
    data.get(k.name).map(_.asInstanceOf[k.Value])

// 需要路径依赖回调的高阶函数
def transform(store: Store)(keys: List[Key])(
  f: (k: Key) => k.Value => k.Value
): Unit =
  for k <- keys do
    store.get(k).foreach(v => store.put(k)(f(k)(v)))
```

**注意：** 依赖函数字面量需要方法桥接（不能直接写依赖 lambda——eta 展开一个依赖方法）。多态函数值较冗长（`[A] => (xs: List[A]) => xs.reverse`）且无推断简写。类型参数和依赖参数**可以**在单个函数类型中组合（如 `[A] => (a: A, e: Entry) => (A, e.Key)` 可编译）。

## 用例交叉引用

- 通过抽象类型成员隐藏实现，客户端针对 `graph.Node` 编程而不知具体表示。参见用例 [封装](../usecases/encapsulation.md)。
- 类型安全的异构集合，每个键决定其值类型。参见用例 [领域建模](../usecases/domain-modeling.md)。
- 抽象类型成员作为扩展点：插件定义自己的 node/edge/config 类型。参见用例 [可扩展性](../usecases/extensibility.md)。
- 类型成员可追踪每实例状态，使状态转换路径依赖。参见用例 [状态机](../usecases/state-machines.md)。

# 引用

- 原始来源：[T53-path-dependent-types.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T53-path-dependent-types.md)
- [Scala 3 Reference — Abstract Type Members](https://docs.scala-lang.org/scala3/reference/new-types/type-lambdas.html)
- [Scala 3 Reference — Dependent Function Types](https://docs.scala-lang.org/scala3/reference/new-types/dependent-function-types.html)
- [Scala 3 Reference — Dropped: Type Projections](https://docs.scala-lang.org/scala3/reference/dropped-features/type-projection.html)
- [Scala 3 Reference — Match Types](https://docs.scala-lang.org/scala3/reference/new-types/match-types.html)
