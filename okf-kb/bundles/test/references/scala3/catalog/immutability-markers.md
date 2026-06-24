---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T32-immutability-markers.md
title: 不可变性标记 (Immutability Markers)
description: Scala 通过 val、final、sealed 与不可变集合在绑定、成员、层级与数据四个层面强制不可变性，全部由编译器检查。
tags:
- Scala 3
- vibe-types
- T32
- 不可变性
- val
- final
- sealed
- 不可变集合
timestamp: '2026-06-24T12:06:50Z'
---

# 不可变性标记 (Immutability Markers)

> **引入版本：** Scala 1.0（`val`、`final`）| Scala 3 继续并强化这些机制

## 简介

Scala 把不可变性作为默认：`val` 声明不可重新赋值的绑定，case class 参数默认为 `val`，标准库优先选择不可变集合。Scala 3 进一步加强了 `sealed` 与 `final` 的检查。关键机制包括：

- **`val` vs `var`** —— `val` 在初始化后不可重新绑定。这是最基础的不可变性标记，也是惯用默认。
- **`final`** —— 阻止子类中覆盖（用于成员）或完全阻止继承（用于类）。与 Java 不同，Scala 的 `final` 还阻止 `val` 被具有不同初始化器的 lazy val 或其他 val 覆盖。
- **`sealed`** —— 把扩展限制在同一文件内，启用穷尽匹配与封闭层级。
- **case class** —— 参数默认为 `val`；实例具有结构相等性与用于函数式更新的 `copy`，而非变异。
- **不可变集合** —— `scala.collection.immutable.*` 默认导入。开箱即用的 `List`、`Map`、`Set` 都是不可变的。

## 可表达的约束

**`val` 阻止重新绑定；`final` 阻止覆盖与继承；`sealed` 阻止文件外扩展。三者共同在绑定、成员与层级层面强制不可变性——全部由编译器检查，而非仅类型检查器。**

## 最小示例

```scala
val x = 42
// x = 43 // 编译错误：Reassignment to val

final class Config(val host: String, val port: Int)
// class MyConfig extends Config("", 0) // 编译错误：cannot extend final class

class Base:
  final def core: Int = 42
class Sub extends Base
// override def core: Int = 0 // 编译错误：cannot override final member
```

## 与其他特性的交互

| 特性 | 组合方式 |
|---------|-----------------|
| **ADT / 枚举**（见 [algebraic-data-types](algebraic-data-types.md)） | 枚举分支隐式为 `final` 且类似 `val`。每个分支是固定值；给枚举加 `sealed` 可阻止外部扩展。 |
| **不透明类型**（见 [newtypes-opaque](newtypes-opaque.md)） | 不透明类型别名天生不可变——类型别名没有 `var` 等价物。底层值若不经过伴生对象则无法被修改。 |
| **case class**（见 [record-types](record-types.md)） | case class 参数默认为 `val`。用 `copy` 做函数式更新：`user.copy(name = "Alice")` 创建新实例而非变异。 |
| **封装**（见 [encapsulation](encapsulation.md)） | 把 `private` 与 `val`、`final` 结合形成纵深防御：private val 外部不可访问，final 内部不可覆盖。 |
| **扩展方法**（见 [extension-methods](extension-methods.md)） | 扩展方法不能覆盖已有的 `final` 方法——编译器拒绝歧义。 |

## 注意事项与局限

