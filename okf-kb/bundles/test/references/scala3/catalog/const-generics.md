---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T15-const-generics.md
title: 单例类型、字面量类型与编译期值参数
description: 通过单例/字面量类型、inline 参数、constValue 与 compiletime.ops，将字面量值提升到类型层，实现 const
  generics 风格的维度与容量约束。
tags:
- T15
- Scala 3
- vibe-types
- const generics
- 单例类型
- 字面量类型
- compiletime.ops
- 类型级算术
timestamp: '2026-06-24T12:05:12Z'
---

# 单例类型、字面量类型与编译期值参数

## 简介

Scala 3 没有 Rust 那样的专用 `const N: Int` 泛型参数语法，而是通过一组特性组合达到同样效果：

- **单例/字面量类型**——每个字面量值都有一个仅是该值的类型：`42` 的类型是 `42`，`"hello"` 的类型是 `"hello"`。这些类型是其拓宽形式的子类型（`42 <: Int`）。
- **`inline` 参数**——强制参数在编译期求值，确保值在静态已知。
- **`constValue[T]`**——在编译期从单例类型中提取值。
- **`compiletime.ops`**——对单例类型的类型级算术、布尔与字符串操作。
- **match 类型**——从类型计算类型，实现类型级条件与递归。

这些特性合在一起让你把尺寸、维度、容量编码进类型——与 Rust 的 const generics 扮演同样角色——但更具通用性，因为任何单例类型都可用，而不仅是标量。

## 可表达的约束

**不同的字面量值产生不同的类型。对单例类型的类型级操作在编译期被检查，因此维度不匹配、非法尺寸与算术错误都变为类型错误。**

更具体地说：

- **不同值 = 不同类型。** `Matrix[3, 4]` 与 `Matrix[4, 3]` 是不同类型。期望前者的函数拒绝后者。
- **编译期求值。** `inline` 参数必须解析为编译期常量。编译器拒绝用运行时值调用需要编译期值的代码。
- **类型级算术。** `compiletime.ops.int.*` 提供对单例 `Int` 类型的 `+`、`-`、`*`、`/`、`<`、`>=` 等，在编译期检查。

## 最小示例

```scala
import scala.compiletime.constValue
import scala.compiletime.ops.int.*

// 长度编入类型的类型安全向量
class Vec[N <: Int](val data: Array[Double]):
  inline def length: Int = constValue[N]

// 类型级加法：拼接两个向量
def concat[A <: Int, B <: Int](a: Vec[A], b: Vec[B]): Vec[A + B] =
  Vec[A + B](a.data ++ b.data)

val v3 = Vec[3](Array(1.0, 2.0, 3.0))
val v2 = Vec[2](Array(4.0, 5.0))
val v5: Vec[5] = concat(v3, v2) // OK —— 3 + 2 = 5
// val bad: Vec[4] = concat(v3, v2) // 编译错误 —— Vec[5] ≠ Vec[4]
```

## 可做与不可做

| 模式 | Scala 3 支持度 |
|------|----------------|
| 不同字面量值得到不同类型 | 完全支持（`Vec[3]` ≠ `Vec[4]`） |
| 类型级算术（`3 + 2 = 5`） | 完全支持（`compiletime.ops`） |
| 类型级条件/递归 | 通过 match 类型支持 |
| 运行时值作为 const 参数 | 不支持——必须是字面量或编译期计算值 |
| 带完整证明的 Nat 索引向量 | 部分——无值归纳，须用类型级 Nat 或字面量 Int |

## 与其他特性的交互

| 特性 | 组合方式 |
|------|----------|
| **match 类型**（见 [match-types](match-types.md)） | match 类型支持对单例类型的类型级模式匹配——类型级 `if`/`else` 与递归的机制。 |
| **inline & compiletime**（见 [compile-time-ops](compile-time-ops.md)） | `inline` 强制编译期求值；`constValue` 将类型级单例桥接到值级常量，是运行时提取机制。 |
| **opaque types**（见 [newtypes-opaque](newtypes-opaque.md)） | 与单例类型组合实现零开销维度包装：`opaque type Meters = Double` 配合类型级单位追踪。 |
| **泛型**（见 [generics-bounds](generics-bounds.md)） | 单例类型可放入带上界的泛型类型参数：`[N <: Int]`。 |
| **类型 lambda**（见 [type-lambdas](type-lambdas.md)） | 高阶抽象可按单例类型参数化以实现编译期多态。 |

## 注意事项与局限

