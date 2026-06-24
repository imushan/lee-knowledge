---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC12-compile-time.md
title: 编译期编程（Compile-Time Programming）
description: 将计算与验证从运行时移到编译期，让错误在编译阶段暴露，常量由编译器求值而非由 JVM 求值。
tags:
- 编译期编程
- inline
- match types
- compiletime.ops
- 宏
- 类型 lambdas
- Scala 3
- vibe-types
- UC12
timestamp: '2026-06-24T12:05:49Z'
---

# 编译期编程（Compile-Time Programming）

## 约束目标

将计算与验证从运行时移到编译期。错误在编译期间暴露，而非在生产中才出现。常量由编译器求值，而非由 JVM 求值。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| Inline | 编译期求值、分支与内联 | [T16 compile-time-ops](../catalog/compile-time-ops.md) |
| Match types | 类型层面的模式匹配；从类型计算类型 | [T41 match-types](../catalog/match-types.md) |
| Compiletime ops | 类型层面的算术与字符串操作 | [T16 compile-time-ops](../catalog/compile-time-ops.md) |
| 宏（Macros） | 通过 quotes 与 splices 实现完整的编译期元编程 | [T17 macros-metaprogramming](../catalog/macros-metaprogramming.md) |
| 类型 lambdas（Type lambdas） | 高阶类型层面的类型函数 | [T40 type-lambdas](../catalog/type-lambdas.md) |

## 模式

### 模式 1 — 用 `inline if` / `inline match` 实现编译期分支

当审查值在编译期已知时，`inline match` 在编译期间选择分支。死分支被完全消除。

```scala
// 一个 match type 让返回类型与输入一样精确，
// 因此每个分支产出的是字面量类型而非被宽化的 String。
type Describe[X] = X match
  case Int     => "integer"
  case String  => "string"
  case Boolean => "boolean"

inline def describe[X](inline x: X): Describe[X] =
  inline x match
    case _: Int     => "integer"
    case _: String  => "string"
    case _: Boolean => "boolean"

val a: "integer" = describe(42)      // 字面量类型——编译期解析
val b: "string"  = describe("hello")
// describe(List(1)) // 编译错误——无匹配分支
```

被消除分支中的代码不会被类型检查，从而支持条件编译：

```scala
inline val debug = false

inline def log(inline msg: String): Unit =
  inline if debug then println(msg)
// 当 debug 为 false 时，println 调用被完全擦除
```

### 模式 2 — 用 `compiletime.ops` 实现类型层面算术

使用单例类型与内置操作在类型层面执行算术与比较。

```scala
import compiletime.ops.int.*

type Pos[N <: Int] = N > 0

// 一个在类型层面追踪大小的向量
class Vec[N <: Int] private (val elems: Array[Double]):
  def append[M <: Int](other: Vec[M]): Vec[N + M] =
    Vec(elems ++ other.elems)
  def head(using N > 0 =:= true): Double = elems(0)

object Vec:
  // 长度存在于类型参数中；调用方显式声明它。
  def apply[N <: Int](elems: Array[Double]): Vec[N] = new Vec(elems)

val v2: Vec[2] = Vec(Array(1.0, 2.0))
val v3: Vec[3] = Vec(Array(3.0, 4.0, 5.0))
val v5: Vec[5] = v2.append(v3) // 2 + 3 = 5，编译期计算
```

### 模式 3 — 用 `constValue` / `constValueTuple` 提取单例类型

将编译期已知的类型提取为运行时值，无需样板代码。

```scala
import compiletime.{constValue, constValueTuple}

// 把单例类型提取为运行时值
val n: 42 = constValue[42]

// 提取一组单例类型
val rgb = constValueTuple[("red", "green", "blue")]
// rgb: ("red", "green", "blue") = ("red", "green", "blue")

// 与 match types 组合使用：
type ElementNames[T] = T match
  case EmptyTuple       => EmptyTuple
  case (name, _) *: rest => name *: ElementNames[rest]

type Schema = ("name", String) *: ("age", Int) *: EmptyTuple
type Names  = ElementNames[Schema] // ("name", "age")

val names = constValueTuple[Names] // 运行时得到 ("name", "age")
```

### 模式 4 — 基于宏的编译期验证

当 `inline` 不够用时，宏可在编译期完整访问 AST。可验证字符串格式、解析 DSL 或生成代码。

```scala
import scala.quoted.*

object Regex:
  inline def checked(inline pattern: String): scala.util.matching.Regex =
    ${ checkedImpl('pattern) }

  private def checkedImpl(pattern: Expr[String])(using Quotes): Expr[scala.util.matching.Regex] =
    import quotes.reflect.*
    pattern.valueOrAbort match
      case p =>
        try
          java.util.regex.Pattern.compile(p)
          '{ new scala.util.matching.Regex($pattern) }
        catch
          case e: java.util.regex.PatternSyntaxException =>
            report.errorAndAbort(s"Invalid regex: ${e.getMessage}")

// 用法——来自*不同的*编译单元：宏不能在定义它的同一文件中调用，
// 因此这些调用位于另一个源文件中。
// val email = Regex.checked("""[\w.]+@[\w.]+""") // 可编译
// val bad   = Regex.checked("""[unclosed""")      // 编译错误：Invalid regex
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 编译期分支 | 不可用——所有分支在运行时都存在；`@switch` 仅优化匹配 | `inline if` / `inline match`——分支在编译期解析并消除 |
| 类型层面算术 | 通过 Shapeless `Nat` 的 Church 编码，或字面量类型 hack——编译慢、错误信息差 | `compiletime.ops.int.*`——内置、快速、错误信息清晰 |
| 提取单例类型 | `shapeless.Witness`——库级别、受限 | `constValue` / `constValueTuple`——语言内置 |
| 宏 | `scala.reflect` 宏——复杂、与编译器内部紧耦合、不可移植 | Quotes 与 splices（`'{ }` / `${ }`）——有原则、卫生、基于 TASTy |
| 类型 lambdas | `({type L[A] = Either[String, A]})#L`——一种工具支持差的 hack | `[A] =>> Either[String, A]`——一等语法 |

## 何时选择哪个特性

**`inline`** 是首选工具。它处理常量折叠、死分支消除以及字面量的编译期验证。大多数编译期需求仅靠 `inline def`、`inline if` 与 `inline match` 即可满足。

**Match types** 适用于需要从另一个类型计算*类型*的场景——映射一组类型、根据类型参数选择编解码器，或实现类型层面的递归。它们替代了许多 Shapeless 风格的类型层面编程。

**`compiletime.ops`** 处理类型层面的算术与比较。当类型携带数值参数（向量长度、矩阵维度、有界整数）且希望编译器验证算术属性时使用。

**宏** 是最后手段。当需要在编译期检查或变换 AST 时使用——根据文法验证字符串字面量、从注解生成样板，或嵌入外部 DSL。在够用时优先使用 `inline`，因为宏增加编译复杂度且更难维护。

**类型 lambdas** 是构建块，而非独立技术。当高阶类型需要部分应用时使用——例如在期望 `F[_]` 的位置传入 `[A] =>> Either[Error, A]`。

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC12-compile-time.md
- 相关用例：[builder-config](builder-config.md)、[state-machines](state-machines.md)
