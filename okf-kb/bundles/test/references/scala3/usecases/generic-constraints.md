---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC04-generic-constraints.md
title: 泛型约束
description: 限制类型参数只能实例化为提供所需能力的类型，编译器拒绝缺失证据的实例化。
tags:
- UC04
- Scala 3
- vibe-types
- 泛型约束
- context bound
- 类型边界
- F-bounded
- 类型 lambda
timestamp: '2026-06-24T12:08:24Z'
---

# 泛型约束

## 约束目标

把类型参数限制为提供了所需能力的类型。编译器拒绝缺少必要证据的实例化，确保泛型代码只被用于满足其假设的类型。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| context bound | `[T: Ordering]`——要求 `T` 存在某个 type-class 实例 | [类型类](../catalog/type-classes.md) |
| 上界 / 下界 | `[A <: Comparable[A]]`——限制为子类型或父类型 | [代数数据类型](../catalog/algebraic-data-types.md) |
| using 子句 | `(using Ord[T])`——显式或隐式传递证据 | [类型类](../catalog/type-classes.md) |
| 类型 lambda | `[A] =>> Either[E, A]`——适配类型形状以匹配约束 | [类型 lambda](../catalog/type-lambdas.md) |
| 联合 / 交集 | 临时组合或交替约束 | [联合与交集类型](../catalog/union-intersection.md) |
| =:= / <:< 证据 | 编译期证明类型相等或子类型关系 | [编译期运算](../catalog/compile-time-ops.md) |

## 模式

### 1 — 用 context bound 表达 type-class 要求

最常见的泛型约束形式。编译器从可用的 given 中自动填入证据。

```scala
import cats.Eq
import cats.syntax.all.* // 把 `===` 引入作用域

def sorted[A: Ordering](xs: List[A]): List[A] = xs.sorted

// 命名 context bound（Scala 3.6+）：
def topN[A: Ordering as ord](xs: List[A], n: Int): List[A] =
  xs.sorted(using ord).take(n)

// 多个 context bound：先用 `Ordering` 排序，再用 `cats.Eq` 折叠连续相等元素。
// A 必须同时有两个 given 可用。
def dedup[A: Ordering : Eq](xs: List[A]): List[A] =
  xs.sorted.foldRight(List.empty[A]):
    case (a, b :: rest) if a === b => b :: rest
    case (a, acc)                  => a :: acc

// 函数没有 Ordering 实例 → 编译错误：
// sorted(List((x: Int) => x)) // error: No given instance of Ordering[Int => Int]
```

### 2 — 上界与下界

按子类型或父类型关系限制类型参数。

```scala
// 上界：A 必须是 Comparable[A] 的子类型
def maxComparable[A <: Comparable[A]](x: A, y: A): A =
  if x.compareTo(y) >= 0 then x else y

// 下界：结果类型是最小上界
def prepend[A, B >: A](xs: List[A], elem: B): List[B] =
  elem :: xs

// 组合边界：
sealed trait Animal
class Dog extends Animal
class Cat extends Animal

def adopt[A >: Dog <: Animal](a: A): String = s"adopted: $a"
// adopt(Dog()) // OK
// adopt(Cat()) // OK —— Cat >: Dog? 否，这里用的是 <: Animal
```

### 3 — F-bounded 多态

类型参数在自身的约束中引用自身。常见于流式 API 与自引用容器。

```scala
trait Builder[Self <: Builder[Self]]:
  def add(item: String): Self
  def build: List[String]

class ListBuilder(items: List[String] = Nil) extends Builder[ListBuilder]:
  def add(item: String): ListBuilder = ListBuilder(items :+ item)
  def build: List[String] = items

def buildAll[B <: Builder[B]](builder: B, items: List[String]): List[String] =
  items.foldLeft(builder)((b, i) => b.add(i)).build

val result = buildAll(ListBuilder(), List("a", "b", "c"))
// List("a", "b", "c")
```

### 4 — 用 =:= 与 <:< 作证据参数

请求类型关系的编译期证明，用于让方法按条件可用。

```scala
class Container[A](val value: A):
  // flatten 仅当 A 本身是 Container 时可用
  def flatten[B](using ev: A =:= Container[B]): Container[B] =
    ev(value)
  // toList 仅当 A <:< Iterable 时可用
  def toList(using ev: A <:< Iterable[?]): List[Any] =
    ev(value).toList

val nested = Container(Container(42))
val flat: Container[Int] = nested.flatten // 编译通过
// Container(42).flatten // 错误：Cannot prove Int =:= Container[B]
```

### 5 — 用交集类型表达多重约束

组合不相关的 type-class 要求，而无需嵌套 context bound。

```scala
trait Printable:
  def print: String
trait Loggable:
  def logLine: String

def report(item: Printable & Loggable): String =
  s"${item.print} [log: ${item.logLine}]"

case class Entry(name: String, level: Int) extends Printable, Loggable:
  def print: String = s"Entry($name)"
  def logLine: String = s"$name@$level"

report(Entry("alpha", 1)) // 编译通过 —— Entry 同时满足两个 trait
```

### 6 — 用类型 lambda 适配形状

当约束期望 `F[_]` 而你有一个多参数类型时，用类型 lambda 适配形状。

```scala
trait Functor[F[_]]:
  extension [A](fa: F[A]) def map[B](f: A => B): F[B]

// Either 有两个类型参数；固定 error 类型：
given [E]: Functor[[A] =>> Either[E, A]] with
  extension [A](fa: Either[E, A])
    def map[B](f: A => B): Either[E, B] = fa.map(f)
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| context bound | `[T: Ordering]`——语法相同，但取值用 `implicitly[Ordering[T]]` | `summon[Ordering[T]]` 或命名 context bound `[T: Ordering as ord]` |
| 上/下界 | 语法与语义完全相同 | 相同，外加联合/交集类型用于临时备选 |
| F-bounded | 可行，但 `implicit` 自类型技巧常见且冗长 | 借助 `using` 子句更清爽；因 extension 方法而更少需要 |
| 证据参数 | `(implicit ev: A =:= B)`——可行但泄漏 implicit 关键字 | `(using ev: A =:= B)`——意图更清晰；证据可被 erased |
| 类型 lambda | 不可用；需插件或 `({type L[A] = Either[E, A]})#L` | 一等公民：`[A] =>> Either[E, A]` |

## 何时选择哪个特性

- **context bound** 作为 type-class 约束的默认选择。它们简洁、被广泛理解，且可与派生组合。
- **上界** 当子类型多态是正确模型时使用（例如限制到封闭层级或 `Comparable` 这样的 Java 接口）。
- **F-bounded 类型** 用于流式 builder API（方法返回具体子类型）。可能时优先用 type-class，因为 F-bounds 把接口与类型参数耦合。
- **证据参数**（`=:=`、`<:<`）用于让方法按类型关系条件性可用，避免单独的包装类型。
- **类型 lambda** 用于把多参数类型适配到单参数 type-class 槽位。它们干净地替代了 Scala 2 的类型投影变通方案。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC04-generic-constraints.md
