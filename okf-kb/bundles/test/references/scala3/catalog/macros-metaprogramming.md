---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T17-macros-metaprogramming.md
title: 宏：quotes 与 splices
description: 通过 quotes `'{ }` 与 splices `${ }` 构建类型安全、跨阶段卫生的编译期代码生成，支持 AST 检查、变换与自定义编译错误。
tags:
- T17
- Scala 3
- vibe-types
- 宏
- quotes
- splices
- 元编程
- Expr
- Type
- 多阶段编程
timestamp: '2026-06-24T12:06:11Z'
---

# 宏：quotes 与 splices

## 简介

Scala 3 宏建立在有原则的多阶段编程系统之上。**quotes** `'{ ... }` 延迟（分阶段）代码到未来编译阶段，产生类型为 `Expr[T]` 的值。**splices** `${ ... }` 提前一阶段求值代码，将结果 AST 插入外围 quote 或程序。宏是一个 `inline def`，其体含顶层 splice，调用一个单独编译的方法在编译期生成代码。该系统是静态类型、卫生且跨阶段安全的：`Expr[T]` 追踪表达式类型，`Type[T]` 跨阶段携带类型信息，`Quotes` 提供 quote 操作的上下文。

## 可表达的约束

**quotes 与 splices 启用完全类型安全的任意编译期代码生成。你可以通过 quote 模式匹配检查表达式结构、变换 AST、在调用点 summon 隐式、产生自定义编译错误并生成特化代码——同时编译器保证生成的代码良构且卫生。**

## 最小示例

### 基本宏（代码生成）

```scala
// 宏实现（必须先于使用编译）
import scala.quoted.*
def unrolledPowerCode(x: Expr[Double], n: Int)(using Quotes): Expr[Double] =
  if n == 0 then '{ 1.0 }
  else if n == 1 then x
  else '{ $x * ${ unrolledPowerCode(x, n - 1) } }

// 宏入口点
inline def power(x: Double, inline n: Int): Double =
  ${ powerCode('x, 'n) }

def powerCode(x: Expr[Double], n: Expr[Int])(using Quotes): Expr[Double] =
  unrolledPowerCode(x, n.valueOrAbort)
```

```scala ignore
// 使用（必须在不同于宏定义的编译单元中——
// 宏不能在定义它的同一源文件中被调用）
power(3.14, 3) // 展开为：3.14 * 3.14 * 3.14
```

### 将值提升进 quote

```scala
import scala.quoted.*
def liftExample(using Quotes): Expr[Int] =
  val expr2: Expr[Int] = Expr(1 + 1) // 将值 2 提升为 '{ 2 }
  // 与 '{ 1 + 1 } 对比，后者分阶段计算
  expr2
```

通过 `ToExpr` 自定义提升：

```scala
import scala.quoted.*
given OptionToExpr: [T: {Type, ToExpr}] => ToExpr[Option[T]]:
  def apply(opt: Option[T])(using Quotes): Expr[Option[T]] =
    opt match
      case Some(x) => '{ Some[T](${ Expr(x) }) }
      case None    => '{ None }
```

### 从 quote 提取值

```scala
import scala.quoted.*
def optimize(n: Expr[Int])(using Quotes): Expr[Int] =
  n match
    case Expr(0)  => '{ 0 }      // n 是已知常量 0
    case Expr(v)  => Expr(v * 2) // n 是已知常量，翻倍
    case _        => '{ $n * 2 } // 运行时——生成乘法
```

### quote 模式匹配（分析型宏）

```scala
import scala.quoted.*
// `power` 是前面定义的宏；其签名必须在作用域内才能在 quote 模式中匹配。
inline def power(x: Double, inline n: Int): Double = ${ powerCode('x, 'n) }
def powerCode(x: Expr[Double], n: Expr[Int])(using Quotes): Expr[Double] = x

def fusedPowCode(x: Expr[Double], n: Expr[Int])(using Quotes): Expr[Double] =
  x match
    case '{ power($y, $m) } =>       // 结构分解
      fusedPowCode(y, '{ $n * $m }) // 融合：(y^m)^n => y^(n*m)
    case _ =>
      '{ power($x, $n) }
```

### 模式中的类型变量

```scala
import scala.quoted.*
def fuseMapCode(x: Expr[List[Int]])(using Quotes): Expr[List[Int]] =
  x match
    case '{ ($ls: List[t]).map[u]($f).map[Int]($g) } =>
      '{ $ls.map($g.compose($f)) } // 融合连续的 map
    case _ => x
```

### 处理类型

```scala
import scala.quoted.*
def emptyOf[T: Type](using Quotes): Expr[Option[T]] =
  // 类型模式会精化 scrutinee 但不会精化结果类型 `T`，因此
  // 用 `asExprOf` 重新断言每个分支的表达式类型（见注意事项）。
  Type.of[T] match
    case '[String]   => '{ Some("") }.asExprOf[Option[T]]
    case '[Int]      => '{ Some(0) }.asExprOf[Option[T]]
    case '[List[t]]  => '{ Some(List.empty[t]) }.asExprOf[Option[T]]
    case _           => '{ None }
```

### 在宏中 summon 隐式

