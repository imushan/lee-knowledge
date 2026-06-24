---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T13-null-safety.md
title: 显式 null（T | Null、.nn、unsafeNulls）
description: 通过 -Yexplicit-nulls 将 Null 从所有引用类型的子类型中移除，要求可空引用显式写作 T | Null，将 NPE 变为编译期错误。
tags:
- T13
- Scala 3
- vibe-types
- explicit-nulls
- 可空性
- 流类型
- 联合类型
- Java 互操作
timestamp: '2026-06-24T12:04:15Z'
---

# 显式 null（`T | Null`、`.nn`、`unsafeNulls`）

## 简介

显式 null 是一个可选特性（通过 `-Yexplicit-nulls` 启用），它修改 Scala 3 的类型层级，使 `Null` 不再是所有引用类型的子类型。`Null` 仅成为 `Any` 与 `Matchable` 的子类型。要表示可空引用，必须显式写作联合类型 `T | Null`，编译器会拒绝在未先证明非空的情况下使用可空值。该特性还提供流敏感的类型收窄、通过 flexible types 实现的 Java 互操作，以及用于渐进迁移的逃生舱 `unsafeNulls`。

## 可表达的约束

**引用类型 `T` 永远不能持有 `null`，除非其类型显式声明 `T | Null`，迫使每一个潜在的 null 解引用在静态层被处理。** 这将 null 安全从运行时关注（NullPointerException）变为编译期保证。

## 最小示例

```scala
//> using option "-Yexplicit-nulls"
// 启用显式 null 后，`Null` 不再是 `String` 的子类型：裸 `null` 被拒绝，
// 可空引用必须写作 `String | Null`。
@main def explicitNullsDemo(): Unit =
  val x: String = null       // error: found Null, required String
  val y: String | Null = null // ok

  // 不能直接对可空类型调用方法：
  // y.trim // 不会编译 —— trim 不是 String | Null 的成员

  // 方式 1：通过 null 检查实现流类型
  if y != null then
    val len = y.trim.length // ok，在该分支中 y: String

  // 方式 2：用 .nn 断言非空
  val z: String = y.nn // 编译通过；若 y 为 null 则运行时抛 NPE
```

## 与其他特性的交互

- **联合类型。** 可空性被编码为 `T | Null`，复用 Scala 3 的一等联合类型机制。所有联合类型规则（模式匹配、子类型）直接适用。参见 [非法状态不可表示](../usecases/invalid-states.md)。
- **流类型。** 编译器执行流敏感收窄：在 `if x != null` 之后，`x` 在 `then` 分支内被精化为非空。这扩展到 `&&`、`||`、`!`、`match` 守卫以及 `assert`。
- **Java 互操作 / flexible types。** 来源于 Java 的引用类型以 *flexible types*（`T?`）加载，边界为 `T | Null <: T? <: T`。这使其可根据上下文作为可空或非空使用，对齐 Scala 的安全保证与 Java。Flexible types 不可显式表达（仅编译器使用）。识别到的 `@NotNull` 注解（如 `@org.jetbrains.annotations.NotNull`）会抑制 null 化。
- **`unsafeNulls` 逃生舱。** 导入 `scala.language.unsafeNulls`（或设置 `-language:unsafeNulls`）允许 `T | Null` 当作 `T` 使用而无需 null 检查，便于从 Scala 2 或未检查的 Scala 3 代码渐进迁移。
- **模式匹配。** 形如 `case _: String =>` 的 match 分支将 `String | Null` 的 scrutinee 收窄为 `String`。参见 [封装](../usecases/encapsulation.md)。
- **可变变量。** 只要局部可变变量不被闭包捕获或修改，其可空性即可被追踪。

## 注意事项与局限

1. **来自未初始化字段的不可靠性。** 类字段在初始化器运行前为 `null`，因此非空字段在构造期间可能临时持有 `null`。`-Wsafe-init` 标志可检测此情况。
2. **不追踪可变变量前缀。** 若 `x` 可变，编译器无法追踪 `x.a` 这类路径的可空性。
3. **无别名推断。** `if s != null && s == s2` 会收窄 `s` 但不会收窄 `s2`，即使两者相等。
4. **可变变量上的 `.nn`。** 直接对可变变量使用 `.nn` 可能在其推断类型中引入未知类型；优先使用 null 检查。
5. **Flexible types 不可显式表达。** 不能在源码中写 `T?`；只有编译器在加载 Java 定义时构造。使用 `-Yno-flexible-types` 可改为获得 `T | Null` 联合类型。
6. **`unsafeNulls` 不等同于普通 Scala。** 返回 `T | Null`（其中 `T` 是类型参数）的泛型 Java 方法即使在 `unsafeNulls` 下仍需 `.nn`，因为编译器无法确认 `T` 是引用类型。

## 用例交叉引用

- 联合类型是基础：`T | Null` 就是 `Union[T, Null]`，参见 [非法状态不可表示](../usecases/invalid-states.md)。
- match 类型与模式匹配与 null 收窄集成，参见 [封装](../usecases/encapsulation.md)。
- Java 互操作模式：用安全的 Scala 门面包装返回可空值的遗留 API，参见 [可空性](../usecases/nullability.md)。
- erased 定义与显式 null 组合可实现完全安全的 null 检查，参见 [可空性](../usecases/nullability.md)。

# 引用

- https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T13-null-safety.md
