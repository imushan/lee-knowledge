---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T39-notation-attributes.md
title: 注解与编译器指令 (Annotations)
description: Scala 注解是附加在定义上的元数据标记，可在编译期强制约束、优化生成代码或重命名字节码，如 @tailrec、@inline、@targetName
  等。
tags:
- Scala 3
- vibe-types
- T39
- 注解
- annotation
- '@tailrec'
- '@inline'
- '@targetName'
- 编译器指令
timestamp: '2026-06-24T12:06:52Z'
---

# 注解与编译器指令 (Annotations)

> **引入版本：** Scala 2（大多数注解）；Scala 3.0 新增 `@targetName`、`@experimental`；Scala 3.3 稳定 `@experimental`

## 简介

Scala 注解是附加在定义上、影响编译器行为、运行时语义或工具的元数据标记。与 Rust 属性（`#[inline]`、`#[must_use]`，它们是语言语法的核心部分）不同，Scala 注解在语法上是统一的（`@name` 或 `@name(args)`），可在编译期处理、保留在字节码中或两者兼有。它们充当**编译器指令**——修改编译器如何优化、检查或命名生成代码的指令。

Scala 3 继承了 Scala 2 的大多数注解并新增了若干。注解系统还与 Java 注解互操作，使 JVM 互操作变得直接。

## 可表达的约束

**注解约束或指导编译器对特定定义的行为：要求尾调用优化、强制内联、在字节码中重命名、标记为弃用或用实验性标志门控。编译器要么在编译期强制约束（如 `@tailrec` 在非尾位置递归时失败），要么发出修改后的字节码/元数据。**

## 最小示例

```scala
import scala.annotation.*

// @tailrec —— 编译器验证尾递归
@tailrec
def factorial(n: Long, acc: Long = 1): Long =
  if n <= 1 then acc else factorial(n - 1, n * acc)

// @inline —— 在调用点内联方法体的提示
@inline def square(x: Int): Int = x * x

// @targetName —— 设置 JVM 字节码名（用于运算符互操作）
extension (x: Int)
  @targetName("plus_mod")
  def +%(y: Int): Int = (x + y) % 100

// @deprecated —— 用消息和起始版本警告调用者
@deprecated("use newMethod instead", since = "2.0")
def oldMethod(): Unit = ()

// @main —— 标记入口点（Scala 3）
@main def run(): Unit = println("Hello!")
```

## 关键注解参考

| 注解 | 效果 | 是否编译期检查 |
|------------|--------|---------------------|
| `@tailrec` | 验证被注解方法是尾递归的；否则编译错误 | 是 |
| `@inline` | 请求编译器/JIT 在调用点内联方法体 | 仅提示 |
| `@targetName(name)` | 设置定义的 JVM 级名字；启用符号运算符名同时保留可读字节码名 | 是（名字冲突检查） |
| `@deprecated(msg, since)` | 引用该定义时发出弃用警告 | 是（警告） |
| `@experimental` | 标记定义为实验性；使用它需要 `-language:experimental` 或调用点也标 `@experimental` | 是 |
| `@main` | 生成带参数解析的程序入口点 | 是 |
| `@throws(classOf[E])` | 为 Java 互操作声明受检异常 | 仅元数据 |
| `@unchecked` | 抑制模式匹配的穷尽性警告 | 是（抑制） |
| `@switch` | 验证 match 编译为 JVM `tableswitch`/`lookupswitch`；否则错误 | 是 |

## 与其他特性的交互

| 特性 | 组合方式 |
|---------|-----------------|
| **编译期操作**（见 [compile-time-ops](compile-time-ops.md)） | `@inline` 与 `@tailrec` 补充 `inline def`（后者保证内联）。`inline def` 总是被内联；`@inline` 是对非 inline 方法的尽力提示。 |
| **宏 / 元编程**（见 [macros-metaprogramming](macros-metaprogramming.md)） | 宏注解（Scala 3 实验性）在编译期处理自定义注解以生成代码。`@experimental` 门控此类不稳定 API 的访问。 |
| **变更 / 弃用特性**（见 [changed-dropped](changed-dropped.md)） | `@deprecated` 是特性在 Scala 版本间变化时的标准迁移工具。`@targetName` 帮助在重命名时维护二进制兼容。 |
| **扩展方法**（见 [extension-methods](extension-methods.md)） | `@targetName` 对定义符号运算符的扩展方法尤其有用，确保字节码与 Java 互操作中有可读名。 |

## 注意事项与局限

1. **`@tailrec` 只检查自递归。** 两个方法间的相互递归不被 `@tailrec` 验证。只有对同一方法的直接尾调用才算数。
2. **`@inline` 不保证。** 与 `inline def`（Scala 3 编译器总是内联）不同，`@inline` 仅仅是提示。JIT 可能忽略它。需要内联必须发生时请用 `inline def`。
3. **`@switch` 限制。** match 必须只使用字面常量、枚举或 `final val` 常量。卫语句、提取器与类型模式会阻止 tableswitch 生成。
4. **`@experimental` 传播。** 使用 `@experimental` 定义要求调用点也标 `@experimental`，或整个编译单元通过 `-language:experimental` 加入。这可能在整个代码库中级联。
5. **Java 注解互操作。** 并非所有 Java 注解保留策略都受支持。`SOURCE` 保留的注解在到达 Scala 编译器阶段前被丢弃。`RUNTIME` 保留的注解保留在字节码中并可通过反射访问。
6. **`@unchecked` 隐藏真实 bug。** 用 `(expr: @unchecked) match { ... }` 抑制穷尽性警告可能掩盖真正缺失的分支。请谨慎使用并记录为何认为匹配是完整的。

## 入门心智模型

把注解视为贴在代码上的**便利贴**。每张便利贴是对编译器的指令："检查这是尾递归"、"尝试内联这个"、"警告任何使用它的人"。编译器在编译期阅读便利贴，要么遵循指令，要么在无法做到时报怨。

## 示例 A —— 用 `@targetName` 安全命名运算符

```scala
import scala.annotation.targetName

case class Vec2(x: Double, y: Double):
  @targetName("add")
  def +(other: Vec2): Vec2 = Vec2(x + other.x, y + other.y)
  @targetName("scalarMultiply")
  def *(scalar: Double): Vec2 = Vec2(x * scalar, y * scalar)

// Scala 看到：Vec2(1, 2) + Vec2(3, 4)
// Java 看到：vec.add(other) —— 可读的互操作名
```

## 示例 B —— 用 `@switch` 做性能关键匹配

```scala
import scala.annotation.switch

def category(c: Char): String = (c: @switch) match
  case 'a' | 'e' | 'i' | 'o' | 'u' => "vowel"
  case ' ' | '\t' | '\n'           => "whitespace"
  case _                           => "other"
// 编译为 JVM lookupswitch——O(1) 分派
```

## 用例交叉引用

- 见 [编译期](../usecases/compile-time.md)：`@tailrec`、`@switch`、`@inline` 等注解对生成代码质量强制编译期保证。

# 引用

- [Scala 3 Reference — @targetName](https://docs.scala-lang.org/scala3/reference/other-new-features/targetName.html)
- [Scala 3 Reference — @main Methods](https://docs.scala-lang.org/scala3/reference/changed-features/main-functions.html)
- [Scala 3 Reference — @experimental](https://docs.scala-lang.org/scala3/reference/other-new-features/experimental-defs.html)
- [Scala Standard Library — scala.annotation](https://www.scala-lang.org/api/3.x/scala/annotation.html)
