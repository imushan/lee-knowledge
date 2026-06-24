---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T08-variance-subtyping.md
title: 变型与子类型规则（Variance & Subtyping）
description: 通过协变、逆变与不变标注声明并强制泛型类型的可替换性规则，在编译期保证 Liskov 替换原则成立。
tags:
- T08
- Scala 3
- vibe-types
- 变型
- 子类型
- 协变
- 逆变
- Liskov
timestamp: '2026-06-24T12:05:55Z'
---

# 变型与子类型规则（Variance & Subtyping）

> **引入版本：** Scala 3.0

## 简介

变型标注声明类型构造子的子类型关系如何关联其类型实参的子类型关系。**协变**（`+A`）表示当 `B <: A` 时 `F[B] <: F[A]`——容器随元素同向变化。**逆变**（`-A`）表示当 `B <: A` 时 `F[A] <: F[B]`——容器随元素反向变化。**不变**（普通 `A`）表示即便 `A <: B`，`F[A]` 与 `F[B]` 也互不相关。Scala 拥有主流语言中最显式的变型系统：类或 trait 的每个类型参数都可标注，编译器通过检查每次出现在协变、逆变或不变位置来强制标注的健全性。

## 可表达的约束

**变型标注让你在编译期声明并强制泛型类型的可替换性规则。** `List[+A]` 保证 `List[Cat]` 可用于任何期望 `List[Animal]` 的地方（Liskov 替换）。`Function1[-A, +B]` 保证接受 `Animal` 的函数可替换接受 `Cat` 的函数（逆变输入），而其结果协变替换。编译器拒绝违反这些保证的定义——例如在方法参数位置使用协变类型参数——从源头防止不安全的转换。

## 最小示例

协变：

```scala
trait Animal { def name: String }
case class Cat(name: String) extends Animal
case class Dog(name: String) extends Animal

enum Opt[+A]:
  case Some(value: A)
  case None

val catOpt: Opt[Cat] = Opt.Some(Cat("Felix"))
val animalOpt: Opt[Animal] = catOpt // OK：Opt[Cat] <: Opt[Animal]
```

逆变：

```scala
trait Animal { def name: String }
case class Cat(name: String) extends Animal

trait Printer[-A]:
  def print(value: A): Unit

val animalPrinter: Printer[Animal] = a => println(a.name)
val catPrinter: Printer[Cat] = animalPrinter // OK：Printer[Animal] <: Printer[Cat]
// 能打印任意动物的打印机当然也能打印猫
```

不变（可变引用必须不变）：

```scala
trait Animal { def name: String }
case class Cat(name: String) extends Animal
case class Dog(name: String) extends Animal

class MutRef[A](var value: A)
val catRef: MutRef[Cat] = MutRef(Cat("Felix"))
// val animalRef: MutRef[Animal] = catRef // 错误：MutRef 在 A 上不变
// 若允许，animalRef.value = Dog("Rex") 会破坏 catRef
```

方法签名中的变型（协变输出用下界）：

```scala
trait Animal { def name: String }
case class Cat(name: String) extends Animal
case class Dog(name: String) extends Animal

enum MyList[+A]:
  case Cons(head: A, tail: MyList[A])
  case Nil

  def prepend[B >: A](elem: B): MyList[B] =
    Cons(elem, this)

val cats: MyList[Cat] = MyList.Cons(Cat("Felix"), MyList.Nil)
val animals: MyList[Animal] = cats.prepend(Dog("Rex")) // MyList[Animal]
```

函数变型（`Function1[-A, +B]`）：

```scala
trait Animal { def name: String }
case class Cat(name: String) extends Animal

val f: Cat => Animal = (c: Cat) => c
val g: Animal => Cat = ???
// Function1 输入逆变、输出协变：
val h: Animal => Animal = f // 错误：Cat => Animal 不是 Animal => Animal
val i: Cat => Animal = g    // OK：Animal => Cat <: Cat => Animal
```

## 与其他特性的交互

