---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T52-literal-types.md
title: 字面量类型（单例类型）
description: Scala 3 中每个字面量值都有单例类型，将值约束为确切的一个字面量，是 const generics、编译期运算和 match types
  的基础。
tags:
- 字面量类型
- 单例类型
- Singleton
- 编译期常量
- T52
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:06:50Z'
---

# 字面量类型（单例类型，Singleton Types）

> **引入版本：** Scala 3.0（一等字面量类型）| Scala 2.13 曾有 `-Yliteral-types` 标志

## 简介

在 Scala 3 中，每个字面量值都有一个**单例类型**——只被该值一个值居住的类型。整数 `42` 的类型是 `42`，字符串 `"hello"` 的类型是 `"hello"`，`true` 的类型是 `true`。这些单例类型是其宽化形式的真子类型：`42 <: Int`、`"hello" <: String`、`true <: Boolean`。

单例类型是 const generics、编译期运算和 match types 在 Scala 3 中得以实现的基础。其他语言额外附加独立的"字面量类型"特性，而 Scala 3 将其直接集成到子类型格中。

## 可表达的约束

**单例类型将值约束为确切的一个字面量。编译器拒绝该位置的任何其他值，不同字面量产生不同且互不兼容的类型。**

- `val x: 42 = 42` 被接受；`val x: 42 = 43` 被拒绝。
- 类型为 `"GET" | "POST"` 的函数参数只接受这两个字符串值。
- 以单例为边界的类型参数（`N <: Int & Singleton`）在泛型代码中保留字面量。

## 最小示例

```scala
val theAnswer: 42 = 42       // OK — 42 的类型是 42
// val wrong: 42 = 43        // 错误：Found (43 : Int), Required (42 : Int)
val greeting: "hello" = "hello"  // OK
val flag: true = true        // OK

// 单例类型是其宽化形式的子类型
val n: Int = theAnswer       // OK — 42 <: Int（宽化）
// val back: 42 = n          // 错误 — Int 不是 <: 42
```

## 与其他特性的交互

- **Const generics**：单例类型是 `Vec[3]` 和 `Matrix[2, 3]` 背后的机制——以 `<: Int` 为边界的类型参数携带字面量类型。
- **Match types**：match type 对单例类型模式匹配实现类型级条件：`type IsZero[N <: Int] = N match { case 0 => true; case _ => false }`。参见 [match-types](match-types.md)。
- **编译期运算**：`compiletime.ops.int.*` 对单例 `Int` 类型执行算术。`constValue[T]` 在运行时提取单例类型的值。
- **联合类型**：单例的联合创建闭合值集：`type Color = "red" | "green" | "blue"`，类似 Python 的 `Literal`。
- **Opaque types**：将单例类型与 opaque type 结合，实现携带编译期信息的零开销包装。

## 注意事项与局限

1. **推断默认宽化。** `val x = 42` 推断 `x: Int` 而非 `x: 42`。要保留单例类型，需显式注解（`val x: 42 = 42`）或在泛型上下文中使用 `Singleton` 边界。
2. **`Singleton` 上界。** 为防止泛型代码中宽化，给类型参数加边界：`def f[N <: Int & Singleton](n: N)`。没有 `Singleton`，编译器可能将 `N` 宽化为 `Int` 而丢失字面量。
3. **字面量类型覆盖基本字面量种类。** 单例类型存在于 `Int`、`Long`、`Float`、`Double`、`Char`、`Boolean` 和 `String`。（Scala 3 移除了 `'sym` 字面量语法，故没有 `Symbol` 字面量类型。）
4. **`constValue` 对宽化类型失败。** 若类型参数被推断为 `Int` 而非具体字面量，`constValue[N]` 不编译。确保调用方提供字面量类型。
5. **运行时值不能成为单例。** 无法取一个运行时 `Int` 并提升为单例类型。值必须是字面量或由其他编译期常量计算而来。
6. **模式匹配不自动收窄到单例。** `case 42 =>` 收窄到 `Int` 而非单例 `42`，除非 scrutinee 本身已是单例类型。

## 入门心智模型

把每个字面量想象成带着一张**就是值本身的姓名牌**。数字 `42` 带着一张写着"我确切是 42，别无其他"的牌。这张牌是一个类型，它装在更大的类别 `Int` 里——但它更具体。当你告诉编译器"这个变量持有 `42`"时，它无需运行代码就能拒绝 `43`。

## 示例 A — 单例联合作为闭合值集

```scala
type Direction = "north" | "south" | "east" | "west"

def move(dir: Direction): (Int, Int) = dir match
  case "north" => (0, 1)
  case "south" => (0, -1)
  case "east"  => (1, 0)
  case "west"  => (-1, 0)

move("north")  // OK — 返回 (0, 1)
// move("up")  // 错误：Found "up", Required "north" | "south" | "east" | "west"
```

## 示例 B — 用 Singleton 边界保留单例

```scala
import scala.compiletime.constValue

inline def sizeOf[N <: Int & Singleton]: Int = constValue[N]
val s = sizeOf[10]  // OK — 运行时返回 10
// sizeOf[Int]     // 错误 — Int 不是单例类型

// 没有 Singleton 边界，推断可能宽化：
def unsafe[N <: Int](n: N): Int = n       // N 可以是 Int — 单例丢失
def safe[N <: Int & Singleton](n: N): N = n  // N 必须是字面量
```

## 示例 C — 单例类型与 match types

```scala
type Parity[N <: Int] = N match
  case 0 => "even"
  case 1 => "odd"

// 结果类型本身是单例字符串类型
val check0: "even" = compiletime.constValue[Parity[0]]
val check1: "odd"  = compiletime.constValue[Parity[1]]
```

## 常见类型检查器错误及解读

### `Found: (43 : Int), Required: (42 : Int)`

**含义：** 你把不同字面量赋给了单例类型的绑定。编译器同时显示找到的和要求的字面量类型。
**修复：** 使用正确字面量，或若不需要单例约束则将注解宽化为 `Int`。

### `Cannot reduce constValue[Int]`

**含义：** `constValue` 要求具体单例类型，却收到 `Int` 等宽化类型。通过在边界加 `& Singleton` 确保类型参数携带字面量类型。

## 用例交叉引用

- 在编译期将值限制到已知集合。参见用例 [非法状态](../usecases/invalid-states.md)。
- 将领域特定的值约束建模为类型。参见用例 [领域建模](../usecases/domain-modeling.md)。
- 对类型级字面量进行编译期计算。参见用例 [编译期计算](../usecases/compile-time.md)。
- 类型级算术建立在单例 Int 类型之上。参见用例 [类型算术](../usecases/type-arithmetic.md)。

# 引用

- 原始来源：[T52-literal-types.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T52-literal-types.md)
- [Scala 3 Reference — Literal Types](https://docs.scala-lang.org/scala3/reference/new-types/literal-types.html)
- [Scala 3 Reference — Singleton Types](https://docs.scala-lang.org/scala3/reference/new-types/literal-types.html#singleton-types)
- [Scala 3 Reference — Match Types](https://docs.scala-lang.org/scala3/reference/new-types/match-types.html)
- [scala.compiletime API](https://scala-lang.org/api/3.x/scala/compiletime.html)
- [SIP-23 — Literal-based singleton types](https://docs.scala-lang.org/sips/42.type.html)
