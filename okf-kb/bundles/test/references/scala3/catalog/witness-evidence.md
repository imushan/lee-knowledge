---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T58-witness-evidence.md
title: Witness 与 Evidence 类型
description: Scala 3 中通过 =:、<:<、自定义 given evidence 在类型层编码前提条件证据，并由编译器经 given 搜索供给的机制。
tags:
- Evidence
- Witness
- '=:'
- <:<
- summon
- 类型证明
- 上下文参数
- T58
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:05:38Z'
---

# Witness 与 Evidence 类型

## 简介

Witness 与 evidence 类型在类型层面编码**证明**，由编译器通过隐式（given）搜索供给。核心类型包括 `=:=[A, B]`（证明 `A` 与 `B` 是同一类型）和 `<:<[A, B]`（证明 `A` 是 `B` 的子类型）。要求 `(using ev: A =:= B)` 的方法只有在编译器能证明两类型相等时才可调用。

在 Scala 3 中，`summon[T]` 可取回任意 given 实例，因此 `summon[A =:= B]` 要么成功（证明相等）要么在编译期失败。`Conversion[A, B]` 提供 `A` 可被隐式转换为 `B` 的证据。与 given 实例、上下文绑定、inline match 一起，evidence 类型让你编写"只有当调用者能提供正确证明时才解锁能力"的 API。

> **Since:** Scala 2（`=:=`、`<:<`）；Scala 3 以 `summon`、`Conversion`、基于 given 的证据加以精炼

## 可表达的约束

**由 evidence 参数守护的方法只有在编译器能合成该 evidence 类型的值时才可调用。这把类型层关系转化为编译期检查的前提条件。**

- `=:=[A, B]` 强制类型相等：仅当 `A` 与 `B` 完全相同时可调用。
- `<:<[A, B]` 强制子类型关系：仅当 `A <: B` 时可调用。
- 自定义 evidence（如 `given CanSerialize[A]`）编码领域特定能力。

## 最小示例

```scala
def collapse[A, B](a: A, b: B)(using ev: A =:= B): List[A] =
  List(a, ev.flip(b)) // ev.flip 将 B 转回 A

collapse(1, 2)        // OK — Int =:= Int
// collapse(1, "two") // 错误：Cannot prove that Int =:= String
```

## 与其他特性的交互

| 特性 | 组合方式 |
|------|----------|
| **类型类**（见 [type-classes](type-classes.md)） | Evidence 类型就是类型类，其实例由编译器自动派生。`=:=` 与 `<:<` 各有唯一的规范 given 实例。 |
| **上下文函数**（见 [context-functions](context-functions.md)） | Evidence 参数即上下文参数（`using`）。上下文函数让你在 lambda 中传递证据而无需显式传参。 |
| **Match types**（见 [match-types](match-types.md)） | 带 `summon` 的 `inline` 方法可根据 evidence 是否存在分支，在编译期按类型关系选择实现。 |
| **路径依赖类型**（见 [path-dependent-types](path-dependent-types.md)） | `=:=` evidence 提供 `apply` 与 `flip` 方法，在两个被证明相等的类型间转换值，类似路径依赖转型。 |
| **Opaque types**（见 [newtypes-opaque](newtypes-opaque.md)） | Evidence 类型与 opaque type 互补：一个 opaque `Token` 可在暴露内部值前要求 `given Authenticated` 证据。 |

## 注意事项与局限

1. **Evidence 在运行时并非免费。** `=:=` 与 `<:<` 实例是堆上分配的对象。在热循环中，考虑 `inline` 方法或 `@specialized` 以避免装箱。Scala 3 的 `inline` + `erasedValue` 可在编译期消除 evidence。
2. **歧义隐式。** 若多个 given 实例都能提供该 evidence，编译器以歧义错误拒绝调用。保持 evidence 实例规范，避免重叠的 given。
3. **逆变 evidence 陷阱。** `<:<` 在第一参数（`From`）逆变、第二参数（`To`）协变。`Nothing <:< Any` 存在，但不能用它证明 `List[Nothing] <:< List[Any]`（需额外证据）。
4. **无否定形式。** 无法表达"A 不等于 B"作为 evidence 类型。Scala 3 的 `NotGiven[A =:= B]` 模式近似实现，但在歧义场景下有边界情况。
5. **宏内 summon。** inline 方法内的 `summon` 在调用点解析，而非定义点。这很强大，但当调用点作用域缺少期望 given 时可能令人意外。

## 新手心智模型

把 evidence 类型想成**身份徽章**。一个由 `(using ev: A =:= B)` 守护的方法是一扇锁住的门，只有当你出示证明 A 等于 B 的徽章时才打开。编译器是徽章办公室——若证明显而易见，它会自动签发徽章；若无法核实，则拒绝。你绝不自己伪造徽章；编译器的徽章办公室是唯一真相源。

## 示例 A：带 =:= 证据的条件方法

```scala
enum Container[A]:
  case Box(value: A)

// flatten 仅在 A 本身是 Container 时可用
def flatten[B](using ev: A =:= Container[B]): Container[B] = this match
  case Box(value) => ev(value) // 将 A 转为 Container[B]

val nested = Container.Box(Container.Box(42))
val flat   = nested.flatten // OK — A 是 Container[Int]

val simple = Container.Box(42)
// simple.flatten // 错误：Cannot prove that Int =:= Container[B]
```

## 示例 B：带 given 的自定义领域证据

```scala
sealed trait Permission
object Permission:
  case object Admin  extends Permission
  case object Reader extends Permission

trait IsAdmin[P <: Permission]
given IsAdmin[Permission.Admin.type] with {}

def deleteAll[P <: Permission]()(using ev: IsAdmin[P]): Unit =
  println("All records deleted")

def withAdmin(): Unit =
  given p: IsAdmin[Permission.Admin.type] = summon
  deleteAll[Permission.Admin.type]() // OK — 找到证据
  // deleteAll[Permission.Reader.type]() // 错误：no given instance of IsAdmin[Reader]
```

## 用例交叉引用

- Evidence 类型通过要求编译期证明前提条件，使非法操作无法表达——见 [invalid-states](../usecases/invalid-states.md)。
- Evidence 守护的方法选择性暴露能力而无需运行时检查——见 [encapsulation](../usecases/encapsulation.md)。
- 状态迁移可要求证据证明当前状态允许该迁移——见 [state-machines](../usecases/state-machines.md)。

# 引用

- [Scala 3 参考 — Context Parameters](https://docs.scala-lang.org/scala3/reference/contextual/using-clauses.html)
- [Scala API — scala.=:=](https://scala-lang.org/api/3.x/scala/=:=.html)
- [Scala API — scala.<:<](https://scala-lang.org/api/3.x/scala/$less$colon$less.html)
- [Scala 3 参考 — Given Instances](https://docs.scala-lang.org/scala3/reference/contextual/givens.html)
- [Scala 3 参考 — summon](https://docs.scala-lang.org/scala3/reference/contextual/using-clauses.html#summoning-instances)