| 特性 | 组合方式 |
|---|---|
| [枚举 / ADT](algebraic-data-types.md) | enum 类型参数携带变型：`enum Option[+A]`；case 继承父类型变型。带逆变字段（如回调）的 case 需显式 `extends` 并调整类型参数。 |
| [不透明类型](newtypes-opaque.md) | 不透明类型可通过边界声明变型：`opaque type IArray[+T] = Array[T]`；外部按声明边界决定变型，而非底层表示，可实现"幻象变型"。 |
| [泛型与边界](generics-bounds.md) | 下界（`B >: A`）是在逆变位置使用协变类型参数（如协变容器的方法参数）的标准逃生舱。 |
| type lambda | type lambda 参数不能携带变型标注；变型只能在具名类型定义（`type`、`trait`、`class`）上声明。 |
| [given 实例](type-classes.md) | 为协变类型提供类型类实例需谨慎：协变 `List[+A]` 上的 `given Ordering[List[A]]` 需正确处理拓宽后的类型。 |
| [联合 / 交叉类型](union-intersection.md) | 协变类型构造子对交叉可分配：`List[A & B] <: List[A] & List[B]`；逆变构造子对联合可分配。 |

## 注意事项与局限

1. **协变类型出现在逆变位置。** 最常见的变型错误：把 `+A` 用作方法参数类型。修复方式是带下界的类型参数：`def add[B >: A](x: B)`。协变集合的 `append`/`prepend` 方法必须有此形式。
2. **可变字段强制不变。** `var x: A` 既读（协变）又写（逆变）`A`，故 `A` 必须不变。协变类型用 `val`，或将变异封装在私有 API 之后。
3. **Java 数组协变（不健全）。** Scala 的 `Array[A]` 不变，而 Java 的 `T[]` 协变；这是有意的健全性修复，意味着 `Array[Cat]` 不能传给期望 `Array[Animal]` 的地方。
4. **类型参数 vs 类型成员变型。** 抽象类型成员不能直接携带变型标注，其变型由使用位置推断，不如类型参数标注显式。
5. **经不透明类型的幻象变型。** `opaque type F[+A] = G[A]`（`G` 不变）合法：编译器仅按对外可见的声明边界检查变型，而不按仅在内部可见的底层类型。这很强大，但需作者在定义作用域内手动确保健全性。
6. **逆变类型与 `Nothing`。** 因 `Nothing` 是底部类型，`Printer[Nothing]` 是 `Printer` 层级的顶端（逆变反转子类型关系），可能违反直觉。

## 初学者心智模型

把变型看作回答：**"若我有一箱猫，能否在需要一箱动物的地方使用？"**

- **协变（`+A`）：** 可以，一箱猫就是一箱动物。适用于只读容器（只取出）。
- **逆变（`-A`）：** 反过来——动物的处理者也是猫的处理者。适用于只写/消费类型（只放入）。
- **不变（`A`）：** 都不行——可变的一箱猫不是可变的一箱动物，因为有人可能放入狗。

Liskov 替换原则是形式化依据：若 `Cat <: Animal`，则任何期望 `Animal` 的代码在被给予 `Cat` 时必须正确工作。变型标注告诉编译器哪些类型构造子保持这种可替换性以及方向。

## 常见类型检查器错误

```
-- [E093] Variance Error ---
trait Box[+A]:
  def set(value: A): Unit
  ^
covariant type A occurs in contravariant position in type A of parameter value
修复：使用带下界的类型参数：
  def set[B >: A](value: B): Unit
```

```
-- [E007] Type Mismatch Error ---
val ref: MutRef[Animal] = MutRef[Cat](Cat("Felix"))
^^^^^^^^^^^^^^^^^^^^^^^^
Found:    MutRef[Cat]
Required: MutRef[Animal]
Note: Cat <: Animal, but class MutRef is invariant in type A.
修复：MutRef 可变故必须不变；需要协变时使用不可变包装器。
```

```
-- [E093] Variance Error ---
enum Tree[+A]:
  case Leaf(value: A)
  case Node(left: Tree[A], right: Tree[A], f: A => Boolean)
  ^
covariant type A occurs in contravariant position in type A => Boolean
修复：将函数移出 enum case，或改用带下界的方法参数。
```

## 用例交叉引用

- 协变领域层级用于 sum 类型与密封 trait，参见[领域建模](../usecases/domain-modeling.md)。
- 用于序列化/格式化的逆变类型类，参见扩展性。
- 设计变型正确的集合 API，参见[变型](../usecases/variance.md)。
- 用变型防止类型化状态机中的非法状态转换，参见[防止非法状态](../usecases/invalid-states.md)。

## 源参考

- [Scala 3 Reference: Variance](https://docs.scala-lang.org/scala3/reference/overview.html)
- [Scala 3 Book: Variance](https://docs.scala-lang.org/scala3/book/types-variance.html)
- [Scala API: Function1[-T1, +R]](https://www.scala-lang.org/api/3.x/scala/Function1.html)

# 引用

- [T08-variance-subtyping.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T08-variance-subtyping.md)
