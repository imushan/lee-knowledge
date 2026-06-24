---
type: Concept
resource: https://github.com/imushan/scala-learning/blob/main/notes/01-Scala3%E5%AE%8C%E6%95%B4%E5%AD%A6%E4%B9%A0%E6%8C%87%E5%8D%97.md
title: Scala 3 完整学习指南
description: Scala 3 核心特性的系统总览，涵盖新类型系统、枚举与 ADT、上下文抽象、元编程、语法变更及 Scala 2 迁移对照。
tags:
- Scala 3
- 类型系统
- 上下文抽象
- 元编程
- ADT
- 迁移
timestamp: '2026-06-24T10:15:51Z'
---

# Scala 3 完整学习指南

基于 Scala 3 官方参考文档整理的系统性总览，适用于 Scala 2 开发者迁移及 Scala 3 新手。上下文抽象部分另有更偏架构实践的深度篇，见 [Scala 3 上下文抽象与现代架构设计](scala3_context_abstraction.md)。

---

## 新类型系统

### 交集类型 (Intersection Types)

`A & B` 表示同时满足 `A` 和 `B` 的值，是 Scala 2 `A with B` 的替代。`&` 可交换，成员是两类型成员的并集，重叠成员的类型为两者交集。

```scala
trait Resettable { def reset(): Unit }
trait Growable[T] { def add(t: T): Unit }

def f(x: Resettable & Growable[String]) =
  x.reset()
  x.add("first")
```

### 联合类型 (Union Types)

`A | B` 表示值为 `A` 或 `B` 之一，是交集类型的对偶。默认 `if/else` 会把分支推断为共同超类型；对 `transparent trait` 标注的类型则保留联合类型。

```scala
def help(id: UserName | Password) =
  id match
    case UserName(name) => lookupName(name)
    case Password(hash) => lookupPassword(hash)
```

### 类型 Lambda (Type Lambdas)

无需单独定义类型，直接内联高阶类型构造器：`[X, Y] =>> Map[Y, X]`。类型参数可带边界但不能带变体注解。注意它与**多态函数类型** `[A] => List[A] => List[A]` 的区别——前者是类型层面，后者是值层面。

### 匹配类型 (Match Types)

根据 scrutinee 类型在**编译时**缩减为右侧类型之一，可递归，可带边界。

```scala
type Elem[X] = X match
  case String      => Char
  case Array[t]    => t
  case Iterable[t] => t

Elem[Array[Int]] =:= Int
```

可据此写出返回类型被精确推断的依赖方法：

```scala
def leafElem[X](../x: X.md): LeafElem[X] = x match
  case x: String   => x.charAt(0)
  case x: Array[t] => leafElem(x(0))
```

### 依赖函数类型与多态函数类型

- **依赖函数类型**：返回类型依赖于参数值，`def extractKey(e: Entry): e.Key = e.key`。
- **多态函数类型**：接受类型参数的函数值，可作为参数传递，如 `[A] => List[A] => List[A]`。

---

## 枚举与代数数据类型 (ADTs)

Scala 3 的 `enum` 同时覆盖传统枚举与 ADT。

```scala
enum Color(val rgb: Int):
  case Red   extends Color(0xFF0000)
  case Green extends Color(0x00FF00)
  case Blue  extends Color(0x0000FF)
```

内置成员：`ordinal`、`valueOf`、`values`、`fromOrdinal`。`enum` 可带自定义方法（如 `Planet` 计算表面重力），可与 Java 枚举互操作（`enum Color extends Enum[Color]`）。

ADT 形态：

```scala
enum Option[+T]:
  case Some(x: T)
  case None
```

变体规则：协变类型参数在 `extends` 子句中最小化，逆变类型参数最大化。

---

## 上下文抽象

### Given 实例

定义"规范值"供上下文参数合成。支持命名 / 匿名（编译器合成 `given_Ord_Int` 之类名称，公开库应用命名以保二进制兼容）/ 别名三种形态。无参无条件 given 按需初始化，别名 given 仅作转发器，条件 given 每次引用创建新实例。

### Using 子句

解决长调用链的参数透传问题。`def max[T](../x: T, y: T.md)(using ord: Ord[T]): T`，调用时可省略。`summon[T]` 召唤实例（Scala 2 `implicitly` 的替代）。

