---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T40-type-lambdas.md
title: 类型 Lambda（Type Lambdas）
description: Scala 3 中的匿名高阶类型表达式，允许在类型位置直接部分应用或重排类型构造器参数，无需命名别名。
tags:
- 类型 Lambda
- 高阶类型
- 类型构造器
- 部分应用
- T40
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:06:49Z'
---

# 类型 Lambda（Type Lambdas，`[X] =>> F[X]`）

> **引入版本：** Scala 3.0

## 简介

类型 Lambda 是 Scala 3 中的匿名高阶类型表达式，允许在类型位置直接部分应用或重排类型构造器参数，无需引入命名类型别名。其语法写作 `[X] =>> F[X]`，是值级 lambda `(x) => f(x)` 在类型层面的对应物。类型 Lambda 消除了 Scala 2 库中常见的"类型 Lambda 技巧"（通过结构 refinement 模拟）。

## 可表达的约束

**类型 Lambda 允许内联抽象类型构造器，表达高阶类型关系（如 `Functor`、`Monad` 或任何 `* -> *` 抽象），而无需辅助类型别名。** 这在类型类期望一元类型构造器、而目标类型是二元类型（例如 `Either[E, _]`）或需要重排类型参数时尤为关键。

## 最小示例

```scala
// 部分应用二元类型构造器：
// Map[K, V] 的 kind 为 (*, *) -> *，但 Functor 期望 * -> *
type MapWithKey[K] = [V] =>> Map[K, V]

// 等价于命名别名，但可内联使用：
trait Functor[F[_]]:
  extension [A](fa: F[A])
    def map[B](f: A => B): F[B]

// 将类型 Lambda 直接作为类型参数使用：
given eitherFunctor[E]: Functor[[A] =>> Either[E, A]] with
  extension [A](fa: Either[E, A])
    def map[B](f: A => B): Either[E, B] = fa.map(f)
```

## 与其他特性的交互

- **Given 实例。** 类型 Lambda 最常用于为期望一元类型构造器但目标类型有多个参数的类型类提供 given 实例。参见用例 [编译期计算](../usecases/compile-time.md)。
- **Context bounds。** 可以在 context bounds 内使用类型 Lambda：`[F[_]: [G[_]] =>> Monad[G]]`，不过通常命名别名更清晰。
- **Match types。** 类型 Lambda 可出现在 match type 体中，实现计算型高阶类型。参见 [match-types](match-types.md)。
- **多态函数类型。** 类型 Lambda 在类型层面定义类型（`=>>`），多态函数类型在值层面定义多态值（`=>`）。二者互补：类型 Lambda 应用于类型表达式，多态函数应用于值表达式。参见用例 [效果追踪](../usecases/effect-tracking.md)。
- **型变。** 类型 Lambda 的类型参数不能带 `+` 或 `-` 型变注解。型变只在命名类型定义（`type`、`trait`、`class`）上声明。
- **类型边界。** 类型 Lambda 的类型参数可以有上界和下界（例如 `[X <: Comparable[X]] =>> Set[X]`）。

## 注意事项与局限

1. **不能加型变注解。** 无法写 `[+X] =>> F[X]`。型变必须在命名类型定义上声明。当型变影响子类型关系时，可能不得不引入类型别名。
2. **可读性。** 深层嵌套的类型 Lambda 很快会变得难以阅读。对超过一层部分应用的场景，优先使用命名 `type` 别名。
3. **非值层构造。** 类型 Lambda 纯粹存在于类型层面，不能被实例化、作为值传递或在运行时被模式匹配。需要值层多态时，请使用多态函数类型（`[A] => ...`）。
4. **高阶 kind 影响可读性。** 类型 Lambda 的参数本身可以是高阶的——`[F[_[_]]] =>> ...` 可以编译——这里没有 kind 限制。唯一的真实警告是可读性：此类嵌套 kind 签名很快会难以理解。
5. **擦除。** 与所有类型层构造一样，类型 Lambda 在运行时被擦除，没有运行时表示，无法被反射。

## 用例交叉引用

- 类型 Lambda 可在 match type 体内产生类型 Lambda 形状的结果，用于计算型高阶类型。参见用例 [状态机](../usecases/state-machines.md)。
- 多态函数类型是类型 Lambda 的值层对应物。参见用例 [效果追踪](../usecases/effect-tracking.md)。
- Given 实例经常使用类型 Lambda，将多参数类型构造器适配为一元类型类形状。参见用例 [编译期计算](../usecases/compile-time.md)。

# 引用

- 原始来源：[T40-type-lambdas.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T40-type-lambdas.md)