1. **无一等公民 const 参数。** 与 Rust 的 `const N: usize` 不同，Scala 用以单例类型为界的常规类型参数（`N <: Int`）。因此写 `Vec[3]` 而非 `Vec<3>`，编译器通过单例类型系统推断/检查。
2. **`constValue` 要求字面量/单例类型。** 若类型参数被拓宽为 `Int`（如通过推断），`constValue` 无法提取值，编译失败。
3. **类型级操作覆盖若干原始种类。** `compiletime.ops` 为 `int`、`long` 提供操作包，也包含 `float`、`double`、`string`、`boolean` 与 `any`。未覆盖者需自定义 match 类型。
4. **无运行时到编译期的桥接。** 不能拿运行时 `Int` 当单例类型参数。值必须是字面量或从其他编译期值计算得到。用 `inline` 参数确保参数为编译期常量。
5. **错误信息可能晦涩。** 类型级算术失败时，错误提及 `3 + 2` 不匹配 `4` 这类类型，尚清晰，但复杂表达式产生冗长的类型级错误信息。
6. **match 类型归约。** 使用 match 类型的复杂类型级计算可能触及编译器归约限制。使用 `@annotation.tailrec` 风格模式或在需要时提高限制。

## 示例 A —— 类型安全的矩阵乘法

```scala
import scala.compiletime.ops.int.*
class Matrix[Rows <: Int, Cols <: Int](
  val data: Array[Array[Double]]
)

// 乘法：(M × N) * (N × P) = (M × P)
// 共享维度 N 必须匹配——由类型系统强制
def multiply[M <: Int, N <: Int, P <: Int](
  a: Matrix[M, N],
  b: Matrix[N, P] // N 必须是同一单例类型
): Matrix[M, P] =
  // 实现略——约束在签名中
  ???

val m23 = Matrix[2, 3](Array(Array(1.0, 2.0, 3.0), Array(4.0, 5.0, 6.0)))
val m34 = Matrix[3, 4](???)
val result: Matrix[2, 4] = multiply(m23, m34) // OK —— 内维度 3 匹配
// val bad = multiply(m23, Matrix[4, 2](???))
// 编译错误：期望 Matrix[3, _] 但找到 Matrix[4, _]
```

## 示例 B —— 编译期边界检查

```scala
import scala.compiletime.ops.int.*
type InRange[N <: Int, Lo <: Int, Hi <: Int] = (N >= Lo) match
  case true  => (N <= Hi) match
    case true  => N
    case false => Nothing
  case false => Nothing

// 只接受 [1, 65535] 范围内的单例 Int 类型
type Port[N <: Int] = InRange[N, 1, 65535]
inline def port[N <: Int](using ev: Port[N] =:= N): N = compiletime.constValue[N]

val p80: 80   = port[80]   // OK
val p443: 443 = port[443]  // OK
// val bad  = port[0]      // 编译错误：Nothing ≠ 0
// val bad2 = port[70000]  // 编译错误：Nothing ≠ 70000
```

## 常见类型检查器错误及读法

### `Found: Vec[5], Required: Vec[4]`

```
Found:   Vec[(3 : Int) + (2 : Int)]
Required: Vec[(4 : Int)]
```

**含义：** 类型级算术产生了与预期不同的结果。编译器算出 3 + 2 = 5，但你声明了 4。修正预期类型。

### `Cannot reduce match type`

```
Cannot reduce `InRange[N, 1, 100]` — type parameter N is not a concrete singleton type.
```

**含义：** 编译器无法归约 match 类型，因为类型参数不是已知字面量。确保调用点提供字面量类型（用 `inline` 参数强制）。

### `No given instance of type =:=[Nothing, N]`

**含义：** 类型级边界检查归约为 `Nothing`，表示值超出范围。约束被违反。

## 用例交叉引用

- 将有效范围编码进类型使越界值无法编译，参见 [非法状态不可表示](../usecases/invalid-states.md)。
- 用于量纲分析与矩阵运算的类型级算术，参见 [类型算术](../usecases/type-arithmetic.md)。
- 编译期计算与特化，参见 [编译期计算](../usecases/compile-time.md)。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T15-const-generics.md
- [Scala 3 Reference — Literal Types](https://docs.scala-lang.org/scala3/reference/new-types/literal-types.html)
- [Scala 3 Reference — Inline](https://docs.scala-lang.org/scala3/reference/metaprogramming/inline.html)
- [Scala 3 Reference — Match Types](https://docs.scala-lang.org/scala3/reference/new-types/match-types.html)
- [scala.compiletime.ops API](https://scala-lang.org/api/3.x/scala/compiletime/ops.html)
