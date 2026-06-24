---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T05-type-classes.md
title: 类型类（Given / Using / Given Import）
description: 通过 given 实例与 using 子句要求编译期类型证据并由编译器自动供给，构成 Scala 3 类型类分派的基础。
tags:
- T05
- Scala 3
- vibe-types
- 类型类
- given
- using
- 上下文抽象
- 实例解析
timestamp: '2026-06-24T12:04:48Z'
---

# 类型类（Given / Using / Given Import）

> **引入版本：** Scala 3.0 | **最新变更：** Scala 3.6（新的 given 语法 `[T] => ...`）

## 简介

given、using 子句与 given import 构成 Scala 3 重新设计的上下文抽象系统的核心，用三个分工明确的机制取代 Scala 2 的 `implicit` 关键字。**given 实例**（`given`）定义一个编译器可自动供给的类型的规范值；**using 子句**（`using`）声明一个由编译器从可用 given 填入的参数；**given import**（`import A.given`）控制哪些 given 实例被引入作用域，与常规 import 分离。三者共同为基于类型类的编程、依赖注入与能力传递提供有原则的框架。

## 可表达的约束

**given 与 using 子句让你要求"某类型满足某约束"的编译期证据，并由编译器自动供给该证据。** 这是 Scala 3 类型类分派的基础：声明类型必须具备的能力（using 子句）、定义具体类型如何满足能力（given 实例）、控制哪些证据可见（given import）。

## 最小示例

```scala
// 定义类型类
trait Ord[T]:
  def compare(x: T, y: T): Int

// 为 Int 提供证据
given intOrd: Ord[Int]:
  def compare(x: Int, y: Int) =
    if x < y then -1 else if x > y then +1 else 0

// 条件证据：当 T 是 Ord 时，List[T] 也是 Ord
given listOrd: [T: Ord] => Ord[List[T]]:
  def compare(xs: List[T], ys: List[T]): Int = (xs, ys) match
    case (Nil, Nil)         => 0
    case (Nil, _)           => -1
    case (_, Nil)           => +1
    case (x :: xs1, y :: ys1) =>
      val fst = summon[Ord[T]].compare(x, y)
      if fst != 0 then fst else compare(xs1, ys1)

// 通过 using 子句要求证据
def max[T](x: T, y: T)(using ord: Ord[T]): T =
  if ord.compare(x, y) < 0 then y else x

// 编译器自动供给证据
val m = max(2, 3) // intOrd 由编译器供给

// given import：选择性可见
object Instances:
  given intOrd: Ordering[Int] = Ordering.Int
  given ec: concurrent.ExecutionContext = ???
import Instances.{given Ordering[?]} // 仅导入 intOrd
```

## 与其他特性的交互

- **上下文边界。** 上下文边界 `[T: Ord]` 是 `using Ord[T]` 参数的语法糖。命名上下文边界（`[T: Ord as ord]`，Scala 3.6+）为证据命名。
- **context 函数。** context 函数类型 `T ?=> U` 抽象 using 参数的传递，使 given 在 lambda 体内可用。
- **联合 / 交叉类型。** 可为交叉类型定义 given 实例以要求组合证据（如 `given [T: Ord & Show] => ...`）。
- **match 类型。** given 实例可在结果类型中使用 match 类型，实现条件式类型类派生。
- **type lambda。** 当类型类期望 `F[_]` 而你有 `Either[E, A]` 时，type lambda `[A] =>> Either[E, A]` 调整形状以适配 given 定义。
- **匿名 given。** given 可匿名，编译器按类型合成名字。公开库应优先用具名实例以保证二进制兼容。
- **别名 given。** `given global: ExecutionContext = ForkJoinPool()` 将一个 lazy、线程安全的值定义为 given。
- **初始化。** 无条件无参 given 按需延迟初始化；条件 given（带类型或项参数）每次使用创建新实例。
- **summon。** `summon[T]` 取回作用域中类型 `T` 的 given 实例，定义为 `def summon[T](using x: T): x.type = x`。
- **按类型 import。** `import A.given TC` 仅导入符合类型 `TC` 的 given，提供精细控制。

## 注意事项与局限

1. **通配符 `*` 不导入 given。** 这是有意为之：`import A.*` 导入除 given 与扩展方法外的所有内容；必须用 `import A.given` 或 `import A.{given, *}` 才能包含它们。
2. **匿名 given 名字冲突。** 当类型"过于相似"时，编译器合成的匿名 given 名字可能冲突；公开 API 应使用具名 given。
3. **歧义。** 若作用域中存在多个同类型 given，编译器报告歧义错误。特异性规则（更具体的 given 优先）可解决部分情形，复杂层级可能需显式 `using` 参数。
4. **given 搜索作用域。** 编译器在当前作用域、import 及涉及类型的伴生对象（"隐式作用域"）中搜索 given；理解该作用域对调试 "no given instance found" 错误至关重要。
5. **从 implicit 迁移。** Scala 3.0 中 `given` import 也会将旧式 `implicit` 定义引入作用域；后续版本中用 `*` 导入旧 implicit 会产生弃用警告并最终报错。
6. **二进制兼容。** 在匿名与具名 given 之间切换是二进制不兼容变更；库应从一开始就使用具名 given。

## 推荐库

| 库 | 作用 | 链接 |
|---|---|---|
| cats | 标准类型类（Monad、Functor、Applicative、Traverse 等）及合法实例 | [typelevel.org/cats](https://typelevel.org/cats/) |
| shapeless-3 | 面向积/和形状的泛型编程；为任意元数进行类型类派生 | [github.com/typelevel/shapeless-3](https://github.com/typelevel/shapeless-3) |
| kittens | 为 case class 与 enum 自动派生 cats 类型类实例（Functor、Show、Eq 等） | [github.com/typelevel/kittens](https://github.com/typelevel/kittens) |

## 从 Lean 迁移

Scala 的 `given`/`using` 直接对应 Lean 的 `class`/`instance`。Lean 写 `class Ord (α : Type) where le : α → α → Bool` 与 `instance : Ord Nat where le := Nat.ble`，Scala 写 `trait Ord[A]: def le(a: A, b: A): Boolean` 与 `given Ord[Int] with def le(a: Int, b: Int) = a <= b`。两者都使用自动实例解析。Lean 的类型类还兼任依赖类型分派的机制——该角色在 Scala 中由 match 类型与 inline 承担。

## 用例交叉引用

- 可为交叉类型定义 given 实例，组合多个类型类约束，用于[防止非法状态](../usecases/invalid-states.md)。
- type lambda 为面向一元类型类的 given 定义调整多参数类型，用于[领域建模](../usecases/domain-modeling.md)。
- match 类型支持按被审视类型进行条件式 given 派生。
- 多态函数类型可作为多态能力值的 given 实例，用于[效果追踪](../usecases/effect-tracking.md)。
- 上下文边界与 context 函数直接建立在 given 与 using 之上，用于[状态机](../usecases/state-machines.md)。

# 引用

- [T05-type-classes.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T05-type-classes.md)
