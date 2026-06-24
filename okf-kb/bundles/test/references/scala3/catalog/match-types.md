---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T41-match-types.md
title: Match Types（类型级模式匹配）
description: Scala 3 中的类型级构造，根据 scrutinee 类型的结构归约到多个右侧类型之一，实现类型级条件选择与递归计算。
tags:
- Match Types
- 类型级计算
- 类型级模式匹配
- 递归类型
- T41
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:06:49Z'
---

# Match Types（类型级模式匹配）

> **引入版本：** Scala 3.0

## 简介

Match type 是 Scala 3 中的类型级构造，根据 scrutinee 类型的结构归约到多个右侧类型之一。语法写作 `X match { case P1 => T1; ... ; case Pn => Tn }`，执行类型级模式匹配，类似值层的 `match` 表达式。Match types 支持条件类型选择与递归类型计算，无需宏或隐式解析技巧。

## 可表达的约束

**Match types 允许表达类型级计算："给定一个输入类型，通过模式匹配选择或计算出合适的输出类型。"** 这使得依赖类型方法（返回类型由参数类型决定）、对元组等结构的类型级递归，以及此前需要宏才能实现的条件类型关系成为可能。

## 最小示例

```scala
// 基础：提取容器的元素类型
type Elem[X] = X match
  case String     => Char
  case Array[t]   => t
  case Iterable[t] => t

// 使用：
val c: Elem[String]       = 'a'    // Char
val i: Elem[Array[Int]]   = 42     // Int
val f: Elem[List[Float]]  = 3.14f  // Float

// 递归：深入到叶子元素类型
type LeafElem[X] = X match
  case String     => Char
  case Array[t]   => LeafElem[t]
  case Iterable[t] => LeafElem[t]
  case AnyVal     => X

// 以 match type 作为返回类型的依赖类型方法
def leafElem[X](x: X): LeafElem[X] = x match
  case x: String   => x.charAt(0)
  case x: Array[t] => leafElem(x(0))
  case x: Iterable[t] => leafElem(x.head)
  case x: AnyVal   => x
```

## 与其他特性的交互

- **依赖方法。** Match type 是编写返回类型依赖参数类型的方法的主要机制。编译器在特定条件下（无 guard、带类型模式、用例数相同）验证值层 match 与类型层 match 同构。参见用例 [效果追踪](../usecases/effect-tracking.md)。
- **递归类型。** Match type 可以自引用递归。声明上界（`type Concat[Xs <: Tuple, Ys <: Tuple] <: Tuple = ...`）有助于编译器验证递归调用类型正确。
- **元组操作。** 标准库广泛使用 match types 实现元组操作（`Concat`、`Zip`、`Map`、`Head`、`Tail` 等）。
- **联合/交集类型。** Match type 可以对联合或交集类型分派，但归约要求能证明 scrutinee 与被拒绝的模式不相交。参见用例 [非法状态](../usecases/invalid-states.md)。
- **Given 实例。** Match type 可用于 given 定义的返回类型，使类型类实例行为因类型而异。参见用例 [编译期计算](../usecases/compile-time.md)。
- **子类型关系。** Match type 与其归约结果（能归约时）互为子类型。即使无法归约，match type 也遵循其声明的上界。

## 注意事项与局限

1. **不总能归约。** 当编译器无法证明 scrutinee 匹配某个用例或与之不相交时，match type 保持"卡住"（未归约）状态。抽象类型参数常导致卡住的 match type。
2. **不相交性证明受限。** 编译器依赖类的单继承、final 性、不同的常量类型和不同的单例路径，无法推理任意用户定义的不相交性。
3. **不变位置。** Match type 中所有类型位置（scrutinee、模式、体）都被视为不变，与外围类型构造器的型变无关。
4. **无 guard。** Match type 用例不能带 guard，所有分派必须仅基于类型模式的结构。
5. **终止性。** 递归 match type 可能导致无限归约循环。编译器通过子类型关系中的环检测发现此类情况并报"recursion limit exceeded"错误。
6. **值层镜像要求。** 要让值层 `match` 使用 match type 类型化，模式必须是带类型模式（`case x: T => ...`），不能有 guard，且用例数量和顺序必须完全一致。
7. **不收窄约束。** 与 Haskell 的 type families 不同，match type 归约不会收紧底层类型约束。外围作用域中的类型变量不会因模式匹配而被 unify。

## 用例交叉引用

- 联合与交集类型可作为 match type 的 scrutinee 实现条件分派。参见用例 [非法状态](../usecases/invalid-states.md)。
- 类型 Lambda 可出现在 match type 体内，产生计算型高阶类型。参见 [type-lambdas](type-lambdas.md)。
- 依赖函数类型使用 match type 作为返回类型，实现类型安全的依赖返回。参见用例 [效果追踪](../usecases/effect-tracking.md)。
- Given 实例可借助 match type 按条件提供类型类证据。参见用例 [编译期计算](../usecases/compile-time.md)。

# 引用

- 原始来源：[T41-match-types.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T41-match-types.md)
