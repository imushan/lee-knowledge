---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC16-nullability.md
title: 可空性与可选性（UC16）
description: 通过 Scala 3 显式可空（explicit nulls）在类型系统中大幅减少 NPE。
tags:
- 可空性
- explicit-nulls
- 'Null'
- Union
- UC16
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:08:21Z'
---

# 可空性与可选性（UC16）

## 约束目标

**通过类型系统大幅减少 NPE。**

默认所有引用都是不可空的。可空性必须在类型中显式声明，且每个可空值在使用前必须经过检查。编译器会拒绝在缺乏非空证明的情况下解引用可能为 null 的引用。该保证并非完全：在初始化器运行之前，非空字段在构造期间仍可能持有 `null`（使用 `-Wsafe-init` 检测）；Java 互操作的灵活类型（flexible types）也可能在边界处让 `null` 溜入。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 显式可空（explicit nulls） | 在 `-Yexplicit-nulls` 下，`Null` 不再是引用类型的子类型；可空值必须声明为 `T \| Null` | [T13 null-safety](../catalog/null-safety.md) |
| 联合类型 | `T \| Null` 是"可空 T"的标准编码，复用了一等联合类型 | [T02 union-intersection](../catalog/union-intersection.md) |
| Opaque types | 用安全 API 包装可空表示，对调用者隐藏 `null` | [T03 newtypes-opaque](../catalog/newtypes-opaque.md) |
| 匹配类型 | 在类型层面计算某类型是否可空，或泛型地剥离可空性 | [T41 match-types](../catalog/match-types.md) |

## 模式

### 模式 A：启用显式可空

在编译选项中启用 `-Yexplicit-nulls`。每个引用类型 `T` 都变为不可空。表达可空性需使用 `T | Null`。

```scala
// scalacOptions += "-Yexplicit-nulls"
val name: String = "Ada"
// val bad: String = null // error: found Null, required String
val nullable: String | Null = null // ok
// Cannot call methods directly on nullable types:
// nullable.length // error: length is not a member of String | Null
// Flow-sensitive narrowing after a null check:
if nullable != null then
  println(nullable.length) // ok: nullable is refined to String here
// Assert non-null with .nn (throws NPE if null):
val forced: String = nullable.nn
```

### 模式 B：用 `T | Null` 表达可空值，用 `.nn` 断言

显式建模可空数据。使用模式匹配、`Option` 转换或 `.nn` 安全地提取值。

```scala
def findUser(id: Long): User | Null =
  if id > 0 then User(id, "found") else null

case class User(id: Long, name: String)

// Pattern match to handle both cases:
findUser(42) match
  case u: User => println(u.name)
  case null => println("not found")

// Convert to Option for idiomatic Scala:
val maybeUser: Option[User] = Option(findUser(42)) // None if null

// Chain with .nn when you are certain it is non-null:
val user: User = findUser(42).nn // throws NPE if null
```

### 模式 C：带可空性注解的 Java 互操作

Java 方法默认返回灵活类型（flexible types）。被识别的 `@NonNull` / `@Nullable` 注解会在 Scala 边界处细化类型。

```scala ignore
// ignore: demonstrates Java-interop flexible types — requires the annotated
// Java classes `Repository`/`User` on the classpath so the compiler can read
// @Nullable/@NonNull and produce `T | Null` / `T`. That behavior cannot be
// reproduced by an isolated pure-Scala snippet, which is the point of the example.

// Given Java code:
// public class Repository {
//   @Nullable public User findById(long id) { ... }
//   @NonNull public List findAll() { ... }
// }
// In Scala 3 with explicit nulls:
val repo = Repository()
val user: User | Null = repo.findById(1) // @Nullable => T | Null
val all: java.util.List[User] = repo.findAll() // @NonNull => T (non-nullable)

// Without annotations, Java types are flexible (T?) —
// assignable to either T or T | Null depending on context.
// Use -Yno-flexible-types to force everything to T | Null for maximum safety.

// Escape hatch for gradual migration:
import scala.language.unsafeNulls
val unsafeUser: User = repo.findById(1) // compiles, but may NPE
```

### 模式 D：用匹配类型剥离可空性

定义一个匹配类型来移除 `| Null`，在必须同时处理可空与不可空类型参数的泛型代码中很有用。

```scala
//> using option -source:3.3
// A capture variable in a union pattern (`t | Null`) is allowed under the
// 3.3 match-type rules; the catch-all returns the input type `T` unchanged.
type StripNull[T] = T match
  case t | Null => t
  case _ => T

// StripNull[String | Null] = String
// StripNull[String] = String

def unwrap[T](value: T)(using ev: T =:= (StripNull[T] | Null)): Option[StripNull[T]] =
  val v = ev(value)
  if v != null then Some(v.asInstanceOf[StripNull[T]]) else None
// Useful in generic APIs that abstract over nullable/non-nullable parameters.
```

## Scala 2 对比

| 方面 | Scala 2 | Scala 3（显式可空） |
|---|---|---|
| Null 子类型化 | `Null <: AnyRef`，每个引用变量都可持有 `null` | `Null <: Any`，`String` 不接受 `null` |
| 表达可空性 | 惯例：使用 `Option[T]`，但无法阻止 `val s: String = null` | 类型系统：`T \| Null` 表可空，`T` 表非空，由编译器强制 |
| Java 互操作 | 所有 Java 引用类型隐式可空，无编译期检查 | 灵活类型（`T?`）桥接差异，识别 `@Nullable` / `@NonNull` 注解 |
| 流敏感类型细化 | 不可用，null 检查不会收窄类型 | `if x != null` 后，`x` 在分支体中被细化为非空 |
| 渐进式迁移 | 无迁移路径——`null` 始终合法 | `unsafeNulls` 导入允许迁移期将 `T \| Null` 当作 `T` 处理 |

## 何时选择哪个特性

| 需求 | 推荐 |
|---|---|
| 全项目 null 安全 | 启用 **`-Yexplicit-nulls`**（模式 A），让编译器找出每个未处理的 null |
| 惯用的可空返回值 | 在 API 边界使用 **`T \| Null`** 并立即转换为 **`Option`**（模式 B） |
| 安全的 Java 互操作 | 用 **`@NonNull`** / **`@Nullable`** 标注 Java 代码（模式 C），用 `-Yno-flexible-types` 获得最严格检查 |
| 泛型剥离可空性 | 使用 **匹配类型**（模式 D）计算类型参数的非空版本 |
| 从 Scala 2 渐进迁移 | 在尚未迁移的文件中先用 **`unsafeNulls`** 导入，再逐文件移除 |
| 对可空表示的安全包装 | 使用 **opaque type**，其伴生对象提供拒绝 `null` 的智能构造器，对调用者隐藏表示 |

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC16-nullability.md
