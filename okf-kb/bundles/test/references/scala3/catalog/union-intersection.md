---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T02-union-intersection.md
title: 联合类型与交叉类型（A | B / A & B）
description: 以类型组合子表达多类型的析取或合取，无需引入共同父类型即可限定接受值或同时要求多种能力。
tags:
- T02
- Scala 3
- vibe-types
- 联合类型
- 交叉类型
- transparent trait
timestamp: '2026-06-24T12:03:44Z'
---

# 联合类型与交叉类型（`A | B` / `A & B`）

> **引入版本：** Scala 3.0

## 简介

联合类型与交叉类型是 Scala 3 中一等公民的类型组合子，无需共享父类型或新建 trait 即可表达类型的析取与合取。联合类型 `A | B` 表示值为 `A` 或 `B`；交叉类型 `A & B` 表示值同时为 `A` 和 `B`。二者共同取代了 Scala 2 的复合类型（`with`），并在表达备选项时免除了临时包装层级。

## 可表达的约束

**联合类型可以声明"该值是若干类型之一"，而无需引入共同父类型；交叉类型可以声明"该值同时满足若干类型约束"。** 这是核心对偶：`|` 拓宽可接受值的集合，`&` 通过要求组合能力来收窄它。

## 最小示例

```scala
// 交叉类型：组合能力
trait Resettable:
  def reset(): Unit

trait Growable[T]:
  def add(t: T): Unit

def f(x: Resettable & Growable[String]) =
  x.reset()
  x.add("first")

// 联合类型：无需共同父类型即可接受备选
case class UserName(name: String)
case class Password(hash: Int)

def help(id: UserName | Password): String = id match
  case UserName(n) => s"user: $n"
  case Password(h) => s"pass: $h"
```

## 与其他特性的交互

- **模式匹配。** 联合类型天然与 `match` 配合做类型收窄；当联合成员为密封或枚举时，编译器检查穷尽性。
- **交换律。** 两个运算符均可交换：`A & B =:= B & A` 且 `A | B =:= B | A`。
- **分配律。** 交叉对联合可分配：`A & (B | C) =:= (A & B) | (A & C)`。
- **成员合并（交叉）。** 当 `&` 两侧定义同名成员时，该成员在交叉类型中的类型是两侧成员类型的交叉。对协变类型构造子会自然简化（如 `List[A] & List[B]` 变为 `List[A & B]`）。
- **类型推断（联合）。** 除非显式标注类型或共同父类型是 `transparent` trait，否则编译器不推断联合类型。未标注时 `if cond then a else b` 会被拓宽到最小非透明公共父类型。
- **透明 trait。** 将父 trait 声明为 `transparent` 会让编译器推断联合类型而非拓宽到父类型。
- **match 类型。** 联合与交叉类型可作为 match 类型的被审视项或模式类型出现。
- **given / 类型类。** 可为交叉类型提供 given 实例，以要求组合证据。

## 注意事项与局限

1. **联合类型默认不被推断。** 写 `val x = if cond then a else b`（`a: A`、`b: B`）得到的是 LUB（最小上界），而非 `A | B`，除非共同父类型为 `transparent` 或显式标注类型。
2. **联合类型上无成员。** 不能直接对 `A | B` 调用方法（除非 `A` 与 `B` 通过共同父类型共享该成员），需先经模式匹配或类型测试收窄。
3. **具体类型交叉为空。** `String & Int` 是空类型（无值 inhabited），编译器不会警告，只是无法构造值。
4. **顺序无关但展示有异。** `A & B` 与 `B & A` 是同一类型，但错误信息与 IDE 提示可能展示顺序不同。
5. **交叉取代 `with`。** Scala 2 的 `A with B` 类型语法已被弃用，改用 `A & B`；语义不同：`&` 可交换，`with` 不可。

## 用例交叉引用

- match 类型可在联合/交叉被审视项上分支。
- 依赖函数类型可返回交叉类型结果，使路径依赖成员组合多种能力。
- 可为交叉类型定义 given 实例以要求组合证据（如 `given [T: Ord & Show]`）。
- context 函数可将联合类型用作参数类型以接受备选能力提供者。

# 引用

- [T02-union-intersection.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T02-union-intersection.md)