1. **`val` 不代表深层不可变。** `val xs = ArrayBuffer(1, 2, 3)` 阻止重新绑定 `xs`，但缓冲区内容仍可变异。要深层不可变，请用不可变集合（`List`、`Vector`、`Map`）。
2. **case class 中的 `var`。** 你*可以*写 `case class Foo(var x: Int)`，但强烈不建议——这会破坏 `equals`、`hashCode` 与 `copy` 的前提。优先使用 `val` 与 `copy`。
3. **`lazy val` 仍然是 `val`。** 一旦初始化，`lazy val` 不可重新赋值。但初始化被推迟且至多发生一次——这是带延迟求值的不可变性，而非可变性。
4. **`val` 上的 `final` 有时是冗余的。** 在 `final class` 中，所有成员实际上都是 final。在非 final 类中，把 `val` 标记为 `final` 可阻止子类覆盖——有用但常被遗忘。
5. **不可变集合并非零成本。** 不可变数据结构使用结构共享（持久化数据结构），效率高但并非免费。对有数百万次更新的热点路径，可考虑 `ArraySeq` 或受控作用域内的局部 `Array`。
6. **`sealed` ≠ `final`。** `sealed trait` 可以在同一文件内被扩展（从而启用穷尽匹配）。`final class` 则完全不可扩展。二者用途不同。

## 入门心智模型

把 Scala 的不可变性视为**层层防御**：

- **`val`** = "这个名字永远指向同一个东西"（绑定层面）
- **`final`** = "子类不能改变它"（层级层面）
- **`sealed`** = "只有这个文件能新增变体"（扩展层面）
- **不可变集合** = "内容也不会变"（数据层面）

Python 的 `Final` 最接近 Scala 的 `val` + `final`，但 Python 只通过类型检查器强制（运行时忽略）。Scala 在编译器层面强制全部——离开反射或 `unsafe`，无法绕过 `val`。

## 示例 A —— 不可变配置

```scala
final case class DbConfig(
  host: String, // 默认为 val —— 不可重新赋值
  port: Int,
  maxConnections: Int
)
val config = DbConfig("localhost", 5432, 10)
// config.host = "remote" // 编译错误：reassignment to val
// config = DbConfig("remote", 5432, 10) // 编译错误：reassignment to val
val updated = config.copy(host = "remote") // 函数式更新——新实例
```

## 示例 B —— 带 final 分支的 sealed 层级

```scala
sealed trait Permission
final case class Read(resource: String) extends Permission
final case class Write(resource: String) extends Permission
final case object Admin extends Permission
// class SuperAdmin extends Permission // 编译错误：sealed，此处不可扩展
def describe(p: Permission): String = p match
  case Read(r)  => s"read $r"
  case Write(r) => s"write $r"
  case Admin    => "full access"
// 若缺少分支，编译器会给出警告
```

## 常见类型检查器报错及读法

### `Reassignment to val`

```
-- [E052] Type Error:
1 | x = 43
  | ^^
  | Reassignment to val x
```

**含义：** 你试图重新赋值一个 `val`。若确实需要变异，请用 `var`；或用一个不同名字创建新绑定。

### `Cannot extend final class`

```
-- [E093] Type Error:
1 | class Sub extends FinalClass
  | ^^^^^^^^^^
  | class FinalClass cannot be extended
```

**含义：** 该类被标记为 `final`。若需扩展，请移除 `final`（或改用组合而非继承）。

### `Cannot override final member`

```
-- [E164] Type Error:
2 | override def core: Int = 0
  | ^^^^
  | Cannot override final member core in class Base
```

**含义：** 该成员在父类中是 `final` 的。你无法在子类中改变其实现。

## 用例交叉引用

- 见 [非法状态不可表示](../usecases/invalid-states.md)：不可变值防止状态腐化；`sealed` 启用穷尽匹配。
- 见 [领域建模](../usecases/domain-modeling.md)：不可变 case class 安全地建模领域实体。
- 见 [封装](../usecases/encapsulation.md)：`final` + `private` + `val` 构成纵深防御式封装。

# 引用

- [Scala 3 Reference — Final](https://docs.scala-lang.org/scala3/reference/other-new-features/final.html)
- [Scala 3 Book — Variables and Data Types](https://docs.scala-lang.org/scala3/book/taste-vars-data-types.html)
- [Scala 3 Reference — Sealed Classes](https://docs.scala-lang.org/scala3/reference/other-new-features/sealed-classes.html)
