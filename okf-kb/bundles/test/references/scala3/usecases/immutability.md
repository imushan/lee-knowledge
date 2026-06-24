---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC06-immutability.md
title: 不可变性
description: 确保数据一旦创建便不可变，消除竞态、别名与陈旧引用类问题，让编译器更激进地推理代码。
tags:
- UC06
- Scala 3
- vibe-types
- 不可变性
- val
- final
- case class
- 不可变集合
timestamp: '2026-06-24T12:08:57Z'
---

# 不可变性

## 约束目标

确保数据一旦创建就不能再被改变。不可变性消除了一整类 bug——竞态条件、意外的别名、陈旧引用——并让编译器更激进地推理代码。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 不可变性标记（val、final） | 在绑定层面禁止重新赋值与覆写 | [不可变性标记](../catalog/immutability-markers.md) |
| Case class | 默认不可变的积类型；编译器生成 `copy` 用于函数式更新 | [代数数据类型](../catalog/algebraic-data-types.md) |
| 封闭层级 | 不可变变体的封闭集合 | [代数数据类型](../catalog/algebraic-data-types.md) |
| 不透明类型 | 零运行时成本的不可变包装 | [不透明类型](../catalog/newtypes-opaque.md) |
| 不可变集合 | `scala.collection.immutable` 中的默认集合 | [不可变性标记](../catalog/immutability-markers.md) |

## 模式

### 1 — val 与 var

`val` 禁止重新赋值，`var` 允许。处处优先用 `val`；仅当可变累加器确实更清晰时才用 `var`。

```scala
val name = "Alice" // 不可变绑定
// name = "Bob"    // 编译错误：reassignment to val

var counter = 0    // 可变 —— 谨慎使用
counter += 1       // 允许
```

### 2 — case class 的不可变性与函数式更新

`case class` 的所有字段默认都是 `val`。用 `copy` 做函数式更新，而非变异。

```scala
case class Config(host: String, port: Int, ssl: Boolean)

val base = Config("localhost", 8080, ssl = false)
val prod = base.copy(host = "prod.example.com", ssl = true)

// base 保持不变：
assert(base.host == "localhost")
assert(prod.host == "prod.example.com")
```

### 3 — 用封闭 enum 表达不可变状态

把 `enum` 与不可变数据结合，建模没有可变字段的状态。

```scala
enum Outcome:
  case Success(value: String)
  case Failure(error: String, retryable: Boolean)

def retry(o: Outcome): Outcome = o match
  case Outcome.Failure(err, true) => Outcome.Failure(err, retryable = false) // 新值
  case other                      => other                                    // 不变
```

### 4 — 以不可变集合为默认

Scala 的默认 import 给你不可变的 `List`、`Map`、`Set`、`Vector`。可变变体需要显式 import。

```scala
val xs = List(1, 2, 3)
val ys = xs :+ 4 // 新列表 —— xs 不变
// xs(0) = 99    // 编译错误 —— 没有 update 方法

val m  = Map("a" -> 1)
val m2 = m + ("b" -> 2) // 新 map
// m("a") = 99          // 编译错误

// 可变需要显式 opt-in：
import scala.collection.mutable
val buf = mutable.ArrayBuffer(1, 2, 3)
buf += 4 // 原地变异
```

### 5 — 用 final 防止覆写

给类或成员加 `final`，防止子类引入可变的覆写。

```scala
final case class Coordinate(x: Double, y: Double)
// class Mutable extends Coordinate(0, 0) // 编译错误 —— 不能继承 final 类

class Base:
  final val id: Int = 42
// 子类不能用 var 覆写 id
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| val / var | 语义相同 | 语义相同 |
| case class 字段 | 默认 `val`；可写 `case class C(var x: Int)` | 相同——仍允许 `var` 字段，但强烈不推荐 |
| 不可变集合 | 默认；同一套库 | 同一库；`LazyList` 取代了 `Stream` |
| final | 相同 | 相同；`enum` 的 case 隐式为 final |
| 函数式更新 | case class 的 `copy` 方法 | `copy` + Scala 3.5+ 的命名元组提供更多灵活性 |

## 何时选择哪个特性

- **默认使用 `val` 与不可变集合。** 这是基线——偏离时必须有理由。
- **用 case class** 承载所有领域数据。编译器免费给你 `copy`、`equals`、`hashCode` 与模式匹配。
- **用 `final`** 标注 case class 与关键绑定，防止子类重新引入可变性。
- **只有**在性能关键的紧循环或不逃逸出作用域的局部累加器内部才使用可变状态。把可变状态封装在不可变 API 之后。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC06-immutability.md
