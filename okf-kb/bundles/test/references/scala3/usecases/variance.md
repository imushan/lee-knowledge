---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC17-variance.md
title: 型变与子类型化（UC17）
description: 精确控制协变、逆变与子类型关系，避免不安全的转换或过僵的 API。
tags:
- 型变
- 协变
- 逆变
- 子类型
- 联合类型
- 交集类型
- UC17
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:08:48Z'
---

# 型变与子类型化（UC17）

## 约束目标

**精确控制协变、逆变与子类型化关系。**

决定 `Container[Dog]` 是否是 `Container[Animal]` 的子类型、两个不相关类型能否在同一表达式中合并、以及包装类型是继承还是打破其底层类型的子类型化。错误的型变会导致不安全的转换或过僵的 API；精确的型变标注可以同时避免两者。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 联合 / 交集类型 | 表达"之一"或"全部"，无需引入类层级；联合放宽、交集收窄 | [T02 union-intersection](../catalog/union-intersection.md) |
| Opaque types | 创建一个**不**继承其表示类型子类型关系的新类型 | [T03 newtypes-opaque](../catalog/newtypes-opaque.md) |
| 类型 lambda | 重排或部分应用类型参数，使型变与所需形状对齐 | [T40 type-lambdas](../catalog/type-lambdas.md) |
| Enums / ADTs | enum 分支是 enum 的子类型，enum 类型参数上的型变标注会传播到分支 | [T01 algebraic-data-types](../catalog/algebraic-data-types.md) |
| Open classes | 控制哪些类可被扩展，直接影响子类型格 | [T21 encapsulation](../catalog/encapsulation.md) |

## 模式

### 模式 A：带联合返回类型的协变容器

协变容器可以在联合类型处返回值，当合并两个不同元素类型的容器时自然地放宽结果类型。

```scala
enum MyList[+A]:
  case Nil
  case Cons(head: A, tail: MyList[A])

import MyList.*
val ints: MyList[Int] = Cons(1, Cons(2, Nil))
val strs: MyList[String] = Cons("a", Nil)

// 协变允许在期望 MyList[Int | String] 处使用 MyList[Int]：
def combine[A](a: MyList[A], b: MyList[A]): MyList[A] = ???
val both: MyList[Int | String] = combine(ints, strs)
// Without union types, this would require an explicit common supertype.

trait Animal
class Dog extends Animal
class Cat extends Animal

// 协变也意味着：
val animals: MyList[Animal] = Cons(Dog(), Cons(Cat(), Nil))
val dogs: MyList[Dog] = Cons(Dog(), Nil)
val all: MyList[Animal] = dogs // ok: MyList[Dog] <: MyList[Animal]
```

```scala
trait Animal
class Dog extends Animal
class Cat extends Animal
```

### 模式 B：用交集类型表达组合约束

交集类型要求一个值同时满足多个接口。这会收窄子类型关系：`A & B <: A` 且 `A & B <: B`。

```scala
trait Printable:
  def printMe(): Unit
trait Serializable:
  def toBytes: Array[Byte]

// 无需定义组合 trait 即可同时要求两种能力：
def process(x: Printable & Serializable): Unit =
  x.printMe()
  val bytes = x.toBytes
  println(s"${bytes.length} bytes")

class Report(data: String) extends Printable, Serializable:
  def printMe(): Unit = println(data)
  def toBytes: Array[Byte] = data.getBytes

process(Report("Q4")) // ok: Report <: Printable & Serializable

// 逆变位置：接受交集类型的函数
// 比单独接受任一类型更通用：
val f: (Printable & Serializable) => Unit = process
// f can be used wherever (Printable => Unit) or (Serializable => Unit) is expected?
// No -- function arguments are contravariant:
// (A => R) <: (B => R) when B <: A.
// (Printable & Serializable => Unit) is a SUPERtype of (Printable => Unit).
```

### 模式 C：Opaque Types 按设计打破子类型化

