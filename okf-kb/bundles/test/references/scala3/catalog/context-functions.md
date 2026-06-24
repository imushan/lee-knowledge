---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T42-context-functions.md
title: 上下文函数与 Context Bounds
description: 'Scala 3 中抽象上下文依赖的两种机制：上下文函数类型 T ?=> U 将隐式参数提升为一等类型，context bound [T:
  Ord] 简化类型类证据声明。'
tags:
- 上下文函数
- Context Bounds
- Given
- Using
- 隐式参数
- T42
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:06:49Z'
---

# 上下文函数（`T ?=> U`）与 Context Bounds（`F : Monad`）

> **引入版本：** Scala 3.0 | **最新变更：** Scala 3.6（命名 context bound `as`、聚合 bound `{Ord, Show}`、抽象类型成员与多态函数上的 context bound）

## 简介

上下文函数与 context bounds 是 Scala 3 中抽象上下文依赖的两种密切相关机制。**上下文函数类型** `T ?=> U` 描述一个接受隐式（given）参数 `T` 并产生 `U` 的函数；该参数由编译器从外围作用域自动供给。**Context bound** `[T: Ord]` 是声明一个应用于类型参数的类型类的 `using` 参数的简写。二者结合，使能力需求在类型中显式可见，同时保持调用点简洁：上下文函数把"需要一个 given `T`"变成一等类型，context bound 把"需要 `Ord[T]` 证据"变成类型参数上的轻量注解。

## 可表达的约束

**上下文函数允许将上下文依赖抽象为类型，使"作用域中需要 `T`"成为函数类型签名的一部分，而非不可见的管道。** **Context bounds 允许在类型参数上直接声明"此类型参数必须有关联的类型类实例"，减少样板。** 二者组合以可组合、零开销的方式编码能力需求——从执行上下文到构建器作用域再到类型类证据。

## 最小示例

```scala
// --- 上下文函数 ---
import scala.concurrent.ExecutionContext

type Executable[T] = ExecutionContext ?=> T

def f(x: Int): Executable[Int] =
  val ec = summon[ExecutionContext]
  x + 1  // ExecutionContext 在函数体内隐式可用

given ec: ExecutionContext = ExecutionContext.global
val result: Int = f(2)  // ec 被自动供给

// --- Context bounds ---
trait Ord[T]:
  def compare(x: T, y: T): Int

def maximum[T: Ord](xs: List[T]): T =
  xs.reduceLeft((a, b) =>
    if summon[Ord[T]].compare(a, b) < 0 then b else a)

// 命名 context bound（Scala 3.6+）：
trait Monoid[A]:
  def unit: A
  extension (x: A) def combine(y: A): A

def reduce[A: Monoid as m](xs: List[A]): A =
  xs.foldLeft(m.unit)(_ `combine` _)
```

## 与其他特性的交互

- **Given 与 using 子句。** Context bounds 脱糖为 using 子句，上下文函数应用依赖作用域中的 given 实例。它们是需求侧，given 是供给侧。参见用例 [编译期计算](../usecases/compile-time.md)。
- **构建器模式（上下文函数）。** 上下文函数支持 DSL 式构建器模式：外围作用域将可变构建器作为 given 提供。经典示例是 HTML 表格构建器，`table { row { cell("x") } }` 通过嵌套上下文函数线程化 `Table` 和 `Row` 实例编译通过。
- **后置条件（上下文函数）。** 与 opaque type 别名和扩展方法结合，上下文函数可实现零开销后置条件检查：`List(1,2,3).sum.ensuring(result == 6)`，其中 `result` 从 `WrappedResult[T] ?=> Boolean` 上下文函数解析。
- **多态函数类型。** Context bound 可用于多态函数类型（Scala 3.6+）：`[X: Ord] => (X, X) => Boolean` 脱糖为 `[X] => (X, X) => Ord[X] ?=> Boolean`。参见用例 [效果追踪](../usecases/effect-tracking.md)。
- **聚合 context bound。** 多个 bound 写在花括号内：`[X: {Ord, Show}]`。命名变体：`[X: {Ord as ord, Show as show}]`。
- **抽象类型成员。** 抽象类型成员上的 context bound（Scala 3.6+）展开为 deferred given：`type Element: Ord` 变为 `type Element` 加 `given Ord[Element] = deferred`。
- **自动包装。** 若表达式 `E` 期望类型为上下文函数类型 `T ?=> U` 但本身不是上下文函数字面量，编译器会将其改写为 `(x: T) ?=> E`，使 `x` 作为 given 在 `E` 中可用。
- **联合/交集类型。** 上下文函数参数可以是交集类型以同时要求多种能力：`(Logging & Tracing) ?=> Result`。参见用例 [非法状态](../usecases/invalid-states.md)。

## 注意事项与局限

1. **上下文函数不是普通函数。** `T ?=> U` 与 `T => U` 不同。不能在期望普通函数处使用上下文函数，反之亦然，除非显式转换。
2. **隐式歧义。** 若作用域中有多个与上下文函数参数类型匹配的 given，编译器报歧义。使用不同的 opaque type 或 newtype 避免冲突（如后置条件示例所示）。
3. **命名 context bound 需 Scala 3.6+。** 为见证命名的 `as` 语法（`[T: Ord as ord]`）和聚合 bound（`[T: {Ord, Show}]`）在 Scala 3.6 前不可用。旧语法 `[T: Ord : Show]` 仍可用但将被弃用。
4. **生成参数的位置。** 由 context bound 生成的 using 子句遵循特定放置规则：若 bound 名称被后续参数子句引用，using 子句插入到该子句之前；否则追加或合并到已有 using 子句。
5. **上下文函数开销。** 虽概念上零开销，但每个上下文函数类型在类型层面创建独立的 `ContextFunctionN` trait 实例。深层嵌套的上下文函数可能产生冗长的推断类型。
6. **调试。** 当未找到上下文函数参数时，错误消息为"no given instance of type T was found"，若未意识到涉及上下文函数可能令人困惑。理解自动包装规则是诊断此类错误的关键。
7. **Deferred given。** 抽象类型成员上的 context bound 产生 `given T = deferred`，必须在具体子类中实现。忘记提供实现会在子类（而非抽象定义处）报编译错误。

## 用例交叉引用

- 交集类型在单个上下文函数参数中组合多种能力需求。参见用例 [非法状态](../usecases/invalid-states.md)。
- 类型 Lambda 将多参数类型构造器适配为 context bound 可用的形状。参见 [type-lambdas](type-lambdas.md)。
- Match type 可作为 context bound 方法的返回类型实现条件返回。参见 [match-types](match-types.md)。
- 多态函数类型与 context bound 组合，表达多态、依赖上下文的值。参见用例 [效果追踪](../usecases/effect-tracking.md)。
- Given 与 using 子句是 context bound 和上下文函数所表达需求的供给侧对应物。参见用例 [编译期计算](../usecases/compile-time.md)。

# 引用

- 原始来源：[T42-context-functions.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T42-context-functions.md)
