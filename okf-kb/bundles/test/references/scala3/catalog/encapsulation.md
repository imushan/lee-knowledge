---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T21-encapsulation.md
title: 封装修饰符（open / export / transparent trait）
description: open 限定谁可继承、export 控制以委托暴露哪些成员、transparent 决定哪些父类型出现在推导类型中，三者共同表达可扩展性与封装契约。
tags:
- T21
- Scala 3
- vibe-types
- open
- export
- transparent trait
- 封装
- 委托
timestamp: '2026-06-24T12:04:01Z'
---

# 封装修饰符（open / export / transparent trait）

**起始版本：** Scala 3.0 | **最新变更：** Scala 3.4（`open` 警告变为默认）

## 简介

Scala 3 提供三个互补的特性来控制类与 trait 如何组合并在类型系统中呈现。**`open` 修饰符** 显式声明一个类是为在源文件之外被子类扩展而设计的。**export 子句** 创建转发别名，暴露被组合对象的选定成员，以委托取代继承实现复用。**透明 trait** 以 `transparent` 修饰符标记，使编译器将其从推导类型中省略，让作为实现细节的混入对调用者不可见。

## 可表达的约束

**`open` 控制 _谁可以继承_ 一个类；`export` 控制 _通过委托暴露哪些成员_；`transparent` 控制 _哪些父类型出现在推导类型中_。** 三者结合，让库作者能够表达可扩展性契约（open/final/默认）、用同样简洁的组合取代基于继承的复用，并防止实现型混入泄漏到公开 API。

## 最小示例

### `open` 修饰符

```scala
// Library code
open class Writer[T]:
  def send(x: T): Unit = println(x)
  def sendAll(xs: T*): Unit = xs.foreach(send)

// Client code -- OK because Writer is open
class EncryptedWriter[T] extends Writer[T]:
  private def encrypt(x: T): T = x // stand-in for real encryption
  override def send(x: T): Unit = super.send(encrypt(x))
```

若无 `open`，从另一个文件扩展 `Writer` 会产生警告，除非作用域内有 `import scala.language.adhocExtensions`。

### export 子句

```scala
type BitMap = Array[Byte]
class Printer:
  def print(bits: BitMap): Unit = ???
  def status: List[String] = ???

class Scanner:
  def scan(): BitMap = ???
  def status: List[String] = ???

class Copier:
  private val printUnit = new Printer
  private val scanUnit  = new Scanner
  export scanUnit.scan                       // alias: def scan(): BitMap = scanUnit.scan()
  export printUnit.{status as _, *}          // all of printUnit except status
  def status: List[String] = printUnit.status ++ scanUnit.status
```

导出的别名是 `final` 的，可以实现抽象成员，并忠实复制类型/值参数。

### transparent trait

```scala
transparent trait Impl   // implementation-only mixin
trait Kind
object Var extends Kind, Impl
object Val extends Kind, Impl
val cond = true
val x = Set(if cond then Val else Var)
// inferred type: Set[Kind] (Impl is dropped)
```

若没有 `transparent`，推导类型会是 `Set[Kind & Impl]`。

## 与其他特性的交互

| 特性 | 交互方式 |
|---|---|
| **`sealed` / `final`** | `open` 与两者都互斥。既非 open 也非 sealed 的类近似 sealed，但允许在带 language import 时临时扩展。`final` 禁止一切扩展。 |
| **`abstract` / trait** | trait 与抽象类总是 open；加 `open` 是冗余的。 |
| **不透明类型** | export 子句可以转发不透明类型的伴生，从而在顶层构建门面（facade）模式。 |
| **扩展方法** | export 子句可出现在 `extension` 块内部，从辅助类创建扩展方法别名。 |
| **联合类型** | 当从某联合拓宽出的所有父类型都是 transparent 时，该联合会保持不拓宽（例如 `Val | Var` 而非 `Any`）。 |
| **Given 实例** | export 使用 `given` 选择子专门别名 given 实例，镜像 import 语法。 |
| **类型推导** | 根类（`Any`、`AnyVal`、`Matchable`、`Product`、`Serializable`）内置即为 transparent，因此 `if c then 1 else "hi"` 推导为 `Int | String` 而非 `Any`。 |

## 注意事项与局限

- **导出别名是 final 的。** 它们不能被重写，也不能重写基类中的具体成员（缺少 `override` 修饰符），但 _可以_ 实现抽象成员。
- **禁止从包做通配导出。** 通配或 given 选择子的限定路径不能是包（增量编译无法追踪）。
- **export 求值顺序。** 所有 export 限定路径在任何别名作为成员录入之前就会被类型化。因此一个 export 子句不能引用同一类中另一个 export 子句引入的别名。
- **transparent trait 的单实例规则。** 单独出现的某个 transparent trait _不会_ 被拓宽到 `Any`。只有当它与其他非透明类型一起出现在交集里时才会被省略。
- **临时扩展警告** 自 Scala 3.4 起默认开启：从不同文件扩展非 open 类时会发出。
- **块中的 export。** export 子句可出现在类中和顶层，但不能作为块内的语句。

## 用例交叉引用

- 用 `open` 类与文档化的扩展契约定义可扩展插件 API，见 [非法状态构造](../usecases/invalid-states.md)。
- 在聚合服务中用 export 子句实现组合优于继承，见 [效应追踪](../usecases/effect-tracking.md)。
- 用 transparent trait 把 `Product`/`Serializable` 排除在公开 ADT 类型之外，见 [可空性](../usecases/nullability.md)。
- 在包顶层重新导出选定定义的门面模块，见 [序列化](../usecases/serialization.md)。

# 引用

- 原始资料：https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T21-encapsulation.md