opaque type 创建新的类型边界。在其定义作用域之外，它与底层类型没有子类型关系，即使底层类型本身有。

```scala
object Ids:
  opaque type UserId = Long
  object UserId:
    def apply(id: Long): UserId = id
    extension (id: UserId) def value: Long = id

  opaque type OrderId = Long
  object OrderId:
    def apply(id: Long): OrderId = id
    extension (id: OrderId) def value: Long = id

import Ids.*

def findUser(id: UserId): Unit = ()
def findOrder(id: OrderId): Unit = ()

val uid = UserId(42)
val oid = OrderId(42)
findUser(uid) // ok
// findUser(oid) // error: expected UserId, got OrderId
// findUser(42L) // error: expected UserId, got Long
// 即便两者内部都是 Long，子类型关系已被切断。
// 这是与类型别名（保留子类型化）的关键区别。
```

### 模式 D：Enum ADT 上的型变标注

enum 类型参数可携带 `+` / `-` 标注。编译器会检查每个分支是否与声明的型变一致。

```scala
enum Result[+E, +A]:
  case Success(value: A)
  case Failure(error: E)

// 协变允许：
val ok: Result[Nothing, Int] = Result.Success(42)
val fail: Result[String, Nothing] = Result.Failure("boom")
val r1: Result[String, Int] = ok // ok: Result[Nothing, Int] <: Result[String, Int]
val r2: Result[String, Int] = fail // ok: Result[String, Nothing] <: Result[String, Int]

// 带类型上界以约束型变：
enum Validated[+E, +A]:
  case Valid(value: A)
  case Invalid(errors: List[E])

// 上界与型变交互：
enum Expr[+A <: Number]:
  case Lit(value: A)
  case Add(left: Expr[A], right: Expr[A])
// Expr[Integer] <: Expr[Number] because +A and Integer <: Number.
```

## Scala 2 对比

| 方面 | Scala 2 | Scala 3 |
|---|---|---|
| 型变标注 | 类与 trait 类型参数上的 `+` / `-`，语法相同 | 语法与规则相同，无变化 |
| 合并不相关类型 | 需要公共父类型或手写 `Either` / `Coproduct` | 联合类型（`A \| B`）无需包装即可表达"之一" |
| 收窄到组合约束 | `A with B` 复合类型（非交换） | `A & B` 交集类型（可交换，成员合并合理） |
| 为 newtype 打破子类型化 | 值类（`extends AnyVal`）是 `AnyVal` 的子类型，而非其包装类型的子类型——值类与 opaque types 都不创建到底层类型的子类型链接。Tagged types（shapeless）部分可行 | opaque types 在其作用域外完全切断子类型关系 |
| Enum 型变 | 不适用——无 `enum` 关键字；sealed trait 层级在父类型上携带型变 | `enum` 直接支持型变标注，分支会被检查一致性 |
| 用于型变对齐的类型 lambda | 结构细化技巧：`({type L[A] = Map[K, A]})#L` | 一等 `[A] =>> Map[K, A]` 语法 |

## 何时选择哪个特性

| 需求 | 推荐 |
|---|---|
| 元素是子类型时容器也是子类型 | 类型参数上的 **`+A` 协变**，配合联合类型自然放宽（模式 A） |
| 一个值同时满足多个接口 | **交集类型** `A & B`（模式 B），无需定义组合 trait |
| 包装类型**不**是其表示的子类型 | **Opaque types**（模式 C），跨领域边界保证类型安全 |
| 带型变感知分支的 ADT | **带 `+`/`-` 标注的 enum**（模式 D），编译器检查分支一致性 |
| 将多参数类型适配为一元形状并保持正确型变 | **类型 lambda**：`[A] =>> Map[K, A]` 保留 `Map` 第二参数的型变 |
| 控制谁能添加新子类型 | 基类的 **`open`** 修饰符，或 `sealed` / `final` 关闭层级 |

# 引用

- 原文：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC17-variance.md
