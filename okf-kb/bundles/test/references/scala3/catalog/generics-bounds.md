---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T04-generics-bounds.md
title: 泛型与有界多态（Generics & Bounds）
description: 通过上界、下界、上下文边界与 F-有界多态约束类型参数，使泛型代码仅在所需操作存在时才可实例化。
tags:
- T04
- Scala 3
- vibe-types
- 泛型
- 上界
- 下界
- 上下文边界
- F-有界多态
timestamp: '2026-06-24T12:04:25Z'
---

# 泛型与有界多态（Generics & Bounds）

> **引入版本：** Scala 3.0

## 简介

Scala 3 的泛型系统允许对类、trait、方法按类型参数化，而**边界**约束这些类型参数，确保泛型代码只在所需操作存在时才能被实例化。**上界**（`A <: B`）将 `A` 限制为 `B` 的子类型；**下界**（`A >: B`）将 `A` 限制为 `B` 的父类型；**上下文边界**（`A: Ordering`）要求作用域中存在 `Ordering[A]` 的 given 实例。**F-有界多态**（`A <: Comparable[A]`）允许类型在自身边界中引用自身，支持流畅 API 与自引用约束。

## 可表达的约束

**边界限制可替换类型参数的类型集合，使泛型代码仅当其使用的操作被约束所证实时才编译通过。** 上界保证可访问父类型的成员；上下文边界保证存在类型类实例；F-边界保证自引用操作（如 `compareTo`）。无边界时类型参数不受限（`A <: Any`），仅可用通用操作。

## 最小示例

上界：

```scala
def maxOf[A <: Comparable[A]](x: A, y: A): A =
  if x.compareTo(y) >= 0 then x else y

maxOf("hello", "world") // OK —— String <: Comparable[String]
// maxOf(1, 2)          // 错误：Int 不是 <: Comparable[Int]
```

下界：

```scala
enum Expr[+A]:
  case Lit(value: A)

def widen[B >: A](default: B): B = this match
  case Lit(v) => v   // v: A，因 A <: B 可作为 B 返回
```

上下文边界（Scala 3.6 命名语法）：

```scala
def sorted[A: Ordering as ord](xs: List[A]): List[A] =
  xs.sorted(using ord)

sorted(List(3, 1, 2)) // OK —— 存在 given Ordering[Int]
```

F-有界多态：

```scala
trait Pet[A <: Pet[A]]:
  def name: String
  def renamed(newName: String): A

case class Cat(name: String) extends Pet[Cat]:
  def renamed(newName: String): Cat = copy(name = newName)

case class Dog(name: String) extends Pet[Dog]:
  def renamed(newName: String): Dog = copy(name = newName)

def rename[A <: Pet[A]](pet: A, n: String): A = pet.renamed(n)

val kitty: Cat = rename(Cat("Felix"), "Kitty") // 返回 Cat，而非 Pet
```

组合边界：

```scala
def clamp[A <: Comparable[A]](value: A, lo: A, hi: A): A =
  if value.compareTo(lo) < 0 then lo
  else if value.compareTo(hi) > 0 then hi
  else value
```

## 与其他特性的交互

| 特性 | 组合方式 |
|---|---|
| [变型](variance-subtyping.md) | 边界约束变型标注的传播：输出位置的协变类型参数在接收参数的方法中可能需要下界（`B >: A`）。 |
| [given 实例 / using 子句](type-classes.md) | 上下文边界（`A: Ordering`）脱糖为 `using Ordering[A]` 参数；命名上下文边界（`A: Ordering as ord`，Scala 3.6+）直接命名证据。 |
| [不透明类型](newtypes-opaque.md) | 不透明类型可声明对外可见的上界（`opaque type Id <: String = String`），在调用处与泛型上界交互。 |
| type lambda | type lambda 参数可携带边界：`[X <: Comparable[X]] =>> Set[X]` 限制可应用的对象。 |
| match 类型 | match 类型的被审视项可以是带边界的类型参数，实现受边界约束的类型级分派。 |
| 扩展方法 | 扩展方法可有带边界的类型参数：`extension [A <: Numeric[A]](xs: List[A]) def sum: A`。 |

## 注意事项与局限

1. **上下文边界 vs 上界。** 上下文边界 `A: Ordering` *不是*上界——它不使 `A` 成为任何类型的子类型，而是要求作用域中有 given `Ordering[A]`。混淆二者是常见初学者错误。
2. **F-有界多态与类型推断。** 当边界深嵌套或涉及多个类型参数时，`A <: Comparable[A]` 类边界可能干扰类型推断，调用处可能需要显式类型实参。
3. **下界与拓宽。** 下界 `A >: B` 表示 `A` 可以是 `B` 的任意父类型，直至 `Any`。这对协变集合方法（如 `List[+A].appended[B >: A](elem: B): List[B]`）至关重要，结果类型会拓宽。
4. **无列表式多重边界语法。** Scala 3 没有 Scala 2 的 `A <: B with C`；请用交叉类型组合上界：`A <: Serializable & Comparable[A]`。
5. **视图边界已移除。** Scala 2 的视图边界（`A <% B`）已移除，改用带 `Conversion[A, B]` 的上下文边界。
6. **抽象类型成员的边界。** trait 中的类型成员可带边界（`type T <: Animal`），提供与类型参数相同的约束机制，但按路径依赖解析。

## 初学者心智模型

把类型参数边界看作**调用方必须满足的契约**。写 `def sort[A: Ordering](xs: List[A])` 等于声明："我可以排序任意列表，但你必须证明元素类型有排序。" 编译器在每个调用处检查这个证明；证明（given 实例）不存在则不编译——不是在运行时，而是在编译期。

## 常见类型检查器错误

```
-- [E057] Type Mismatch Error ---
def process[A](x: A) = x.length
^^^^^^^^
value length is not a member of A
修复：加上界 def process[A <: String](x: A) = x.length
```

```
-- [E172] Type Error ---
maxOf(1, 2)
^
Type argument Int does not conform to upper bound Comparable[Int]
修复：对原始类型改用 Ordering 上下文边界，或显式使用 java.lang.Integer。
```

```
-- Error ---
sorted(List(Cat("a"), Dog("b")))
No given instance of type Ordering[Pet[? <: Pet[?]]] was found
修复：为具体类型提供 given Ordering，或将列表限定为单一 Pet 子类型。
```

## 用例交叉引用

- [领域建模](../usecases/domain-modeling.md)：用上界与类型类证据约束领域类型。
- [编译期](../usecases/compile-time.md)：要求编译期能力证明的泛型算法。
- 扩展性：用于流畅构建器模式的 F-有界 API。
- [变型](../usecases/variance.md)：泛型集合设计中与变型兼容的边界。

## 源参考

- [Scala 3 Reference: Type Parameter Bounds](https://docs.scala-lang.org/scala3/reference/overview.html)
- [Scala 3 Reference: Context Bounds](https://docs.scala-lang.org/scala3/reference/contextual/context-bounds.html)
- [Scala 3 Reference: Variance](https://docs.scala-lang.org/scala3/reference/overview.html)

# 引用

- [T04-generics-bounds.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T04-generics-bounds.md)