```scala
import scala.quoted.*
import scala.collection.immutable.{TreeSet, HashSet}
inline def setFor[T]: Set[T] =
  ${ setForExpr[T] }

def setForExpr[T: Type](using Quotes): Expr[Set[T]] =
  Expr.summon[Ordering[T]] match
    case Some(ord) => '{ new TreeSet[T]()($ord) }
    case _         => '{ new HashSet[T] }
```

## 与其他特性的交互

| 特性 | 交互 |
|------|------|
| **`inline`**（见 [compile-time-ops](compile-time-ops.md)） | 宏定义为含 `${ ... }` 体的 `inline def`。inline 机制是面向用户的入口；splice 对最终用户隐藏。 |
| **`transparent inline`** | transparent inline 宏可根据生成的代码特化返回类型，实现 whitebox 风格宏。 |
| **`Type[T]`** | 只要泛型类型 `T` 跨阶段使用就必需。编译器执行“类型愈合”自动插入 `Type` 见证。`Type[T <: AnyKind]` 支持高阶类型。 |
| **`Quotes`** | 每个 quote 需要 `Quotes` 上下文。每个 splice 向其体提供新鲜 `Quotes`。`Quotes` 也是反射 API 的入口。 |
| **反射 API** | `quotes.reflect` 暴露完整的带类型 AST，支持超出 quote 模式能力的低阶树检查与构造。 |
| **`ExprMap`** | 用于变换 `Expr` 所有子表达式的 trait，适用于自底向上或自顶向下的生成代码重写。 |
| **编译期操作**（见 [compile-time-ops](compile-time-ops.md)） | `compiletime.error` 可从宏实现中调用以产生自定义编译错误。`constValue` / `erasedValue` 在更简单的类型级计算上补充宏。 |
| **staging（`scala.quoted.staging`）** | 同样的 `Expr`/`Type`/`Quotes` 抽象通过 `staging.run` 支持运行时多阶段编程，以 `staging.Compiler` 为后端。 |
| **单独编译** | 宏实现方法必须先于调用点编译。当定义在同一项目内时，编译器自动检测并推迟编译使用尚未编译宏的文件。 |

## 注意事项与局限

- **单独编译要求。** 顶层 splice 中调用的方法必须已编译。宏定义与使用间的循环依赖导致编译失败。
- **层级一致性。** 局部变量只能在其定义的同一分阶段层级使用。层级 0 定义的变量不能不经提升出现在 quote（层级 1）中，层级 1 的变量不能出现在 splice（层级 0）中。
- **局部变量无跨阶段持久化。** 不能直接在 quote 中引用局部运行时变量。用 `Expr(value)` 提升或在正确层级定义时用 `'{ localVal }`。
- **作用域外逸。** 通过可变状态存储 `Expr` 并在其定义 splice 作用域外使用会导致运行时错误（用 `-Xcheck-macros` 检查）。每个 `Expr` 追踪其作用域。
- **`isInstanceOf[Expr[T]]` 不可靠。** 由于擦除，对 `Expr` 的运行时类型检查忽略类型参数。改用 `isExprOf[T]` 与 `asExprOf[T]`。
- **顶层 splice 限制。** 顶层 splice 必须包含对已编译静态方法的单个调用，参数为字面量、quoted 表达式、`Type.of` 调用或 `Quotes` 引用。顶层 splice 中不允许嵌套 splice。
- **quote 模式闭合性。** quote 模式中的 `${ }` 仅当被提取表达式闭合（不引用模式中绑定的变量）时匹配。用 HOAS 模式 `$f(y)` 捕获引用模式绑定变量的表达式。
- **类型变量约定。** quote 模式中，小写类型名自动被视为类型变量。用反引号引用同名既有类型。
- **`Expr` 是协变的。** 若 `B <: A` 则 `Expr[B]` 是 `Expr[A]` 的子类型。这可靠但意味着静态类型可能不如实际表达式类型精确。

## 推荐库

| 库 | 角色 | 链接 |
|----|------|------|
| **scalameta** | 语法树解析与变换；代码分析与生成工具的基础 | [scalameta.org](https://scalameta.org/) |
| **scalafix** | 基于语义分析的重写规则与 lint；自动化代码迁移 | [scalacenter.github.io/scalafix](https://scalacenter.github.io/scalafix/) |
| **bleep** | 宏友好的构建工具；对多阶段构建的一等支持 | [github.com/oyvindberg/bleep](https://github.com/oyvindberg/bleep) |

## 用例交叉引用

- 用于消除样板（序列化器、编解码器、lens）的编译期代码生成，参见 [非法状态不可表示](../usecases/invalid-states.md)。
- 通过 quote 模式匹配在编译期融合操作以优化 DSL，参见 [编译期计算](../usecases/compile-time.md)。
- 在宏中用 `Expr.summon` 进行条件隐式 summon，参见 [相等性](../usecases/equality.md)。
- 针对性能关键数值代码（幂运算、多项式求值）的 staged 计算，参见 [类型算术](../usecases/type-arithmetic.md)。
- 为领域特定验证生成自定义编译期错误信息，参见 [编译期计算](../usecases/compile-time.md)。
- 入口点：`inline def` + `${ ... }` 连接 inline 与宏，参见 [编译期计算](../usecases/compile-time.md)。
- 用 `scala.quoted.staging` 进行运行时多阶段编程，参见 [编译期计算](../usecases/compile-time.md)。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T17-macros-metaprogramming.md
