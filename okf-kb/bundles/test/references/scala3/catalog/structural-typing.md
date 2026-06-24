---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T07-structural-typing.md
title: 结构类型、细化类型与命名元组
description: 通过结构类型与命名元组实现静态检查的鸭子类型与记录式类型，按成员签名而非具名层级约束值。
tags:
- T07
- Scala 3
- vibe-types
- 结构类型
- 命名元组
- Selectable
- 细化类型
- 鸭子类型
timestamp: '2026-06-24T12:05:26Z'
---

# 结构类型、细化类型与命名元组

> **引入版本：** Scala 3.0 | **最新变更：** Scala 3.7（命名元组）

## 简介

Scala 3 支持**结构类型**——按成员签名而非具名类层级定义的类型。结构类型是对父类型（通常是 `Selectable`）的细化，声明值必须提供的字段或方法。结构类型上的成员访问通过 `selectDynamic` / `applyDynamic` 分派，使库作者能完全控制解析策略。**命名元组**（Scala 3.7+）为元组扩展字段名，创建轻量的记录式类型，元素可按名访问（如 `person.age`）。命名元组通过 `Fields` 类型成员与 `Selectable` 集成，支持计算字段访问模式（如类型化查询 DSL）。

## 可表达的约束

**结构类型提供静态检查的鸭子类型——可以要求值拥有某些成员，而无需规定共同父类型。命名元组提供记录式类型，支持按位置与按名访问、零开销表示，并通过 `NamedTuple.From` 与 case class 无缝互操作。**

## 最小示例

### 带 Selectable 的结构类型

```scala
class Record(elems: (String, Any)*) extends Selectable:
  private val fields = elems.toMap
  def selectDynamic(name: String): Any = fields(name)

type Person = Record { val name: String; val age: Int }
val p: Person = Record("name" -> "Emma", "age" -> 42).asInstanceOf[Person]
println(p.name) // "Emma" —— 编译为 p.selectDynamic("name").asInstanceOf[String]
```

### 基于 Java 反射的结构类型

```scala
import scala.reflect.Selectable.reflectiveSelectable

type Closeable = { def close(): Unit }

def autoClose(f: Closeable)(op: Closeable => Unit): Unit =
  try op(f) finally f.close()
// f.close() 经 Java 反射分派
```

### 局部 Selectable 细化

```scala
trait Vehicle extends reflect.Selectable:
  val wheels: Int

val i3 = new Vehicle:
  val wheels = 4
  val range = 240      // 推断类型：Vehicle { val range: Int }

i3.range // OK —— 经 Selectable 的结构访问
```

### 命名元组

```scala
type Person = (name: String, age: Int)
val Bob: Person = (name = "Bob", age = 33)
Bob.name // "Bob"
Bob.age  // 33

// 模式匹配（按名或按位置）
Bob match
  case (age = a, name = n) => s"$n is $a"

// 无名元组可符合命名元组类型
val Laura: Person = ("Laura", 25) // OK
```

### 带 Selectable 的命名元组（计算字段）

```scala
trait Q[T] extends Selectable:
  type Fields = NamedTuple.Map[NamedTuple.From[T], Q]
  def selectDynamic(name: String): Any = ???

case class City(zipCode: Int, name: String, population: Int)
val city: Q[City] = ???
city.zipCode // 类型：Q[Int]
city.name    // 类型：Q[String]
```

## 与其他特性的交互

| 特性 | 交互 |
|---|---|
| `Selectable` trait | 结构类型与其运行时分派之间的桥梁；自定义 `Selectable` 子类可使用 map、反射、代码生成或任意策略。 |
| `scala.Dynamic` | 二者都使用 `selectDynamic`/`applyDynamic`，但结构类型是静态类型检查的，而 `Dynamic` 不是。 |
| 不透明类型 | `NamedTuple` 是一个不透明类型别名：`opaque type NamedTuple[N <: Tuple, +V <: Tuple] >: V = V`。名字仅存在于编译期，运行时被擦除。 |
| case class | `NamedTuple.From[CaseClass]` 提取与 case class 第一参数列表对应的命名元组类型，桥接名义类型与结构类型世界。 |
| 模式匹配 | 命名元组模式支持以任意顺序匹配字段子集；命名模式也可用于 case class。 |
| match 类型 | `Selectable` 的 `Fields` 类型成员可通过 match 类型或 `NamedTuple.Map` 计算，支持类型化查询 DSL。 |
| 扩展方法 | 命名元组的操作（`head`、`tail`、`map`、`zip`、`++`）以扩展方法形式定义在 `NamedTuple` 对象中。 |
| transparent inline | 可与结构类型结合在编译期生成 `Selectable` 包装器。 |

## 注意事项与局限

- **反射分派较慢。** 使用 `reflectiveSelectable` 会在运行时触发 Java 反射；所需 import 即为警示。自定义 `Selectable` 实现可避免此开销。
- **构造 Record 需 `asInstanceOf`。** 泛型 `Record` 类类型过弱，编译器无法校验细化；实践中由数据库层或宏处理此转换。
- **非 Selectable 的匿名类丢失细化。** 若父 trait 不继承 `Selectable`，匿名类中超出父类型声明的成员经推断类型不可见。
- **命名元组混合规则。** 同一元组内混用命名与无名元素非法；所有元素必须全部命名或全部无名。
- **命名元组顺序敏感。** `(name: String, age: Int)` 与 `(age: Int, name: String)` 是不同且不兼容的类型。
- **转换不对称。** 无名元组（按位置）是命名元组的子类型，但命名元组需显式 `.toTuple` 或编译器插入的转换才能变为无名元组；在类型构造子内部（如 `List[Person]` 到 `List[(String, Int)]`）不会自动转换。
- **一元数源不兼容。** `(age = 1)` 现为命名元组而非括号赋值，这是相对 Scala 2 的源码级变更。

## 用例交叉引用

- 使用结构类型与自定义 `Selectable` 进行数据库行访问，参见[领域建模](../usecases/domain-modeling.md)。
- 使用 `NamedTuple.From` 与计算 `Fields` 构建类型化查询 DSL，参见[编译期](../usecases/compile-time.md)。
- 为配置或 API 响应定义轻量记录类型而无需 case class，参见扩展性。
- 与共享方法签名但无共同接口的 Java 类做鸭子类型互操作。
- 命名元组模式匹配用于解构复杂返回值，参见[构建器配置](../usecases/builder-config.md)。

# 引用

- [T07-structural-typing.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T07-structural-typing.md)
