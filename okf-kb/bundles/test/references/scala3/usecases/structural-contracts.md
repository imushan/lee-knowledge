---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC05-structural-contracts.md
title: 结构化契约
description: 按值暴露的成员而非类层级来接受值，编译器静态验证鸭子类型契约。
tags:
- UC05
- Scala 3
- vibe-types
- 结构化类型
- 细化类型
- Selectable
- 鸭子类型
timestamp: '2026-06-24T12:08:40Z'
---

# 结构化契约

## 约束目标

按值暴露的成员来接受值，而不是按它所属的类层级。结构化类型与细化类型让你表达鸭子类型的契约，而编译器仍然对其做静态校验。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 结构化类型 | 接受任何具有匹配成员的值；无需共同父类型 | [结构化类型](../catalog/structural-typing.md) |
| 细化类型 | 通过追加成员要求来收窄一个类型 | [细化类型](../catalog/refinement-types.md) |
| Selectable / Dynamic | 通过 `selectDynamic` 为结构化定义的字段提供类型化访问 | [结构化类型](../catalog/structural-typing.md) |
| 联合类型 | 把不相关的结构化类型合并进单个参数 | [联合与交集类型](../catalog/union-intersection.md) |

## 模式

### 1 — 结构化类型作为参数

接受任何具有 `close(): Unit` 方法的对象，不论其类层级。

```scala
import reflect.Selectable.reflectiveSelectable

type Closeable = { def close(): Unit }

def safeUse[A](resource: Closeable)(f: Closeable => A): A =
  try f(resource)
  finally resource.close()

// 任何暴露 close() 的类都可以：
class MyConn:
  def close(): Unit = println("closed")
  def query(sql: String): String = s"result of $sql"

safeUse(MyConn())(r => println("using resource"))
```

### 2 — 用细化类型收窄基类型

对基类型细化以要求额外成员。编译器检查提供的值同时满足基类型和细化。

```scala
import reflect.Selectable.reflectiveSelectable

type Named  = { val name: String }
type HasAge = { val age: Int }
type Person = Named & HasAge

def greet(p: Person): String =
  s"Hello, ${p.name}, age ${p.age}"

// 任何类（或匿名实例）只要形状匹配即可：
val p: Person = new { val name = "Alice"; val age = 30 }
greet(p) // "Hello, Alice, age 30"
```

### 3 — 用 Selectable trait 实现类型化动态字段

实现 `Selectable` 以对结构化类型的记录提供编译期校验的字段访问。

```scala
class Record(fields: Map[String, Any]) extends Selectable:
  def selectDynamic(name: String): Any = fields(name)

type UserRec = Record { val name: String; val email: String }

val user: UserRec =
  Record(Map("name" -> "Alice", "email" -> "a@b.com")).asInstanceOf[UserRec]

// 类型化访问 —— 编译器知道这些字段存在：
val n: String = user.name
val e: String = user.email
// user.age // 编译错误 —— age 不在细化中
```

### 4 — 类型参数上的结构化约束

把泛型参数约束为任何暴露特定成员的类型。

```scala
import reflect.Selectable.reflectiveSelectable

def size[T <: { def length: Int }](t: T): Int = t.length

size("hello")       // 5 —— String 有 length
size(List(1, 2, 3)) // 3 —— List 有 length
// size(42)         // 编译错误 —— Int 没有 length
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 结构化类型 | 支持但需 `import language.reflectiveCalls`；运行时反射 | 同样的 import；`Selectable` trait 提供自定义分发的钩子 |
| 细化类型 | 可作为复合类型上的类型成员；冗长 | 同概念；配合 `&` 交集语法更清爽 |
| 类型化记录 | 没有宏或 Shapeless HList 无法表达 | `Selectable` + 细化类型提供内建路径 |
| 性能 | 总是反射调用——慢 | `Selectable` 实现可用 map 或代码生成替代反射 |

## 何时选择哪个特性

- **用结构化类型** 集成来自不同库、碰巧暴露相同 API 表面却没有共同 trait 的代码。
- **用细化类型** 当你想收窄基类型以要求特定额外成员时——例如要求任何值都同时具有 `name` 和 `age`。
- **用 Selectable** 构建类记录的抽象（如数据库行、配置对象），字段名在编译期已知但后端存储是 map 之类的结构。
- **优先使用名义类型**（trait、type-class）当你掌控代码、可以定义共同接口时。结构化类型增加了间接层与反射开销，应在集成边界处使用。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC05-structural-contracts.md
