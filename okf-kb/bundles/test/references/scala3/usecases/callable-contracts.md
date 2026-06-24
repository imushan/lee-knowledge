---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC07-callable-contracts.md
title: 可调用契约
description: 对可调用值表达契约——函数类型、SAM 转换、传名参数、eta 展开——让编译器在每个调用点校验元数、参数类型与求值策略。
tags:
- UC07
- Scala 3
- vibe-types
- 可调用契约
- 函数类型
- SAM
- 传名参数
- 上下文函数
timestamp: '2026-06-24T12:09:15Z'
---

# 可调用契约

## 约束目标

对可调用值表达契约——函数类型、SAM 转换、传名参数、eta 展开——使编译器在每个调用点校验元数、参数类型与求值策略。

## 特性工具箱

| 特性 | 作用 | 链接 |
|---|---|---|
| 函数类型 | 一等的 `FunctionN` / `ContextFunctionN` 类型 | [可调用类型](../catalog/callable-typing.md) |
| SAM 类型 | 单抽象方法的 trait 可作为函数字面量使用 | [可调用类型](../catalog/callable-typing.md) |
| 上下文函数 | 把隐式参数烘焙进类型的函数 | [上下文函数](../catalog/context-functions.md) |
| 传名参数 | 延迟求值；由被调用方决定何时（以及是否）计算参数 | [可调用类型](../catalog/callable-typing.md) |

## 模式

### 1 — 一等函数类型

函数是具有精确类型的值。编译器检查元数与参数类型。

```scala
val add: (Int, Int) => Int = (a, b) => a + b
val greet: String => String = name => s"Hello, $name"

def applyTwice[A](f: A => A, x: A): A = f(f(x))

applyTwice((n: Int) => n + 1, 0) // 2
applyTwice(greet, "world")       // "Hello, Hello, world"
```

### 2 — SAM（单抽象方法）转换

任何恰好只有一个抽象方法的 trait 或抽象类，都可以作为函数字面量的目标。

```scala
trait Comparator[A]:
  def compare(a: A, b: A): Int

def sort[A](xs: List[A], cmp: Comparator[A]): List[A] =
  xs.sortWith((a, b) => cmp.compare(a, b) < 0)

// SAM 转换：lambda 填充唯一的抽象方法
val byLength: Comparator[String] = (a, b) => a.length - b.length
sort(List("hello", "hi", "hey"), byLength)
```

### 3 — eta 展开：方法作为函数

Scala 3 在期望函数类型处自动把方法转换为函数值（不再像 Scala 2 那样需要尾随 `_`）。

```scala
object Eta:
  def double(x: Int): Int = x * 2

val xs = List(1, 2, 3)
xs.map(double) // List(2, 4, 6) —— 自动 eta 展开

// 当期望类型明确时，重载方法也适用。
// (format(Int) 与 format(String) 擦除为不同签名，因此无需 @targetName。)
def format(n: Int): String    = n.toString
def format(s: String): String = s.toUpperCase

val ints: List[Int] = List(1, 2)
ints.map(format) // 编译器按期望类型选择 format(Int)
```

### 4 — 用传名参数实现惰性求值

传名参数（`=> T`）把求值推迟到被调用方访问它时。对日志、断言与短路组合子很有用。

```scala
def unless(cond: Boolean)(body: => Unit): Unit =
  if !cond then body

var count = 0
unless(true) { count += 1 } // body 从未求值
assert(count == 0)

// 传名参数可以构造无限结构：
def repeat[A](a: => A): LazyList[A] = a #:: repeat(a)
```

### 5 — 用上下文函数传递隐式携带的可调用值

上下文函数 `T ?=> U` 自动穿线一个 `given` 值，把能力传播变成一等类型。

```scala
import scala.concurrent.ExecutionContext

type Executable[A] = ExecutionContext ?=> A

def runOnPool[A](f: Executable[A]): A =
  given ec: ExecutionContext = ExecutionContext.global
  f // ExecutionContext 被自动提供

val task: Executable[String] = summon[ExecutionContext].toString
runOnPool(task)
```

## Scala 2 对比

| 技术 | Scala 2 | Scala 3 |
|---|---|---|
| 函数类型 | `FunctionN`，最多到 `Function22` | 相同，外加用于隐式参数的 `ContextFunctionN` |
| SAM 转换 | 2.12 以 `-Xexperimental` 引入，后变为默认 | 始终开启；适用于 trait 与抽象类 |
| eta 展开 | 无参列表的方法需要尾随 `_` | 自动——不再需要 `_` |
| 传名参数 | `=> T`——语义相同 | 语义相同 |
| 上下文函数 | 不可用；每个方法都要写隐式参数列表 | `T ?=> U`——一等、可组合、无样板 |

## 何时选择哪个特性

- **用普通函数类型**（`A => B`）做回调、转换以及任何高阶 API。它们是函数式 Scala 的看家本领。
- **用 SAM 转换** 与 Java API 互操作，或当 trait 承载超出裸函数的语义时（例如 `Comparator`、`Runnable`）。
- **用传名参数** 做控制抽象——`unless`、`attempt`、`logIf`——参数不应被及早求值的场合。
- **用上下文函数** 当你想把能力（执行上下文、日志器、事务句柄）沿一串调用传播，而不在每一步重复 `using` 时。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/usecases/UC07-callable-contracts.md
