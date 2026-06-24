---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T44-changed-dropped.md
title: 变更与移除的特性
description: Scala 3 相对 Scala 2 的类型系统行为变更与移除：改进的类型推断、新的隐式解析算法、移除存在类型、限制抽象类型上的类型投影。
tags:
- 类型推断
- 隐式解析
- 存在类型
- 类型投影
- NotGiven
- 变更
- T44
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:06:50Z'
---

# 变更与移除的特性：类型推断、隐式解析、存在类型、类型投影

> **引入版本：** Scala 3.0 | **最新变更：** Scala 3.5（given 消歧规则 9）、Scala 3.6（递归 given 规避规则 10）

## 简介

Scala 3 刻意变更了若干继承自 Scala 2 的类型系统行为，并移除了被证明不健全或过于复杂的特性。**类型推断**通过更好的 GADT 支持和新算法得到改进。**隐式解析**使用新搜索算法，具有精炼的消歧、正确的歧义传播和递归 given 防护。**存在类型**（`forSome`）被完全移除。**通用类型投影**（抽象类型上的 `T#A`）被限制为仅允许具体前缀。这些变更共同使类型系统更可预测、更健全、更利于工具化。

## 可表达的约束

**通过收紧推断规则、修复隐式解析异常、移除不健全特性，Scala 3 确保编译器推断的类型和选择的隐式一致、无歧义，且摆脱了困扰 Scala 2 的健全性漏洞。** 失去的约束（存在类型、抽象类型投影）被更安全的替代方案（路径依赖类型、通配符精炼类型）取代。

## 最小示例

```scala
// --- 隐式解析：嵌套现在起作用 ---
def f(implicit i: C) = ???
def g(implicit j: C) = ???
implicitly[C] // 解析为 j（嵌套更深），而非歧义错误

// --- 隐式解析：歧义传播 ---
class A; class B extends C; class C
implicit def a1: A = ???
implicit def a2: A = ???
implicit def b(implicit a: A): B = ???
implicit def c: C = ???
// implicitly[C] 歧义：b(a1) 和 b(a2) 都比 c 更优，但彼此不分伯仲。
// Scala 2 本会选 c。

// --- NotGiven 替代"借歧义取反"技巧 ---
import scala.util.NotGiven
def onlyIfNoOrdering[T](x: T)(using NotGiven[Ordering[T]]): String =
  "no ordering available"

// --- 移除：存在类型 ---
// Scala 2: List[T] forSome { type T } // 不再编译
// Scala 3: List[?] // 通配符，视为精炼类型

// --- 移除：抽象类型上的通用类型投影 ---
// Scala 2: T#A where T is abstract // 不健全，不再编译
// Scala 3: 仅允许具体前缀
class Outer { class Inner }
type Valid = Outer#Inner // OK：Outer 是具体的
// type Invalid = T#Inner // 错误：若 T 是抽象的
```

## 与其他特性的交互

- **显式 given 类型（规则 1）。** 类或对象层级的隐式 val 和 def 必须有显式声明的返回类型。这提升编译速度（索引前无需推断类型）并防止意外的隐式宽化。块内局部隐式豁免。
- **基于嵌套的优先级（规则 2）。** 当两个同类型隐式在作用域内且其中一个嵌套更深时，更内层的胜出。Scala 2 将此视为歧义。这消除了旧的"遮蔽"失败模式。
- **排除包前缀（规则 3）。** 包级 given 不再位于子包中定义的类型的隐式作用域内。仅伴生对象和显式 import 贡献。这使隐式作用域更可预测。
- **歧义传播（规则 4）。** 隐式搜索递归步骤中发现的歧义现在传播给调用者，而非被静默丢弃。这防止了 Scala 2 中子查询歧义导致回退到次优替代的意外行为。
- **`NotGiven[Q]`（规则 4 推论）。** `scala.util.NotGiven` 类型替代了 Scala 2 中利用歧义实现取反隐式搜索的技巧。`NotGiven[Q]` 当且仅当找不到类型 `Q` 的隐式时成功。
- **发散作为软失败（规则 5）。** 发散的隐式搜索被视为普通失败，允许尝试其他候选，而非中止整个搜索。
- **Given 消歧（规则 9）。** 自 Scala 3.5 起，当多个 given 匹配期望类型时，优先选择**最一般**的（而非重载解析中的最特定）。用 `-source:3.5-migration` 编译以查看行为变更警告。
- **递归 given 规避（规则 10）。** 在 `-source:future` 下，隐式解析丢弃导致回到当前正在检查的 given 定义的搜索结果，防止如 opaque type 伴生中 `given Ordering[Price] = summon[Ordering[BigDecimal]]` 的无限循环 given。
- **路径依赖类型替代存在类型。** 任何此前需要 `forSome` 的用例都可用路径依赖类型、通配符（精炼类型）或 match types 表达。参见用例 [效果追踪](../usecases/effect-tracking.md)。
- **具体类型投影。** `T#A` 仅当 `T` 是具体类时允许。对抽象类型，使用路径依赖类型（某值 `x: T` 的 `x.A`）。参见用例 [效果追踪](../usecases/effect-tracking.md)。

## 注意事项与局限

1. **取反隐式的迁移。** 依赖基于歧义的取反模式的 Scala 2 代码必须改写为 `NotGiven`。`-source:3.0-migration` 标志有助于识别这些情况。
2. **隐式作用域收窄。** 从隐式作用域中移除包前缀意味着某些依赖包级隐式的 Scala 2 代码将停止编译。将此类隐式移入伴生对象或显式 import。
3. **传名参数优先级取消（规则 6）。** Scala 2 给带传名参数的隐式转换更低优先级。Scala 3 平等对待，因此此前同时有 `conv(x: Int)` 和 `conv(x: => Int)` 的可用代码可能变歧义。
4. **存在类型近似。** 读取含存在类型的 Scala 2 classfile 时，Scala 3 尽力近似并发警告。某些类型可能无法精确往返。
5. **类型投影限制。** 对抽象 `T` 弃用 `T#A` 破坏了类型级编码技巧（如 SKI 组合子演算编码）。推荐替代是路径依赖类型，需要值层见证。
6. **Given 偏好反转。** given 消歧中从"最特定"到"最一般"的转变（规则 9）可能静默改变被选中的实例。升级到 Scala 3.5+ 时始终用迁移警告编译。

## 用例交叉引用

- 路径依赖类型：存在类型和抽象类型投影的主要替代。参见用例 [效果追踪](../usecases/effect-tracking.md)。
- Given 实例：所有隐式解析变更直接影响类型类派生与 given 搜索。参见用例 [编译期计算](../usecases/compile-time.md)。
- 上下文函数：隐式解析变更同样适用于 `?=>` 参数合成。参见用例 [状态机](../usecases/state-machines.md)。
- 模块化：`tracked` 参数减少了对部分由类型投影限制催生的 `Aux` 模式变通的需求。参见用例 [可扩展性](../usecases/extensibility.md)。

# 引用

- 原始来源：[T44-changed-dropped.md](https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T44-changed-dropped.md)
