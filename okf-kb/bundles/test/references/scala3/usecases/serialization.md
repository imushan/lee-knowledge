---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC19-serialization.md
title: 序列化编解码器（UC19）
description: 通过 derives、Mirror 与 inline 在编译期自动派生类型安全的序列化编解码器。
tags:
- 序列化
- 编解码器
- derives
- Mirror
- inline
- 类型类派生
- UC19
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:09:32Z'
---

# 序列化编解码器（UC19）

## 约束目标

自动派生序列化器与反序列化器，并保证完全的类型安全。每个字段和变体都必须在编译期被覆盖——运行时不会再出现"字段缺失"的意外。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 类型类派生（`derives`） | 一关键字为 ADT 自动生成编解码器 | [T06 derivation](../catalog/derivation.md) |
| Mirror（ProductOf / SumOf） | 编译器生成的结构描述，用于手动派生 | [T06 derivation](../catalog/derivation.md) |
| Inline / compiletime | 编译期字段迭代；零开销序列化 | [T16 compile-time-ops](../catalog/compile-time-ops.md) |
| 宏 | 当 inline 不足时进行完整编译期代码生成 | [T17 macros-metaprogramming](../catalog/macros-metaprogramming.md) |
| 匹配类型 | 从结构计算编解码器类型（例如字段类型 → 线缆格式） | [T41 match-types](../catalog/match-types.md) |

## 模式

### 模式 1：用 `derives` 自动派生编解码器

最简路径：声明一个带 `derived` 方法的类型类，然后用 `derives` 附着。

```scala
import scala.deriving.Mirror

trait JsonCodec[A]:
  def encode(a: A): String
  def decode(s: String): Either[String, A]

// A real library provides this `derived` via a macro/inline; this stub is just
// enough for `derives` to resolve. (See patterns 2 and 3 for a working body.)
object JsonCodec:
  inline given derived[A](using m: Mirror.Of[A]): JsonCodec[A] = new JsonCodec[A]:
    def encode(a: A): String = a.toString
    def decode(s: String): Either[String, A] = Left("not implemented")

// Usage is a single keyword:
case class User(name: String, age: Int) derives JsonCodec
enum Role derives JsonCodec:
  case Admin, Editor, Viewer

val json = summon[JsonCodec[User]].encode(User("Ada", 36))
```

### 模式 2：用 `Mirror.ProductOf` / `Mirror.SumOf` 手动派生

通过 `Mirror` 检查编译期结构，构建通用编解码器。

```scala
import scala.deriving.Mirror
import scala.compiletime.{erasedValue, summonInline}

trait Encoder[A]:
  def encode(a: A): Map[String, Any]

object Encoder:
  given Encoder[String] with
    def encode(a: String) = Map("value" -> a)
  given Encoder[Int] with
    def encode(a: Int) = Map("value" -> a)

  inline given derived[A](using m: Mirror.ProductOf[A]): Encoder[A] =
    new Encoder[A]:
      def encode(a: A): Map[String, Any] =
        val elems = a.asInstanceOf[Product].productIterator.toList
        val labels = labelsOf[m.MirroredElemLabels]
        labels.zip(elems).toMap

inline def labelsOf[T <: Tuple]: List[String] =
  inline erasedValue[T] match
    case _: EmptyTuple => Nil
    case _: (head *: tail) =>
      scala.compiletime.constValue[head].toString :: labelsOf[tail]

case class Point(x: Int, y: Int) derives Encoder
val m = summon[Encoder[Point]].encode(Point(1, 2))
// Map("x" -> 1, "y" -> 2)
```

### 模式 3：基于 inline 的无宏序列化器

使用 `inline` 和 `compiletime` 在编译期展开字段访问——无反射、无宏。

```scala
import scala.compiletime.{erasedValue, summonInline, constValue}

trait Write[A]:
  def write(a: A): String

object Write:
  given Write[Int] with { def write(a: Int) = a.toString }
  given Write[String] with { def write(a: String) = s""""$a"""" }

  inline def writeElems[Ts <: Tuple, Ls <: Tuple](p: Product, i: Int): List[String] =
    inline (erasedValue[Ts], erasedValue[Ls]) match
      case _: (EmptyTuple, EmptyTuple) => Nil
      case _: (t *: ts, l *: ls) =>
        val label = constValue[l].toString
        val writer = summonInline[Write[t]]
        val value = writer.write(p.productElement(i).asInstanceOf[t])
        s""""$label":$value""" :: writeElems[ts, ls](p, i + 1)

  inline given derived[A](using m: scala.deriving.Mirror.ProductOf[A]): Write[A] =
    (a: A) =>
      val fields = writeElems[m.MirroredElemTypes, m.MirroredElemLabels](
        a.asInstanceOf[Product], 0
      )
      fields.mkString("{", ",", "}")

case class Config(host: String, port: Int) derives Write
val json = summon[Write[Config]].write(Config("localhost", 8080))
// {"host":"localhost","port":8080}
```

### 模式 4：编译期模式校验

使用匹配类型在编译期验证类型的结构是否匹配预期模式。

```scala
import scala.compiletime.ops.int.*

// 类型级字段计数，由 product 的元素类型元组计算：
type FieldCount[Elems <: Tuple] = scala.Tuple.Size[Elems]

// 类型级"至少 N 个字段"谓词：
type HasAtLeast[Elems <: Tuple, N <: Int] =
  scala.Tuple.Size[Elems] >= N =:= true

// 将编解码器约束为仅作用于字段数 >= 2 的类型
inline def toCsv[A](a: A)(
  using m: scala.deriving.Mirror.ProductOf[A],
       ev: HasAtLeast[m.MirroredElemTypes, 2]
): String =
  a.asInstanceOf[Product].productIterator.mkString(",")

case class Row(id: Int, name: String, score: Int)
toCsv(Row(1, "Ada", 100)) // compiles — 3 fields >= 2
// case class Solo(x: Int)
// toCsv(Solo(1)) // compile error — 1 field < 2
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 自动派生 | Shapeless `Generic` + `LabelledGeneric`；复杂的隐式链 | `derives` 关键字 + `Mirror`——内建于语言 |
| 字段迭代 | 用 `Poly` 折叠 `HList`；学习曲线陡峭 | `inline erasedValue` + `Tuple`——读起来像普通 Scala |
| 和类型派生 | `Generic.Aux[A, Repr]` 配合 `Coproduct` | `Mirror.SumOf` 配合 `ordinal`；`enum` 封闭层级 |
| 编译期反射 | 基于宏的 `TypeTag`、`WeakTypeTag`——跨版本脆弱 | `Mirror` + `constValue`——稳定的编译器 API |
| 零开销编解码器 | 需要宏注解（如 `@JsonCodec`） | `inline` 展开——无需宏注解 |

## 何时选择哪个特性

- **默认使用 `derives`**。若库支持，单个关键字即可获得无样板编解码器，覆盖绝大多数 product 与 sum 类型。
- **直接使用 `Mirror`** 当你在构建编解码器库或需要自定义派生逻辑（重命名字段、跳过默认值、转换 enum）。`Mirror.ProductOf` 和 `Mirror.SumOf` 提供结构化元数据。
- **使用 `inline` + `compiletime`** 当性能敏感且需要零反射、零分配编解码器。编译器将字段访问展开为直线代码。
- **求助于宏** 当 inline 派生遇到限制——例如生成伴生对象、产出自定义错误消息，或处理超出 inline 递归深度的递归类型。
- **使用匹配类型** 表达模式级约束（最小字段数、字段类型限制），这些约束应在编解码器实例化前就被强制。

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC19-serialization.md
