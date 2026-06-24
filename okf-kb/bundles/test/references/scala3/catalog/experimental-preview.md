---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T43-experimental-preview.md
title: 实验与预览特性：命名类型参数、into、模块化
description: Scala 3 中三个前向特性：命名类型参数、into 类型（控制隐式转换位置）、模块化改进（tracked 参数、应用构造类型、精炼类型父类）。
tags:
- 命名类型参数
- into
- tracked
- 模块化
- 实验特性
- 预览特性
- T43
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:06:49Z'
---

# 实验与预览特性：命名类型参数、`into`、模块化

> **状态：** 混合 — 命名类型参数：3.0 起实验 | `into`：3.8 起预览 | 模块化：实验性

## 简介

本文档涵盖三个处于不同成熟阶段的前向 Scala 3 特性。**命名类型参数**（实验性）允许调用方按名称而非位置绑定类型参数，使不需要的参数可被推断。**`into` 类型**（预览，Scala 3.8 起）提供对使用 `scala.Conversion` 的隐式转换发生位置的细粒度控制，无需全局 `import scala.language.implicitConversions`。**模块化改进**（实验性，`-source:future -language:experimental.modularity`）引入 `tracked` 类参数、应用构造类型和精炼类型父类，使 Scala 中基于依赖类型的模块组合像 SML functor 一样自然——无需声名狼藉的 `Aux` 模式。

## 可表达的约束

**命名类型参数允许选择性指定编译器无法推断的类型参数；`into` 将隐式转换限制到特定参数位置而非全局启用；`tracked` 参数在类构造器中保留依赖类型信息，实现基于抽象类型成员的健全模块组合。**

## 最小示例

```scala
//> using option "-preview"
// `into` 是预览特性，本文件通过 `-preview` 选择启用。
import scala.language.experimental.namedTypeArguments
import scala.language.experimental.modularity
import scala.language.implicitConversions
import scala.Conversion.into

// --- 命名类型参数 ---
def construct[Elem, Coll[_]](xs: Elem*): Coll[Elem] = ???

// --- into（预览，Scala 3.8+）---
// 作为类型构造器：仅在被标记的位置允许转换
def prepend(elems: into[IterableOnce[Int]]): List[Int] = ???
given Conversion[Array[Int], IterableOnce[Int]] = _.toList

// 作为修饰符：该类型的所有参数都允许转换
into trait Modifier
given Conversion[String, Modifier] = ???
def f(m: Modifier): Unit = ()

// --- tracked 参数（模块化）---
trait Ordering:
  type T
  def compare(t1: T, t2: T): Int

class SetFunctor(tracked val ord: Ordering):
  type Set = List[ord.T]
  def empty: Set = Nil
  extension (s: Set)
    def add(x: ord.T): Set = x :: s

object intOrdering extends Ordering:
  type T = Int
  def compare(t1: Int, t2: Int): Int = t1 - t2

@main def demo(): Unit =
  val xs1 = construct[Coll = List, Elem = Int](1, 2, 3) // 全命名，顺序任意
  val xs2 = construct[Coll = List](1, 2, 3)             // Elem 被推断
  val ys = prepend(Array(2, 3))                         // 应用转换，无需 language import
  f("hello")                                           // OK，Modifier 声明为 `into`
  val IntSet = SetFunctor(intOrdering)
  import IntSet.add // 将扩展方法引入作用域
  val s = IntSet.empty.add(1).add(2)                    // 元素类型 Int 被保留
```

## 与其他特性的交互

- **命名类型参数与类型推断。** 命名类型参数与局部类型推断组合：未指定的参数照常推断。所有参数必须要么全命名要么全位置——不能混用。这对有多个类型参数但只有一两个歧义的方法尤其有用。
- **`into` 与 `Conversion`。** `into[T]` 在 `Conversion` 伴生中定义为 `opaque type into[T] >: T = T`。它与隐式搜索交互：仅当期望类型是合法的转换目标类型（`into` 包装的类型、`into` 修饰的 trait 或其类型别名）时，编译器才在不要求 language import 的情况下插入 `Conversion`。带 `into` 的变长参数允许每个元素有不同的转换。
- **`into` 在方法体内的解包。** 方法内部，参数类型上的 `into` 包装从局部类型中擦除，因此 `elems: into[IterableOnce[A]]` 在体内被视为 `elems: IterableOnce[A]`——无需 `.underlying` 调用。
- **`tracked` 与依赖类型。** 类 `F` 中的 `tracked val` 参数 `x: C` 将构造器返回类型精化为 `F { val x: x1.type }`，保留路径依赖类型信息。当参数类型有抽象类型成员时自动推断。参见用例 [效果追踪](../usecases/effect-tracking.md)。
- **应用构造类型。** 启用模块化后，`C(42)` 可作为类型使用，对 `class C(tracked val v: Any)` 展开为 `C { val v: 42 }`，为精炼类型提供简洁语法。
- **精炼类型父类。** 类现在可以直接继承精炼类型；精炼被提升为合成成员。这允许将模块签名表达为带精炼的类型别名，然后作为类实现。
- **导出放宽。** 类型成员导出不再是 `final`，允许多个 trait 导出同一类型成员然后混在一起——对聚合类类型类 given 至关重要。

## 注意事项与局限

1. **命名类型参数：不能混用。** 不能在同一应用中混用位置和命名类型参数，只能全命名或全位置。
2. **`into` 子类。** `into` 声明类型的子类**不是**自动合法的转换目标。若 `class C extends T` 且 `T` 是 `into`，`C` 类型的参数仍需 language import 才能转换。
3. **`into` 与类型参数实例化。** 未显式实例化为 `into` 类型的类型参数不算合法转换目标。例如 `List("a", "b")` 中元素类型被推断（非显式 `into[Keyword]`）时，不允许对元素转换。
4. **两种 `into` 方案互补。** 作为类型构造器的 `into` 提供按参数控制（库作者包装特定参数）；作为修饰符的 `into` 提供按类型控制（该类型的所有参数接受转换）。使用过多 `into` 修饰符会削弱 language import 旨在提供的保护。
5. **`tracked` 改变推断类型。** 将 case class 参数设为 `tracked` 可能在期望更宽类型处推断出单例类型，可能破坏向可变变量赋值（如 `var x = Foo(1); x = Foo(2)` 在 `x` 被推断为 `Foo { val v: 1 }` 时失败）。
6. **`tracked` 非默认。** 为向后兼容，`tracked` 不对所有 `val` 参数默认假定，仅在参数类型有抽象类型成员时推断。

## 用例交叉引用

- 依赖函数类型：`tracked` 参数将路径依赖类型引入类构造器。参见用例 [效果追踪](../usecases/effect-tracking.md)。
- 类型类模式：`tracked` 与模块化改进简化了带关联类型的类型类的 `Aux` 模式。参见用例 [编译期计算](../usecases/compile-time.md)。
- 上下文函数：`into` 参数与上下文函数类型组合，实现人体工学的 DSL 设计。参见用例 [状态机](../usecases/state-machines.md)。
- 模块组合：`SetFunctor` 式模式在 Scala 中替代 SML functor。参见用例 [可扩展性](../usecases/extensibility.md)。

# 引用

- 原始来源：[T43-experimental-preview.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T43-experimental-preview.md)