### 上下文边界

上下文参数的简写，常用于类型类建模。`def maximum[T: Ord](../xs: List[T].md)` 展开为 `(using Ord[T])`。Scala 3.6+ 的命名上下文边界 `T: Ord as ord` 可直接拿到实例名。

### 扩展方法

定义后为已有类型追加方法，是 Scala 2 `implicit class` 的替代，零运行时开销。

```scala
extension (c: Circle)
  def circumference: Double = c.radius * math.Pi * 2
```

支持泛型扩展、运算符扩展、带上下文边界的扩展（`extension [T: Numeric](../x: T.md)`）。

### 类型类与派生

类型类是参数化 trait + 一组通用操作。`derives Eq, Ordering, Show` 可基于 `Mirror` 自动生成 given 实例，避免手写样板。

### 多宇宙相等性 (Multiversal Equality)

通过 `CanEqual[-L, -R]` 类型类实现类型安全的相等性，防止跨类型比较。`import scala.language.strictEquality` 启用严格模式，`class T derives CanEqual` 派生。

---

## 元编程

### Inline

`inline` 保证定义在使用点内联展开。支持 inline 值（常量）、inline 方法、递归 inline（如 `power` 展开为无循环代码）、inline 参数、`transparent inline`（保留精确静态类型）、inline 匹配。

### 编译时操作

`scala.compiletime` 提供：`constValue` / `constValueOpt`、`erasedValue`、`error`、`summonFrom`，以及 `scala.compiletime.ops.int` 的类型级算术（`3 * 5 = 15`）。

### 宏

基于**引号与拼接**（`'{..}` 引用 / `${..}` 拼接），类型安全且卫生。支持抽象类型处理（`Type[T]`）、引用模式匹配（`case '{ power($y, $m) }`）、类型模式（`case '[List[t]]`）。

---

## 其他新特性

- **Trait 参数**：`trait Greeting(val name: String)`。三条规则约束参数传递（父类是否已继承决定子类能否再传）。
- **透明 Trait** (`transparent trait`)：阻止类型拓宽，常配合联合类型使用。
- **Opaque 类型别名**：零开销类型抽象，带边界时可建模子集关系（如 `Permission <: Permissions`）。
- **Export 子句**：为对象的选定成员定义别名转发，实现"组合优于继承"，支持重命名与排除。
- **命名元组**（实验性）：`(name = "Alice", age = 25)`。
- **缩进语法**：可选大括号、`end` 标记、`if/then`、多行 `for ... do`。
- **顶层定义**：无需包对象即可在文件顶层定义类、方法、值。

---

## 变更的特性

- **类型推断**：更精确，倾向保留具体类型。
- **隐式机制重塑**：`implicit` → `given`/`using`，`implicitly` → `summon`，`implicit def` → `given Conversion`，`implicit class` → `extension`。
- **模式匹配**：更精确的类型匹配（`case _: List[t]` 中 `t` 为类型变量）。
- **移除项**：`DelayedInit`、Scala 2 宏、存在类型、`do-while`、过程语法、包对象、早期初始化器、22 参数限制、XML 字面量、符号字面量、自动应用、`private[this]`、`_` 初始化器。

---

## 最佳实践

- **类型系统**：联合类型替代简单 `Either`；匹配类型做类型级计算；Opaque 做领域抽象。
- **上下文抽象**：given 做类型类与依赖注入；extension 增强现有类型；命名上下文边界提高可读性。
- **元编程**：inline 做性能与编译时配置；transparent inline 做精确推断；宏做复杂代码生成。
- **语法风格**：缩进语法降嵌套；`end` 标记大块；export 替代继承做组合。

---

# Citations

- [01-Scala3完整学习指南.md (imushan/scala-learning)](https://github.com/imushan/scala-learning/blob/main/notes/01-Scala3%E5%AE%8C%E6%95%B4%E5%AD%A6%E4%B9%A0%E6%8C%87%E5%8D%97.md)
- [Scala 3 官方文档](https://docs.scala-lang.org/scala3/)
- [Scala 3 参考文档](https://docs.scala-lang.org/scala3/reference/index.html)
- [Scala 2 to Scala 3 迁移指南](https://docs.scala-lang.org/scala3/guides/migration/compatibility-classpath.html)
