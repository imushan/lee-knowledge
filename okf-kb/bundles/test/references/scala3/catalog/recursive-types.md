---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T61-recursive-types.md
title: 递归类型
description: Scala 3 中通过 sealed trait/enum 层级定义自引用类型以建模树、表达式、流等递归与共递归数据结构的技术。
tags:
- 递归类型
- Recursive Type
- sealed enum
- ADT
- 共递归
- lazy val
- F-bounded
- T61
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:06:27Z'
---

# 递归类型

## 简介

递归类型是其定义引用自身的类型。在 Scala 3 中，主要机制是 **sealed trait/enum 层级**，其中一个或多个变体包含所属类型的字段。`enum Tree[A] { case Leaf(v: A); case Branch(l: Tree[A], r: Tree[A]) }` 定义了一棵二叉树，其中 `Branch` 含两个 `Tree` 值——类型出现在自身的定义中。

Scala 3 的 `enum` 语法提供简洁的递归 ADT 定义。sealed trait 提供相同能力并对表示有更多控制。由于 JVM 以垃圾回收管理内存，递归类型无需特殊间接（不像 Rust 要求 `Box`）——每个对象默认在引用后堆分配。

对于**共递归**（可能无限）结构，Scala 用 `lazy val` 延迟求值，从而支持无限流、循环图等余归纳模式。

> **Since:** Scala 2（sealed trait 层级）；Scala 3（`enum` 语法自 3.0 起）

## 可表达的约束

**编译器确保对递归类型的穷尽模式匹配，并通过类型系统追踪递归结构。每个变体的字段必须符合声明的类型，sealed 层级保证外部代码无法添加新变体。**

- sealed enum 是封闭的：编译器知晓所有 case 并要求穷尽匹配。
- 类型参数贯穿递归：`Tree[Int]` 确保每片叶子持有 `Int`。
- 递归泛型边界（F-bounded polymorphism）允许类型在自身边界中引用自身。

## 最小示例

```scala
enum Tree[+A]:
  case Leaf(value: A)
  case Branch(left: Tree[A], right: Tree[A])

import Tree.*

def depth[A](t: Tree[A]): Int = t match
  case Leaf(_)         => 0
  case Branch(l, r)    => 1 + math.max(depth(l), depth(r))

val tree = Branch(Leaf(1), Branch(Leaf(2), Leaf(3)))
println(depth(tree)) // 2
```

## 与其他特性的交互

| 特性 | 组合方式 |
|------|----------|
| **ADT**（见 [algebraic-data-types](algebraic-data-types.md)） | 递归类型即递归 ADT。sealed enum 层级在递归定义中结合了 sum 类型（变体）与 product 类型（字段）。 |
| **型变**（见 [variance-subtyping](variance-subtyping.md)） | 协变递归类型（`Tree[+A]`）允许在期望 `Tree[Any]` 处使用 `Tree[Int]`；型变标注贯穿递归结构传播。 |
| **模式匹配**（见 [type-narrowing](type-narrowing.md)） | 编译器确保对所有递归变体的穷尽匹配；嵌套模式可在单次 match 中解构递归结构。 |
| **类型别名**（见 [type-aliases](type-aliases.md)） | 递归类型别名（`type Stream[A] = () => (A, Stream[A])`）定义余归纳类型；Scala 3 允许递归 opaque 类型别名。 |
| **派生**（见 [derivation](derivation.md)） | 递归 enum 上的 `derives` 子句生成贯穿结构递归的类型类实例（如 `derives Codec` 用于树的 JSON 序列化）。 |

## 注意事项与局限

1. **深递归栈溢出。** 深结构上的递归函数可能爆栈。对非常深的树，使用尾递归方法（带 `@tailrec`）、trampolining 或转为迭代算法。
2. **无内置结构递归检查。** 不同于 Lean 或 Agda，Scala 不验证递归函数终止；递归类型上的无限循环能无警告编译。
3. **lazy val 开销。** 使用 `lazy val` 的共递归结构在首次访问时有同步开销（JVM 须检查初始化）。对高吞吐惰性流，可考虑标准库的 `LazyList`。
4. **F-bounded 复杂度。** 形如 `trait Comparable[A <: Comparable[A]]` 的递归边界虽强大，但产生难以阅读的复杂类型，并可能导致令人困惑的错误信息。
5. **无匿名递归类型。** 无法写出内联的递归类型表达式；每个递归类型必须声明为具名的 `enum`、`sealed trait` 或类型别名。

## 新手心智模型

把递归类型想成**俄罗斯套娃**（matryoshka）。一棵 `Tree` 要么是 `Leaf`（最小的娃娃，含一个值），要么是 `Branch`（一个里面装着两个更小娃娃的娃娃，每个本身又是一棵 `Tree`）。定义自引用——树由树构成——但每棵具体的树都是有限的（嵌套最终到达叶子）。

## 示例 A：递归表达式求值器

```scala
enum Expr:
  case Num(value: Double)
  case Add(left: Expr, right: Expr)
  case Mul(left: Expr, right: Expr)
  case Neg(inner: Expr)

import Expr.*

def eval(e: Expr): Double = e match
  case Num(v)   => v
  case Add(l, r) => eval(l) + eval(r)
  case Mul(l, r) => eval(l) * eval(r)
  case Neg(i)   => -eval(i)

val expr = Add(Num(1), Mul(Num(2), Neg(Num(3))))
println(eval(expr)) // -5.0
```

## 示例 B：用 lazy val 构造共递归无限流

```scala
class Stream[+A](val head: A, next: => Stream[A]):
  lazy val tail: Stream[A] = next
  def take(n: Int): List[A] =
    if n <= 0 then Nil
    else head :: tail.take(n - 1)

def nats(from: Int): Stream[Int] =
  new Stream(from, nats(from + 1))

val naturals = nats(0)
println(naturals.take(5)) // List(0, 1, 2, 3, 4)
// 流是无限的——仅按需求值
```

## 用例交叉引用

- sealed 递归类型确保所有结构变体都被处理，使不完整处理成为编译错误——见 [invalid-states](../usecases/invalid-states.md)。
- sealed 递归层级阻止外部代码添加非法变体——见 [encapsulation](../usecases/encapsulation.md)。
- 递归类型可建模状态机，迁移产生同类型的新状态——见 [state-machines](../usecases/state-machines.md)。

# 引用

- [Scala 3 参考 — Enumerations](https://docs.scala-lang.org/scala3/reference/enums/enums.html)
- [Scala 3 参考 — Algebraic Data Types](https://docs.scala-lang.org/scala3/reference/enums/adts.html)
- [Scala API — LazyList](https://scala-lang.org/api/3.x/scala/collection/immutable/LazyList.html)
- Martin Odersky，《Programming in Scala》第 15 章 "Case Classes and Pattern Matching"
