---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T54-functor-applicative-monad.md
title: Functor、Applicative 与 Monad
description: Scala 3 中用于表达上下文计算的 Functor、Applicative、Monad 抽象层级，以及 cats 提供的类型类实例与
  for 推导的脱糖机制。
tags:
- Functor
- Applicative
- Monad
- 高阶类型
- 类型类
- for 推导
- cats
- T54
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:04:04Z'
---

# Functor、Applicative 与 Monad

## 简介

Functor、Applicative 与 Monad 构成了处理上下文中值（`F[_]`）的核心抽象层级。

- **Functor** 提供 `map`，用于在不改变上下文形状的前提下变换内部值。
- **Applicative** 在 Functor 之上扩展了 `pure`（将普通值提升到上下文）和 `ap`（在上下文中应用一个被上下文包裹的函数到被上下文包裹的值）。
- **Monad** 在 Applicative 之上扩展了 `flatMap`，用于串联每一步都依赖上一步结果的计算。

Scala 标准库对这套抽象的内置支持有限：`Option`、`List`、`Either`、`Future` 都提供了 `map` 和 `flatMap` 方法，for 推导会脱糖为 `flatMap` / `map` / `withFilter` 链。但标准库中没有 `Functor`、`Applicative`、`Monad` trait。**cats** 库提供了完整的层级以及合法的类型类实例，支持对任意 monadic effect 进行泛型编程。

> **Since:** Scala 3.0（for 推导自 Scala 2 起；cats 类型类层级自 cats 1.x 起）

## 可表达的约束

**基于 `Functor[F]`、`Applicative[F]` 或 `Monad[F]` 约束编写的代码只能使用该抽象层级提供的操作，保证声明了所需的最小能力，并且实现满足相关定律（identity、composition、associativity）。**

## 最小示例

```scala
import cats.Monad
import cats.syntax.all.*

def combine[F[_]: Monad](fa: F[Int], fb: F[Int]): F[Int] =
  for
    a <- fa
    b <- fb
  yield a + b

// 适用于任意 Monad：Option、List、Either、IO……
val optResult  = combine(Option(1), Option(2))            // Some(3)
val listResult = combine(List(1, 2), List(10, 20))        // List(11, 21, 12, 22)
```

## for 推导（Scala 的 do-notation）

Scala 的 `for` 推导会脱糖为 `flatMap` / `map` / `withFilter` 链，是 Scala 中编写 monadic 代码的主要方式，让顺序依赖计算读起来像命令式代码。

```scala
def findUser(id: Long): Option[String]   = Some("alice")
def getEmail(user: String): Option[String] = Some(s"$user@example.com")
def sendWelcome(email: String): Option[Unit] = Some(())

val id = 1L

// 这段 for 推导：
for
  user  <- findUser(id)
  email <- getEmail(user)
  _     <- sendWelcome(email)
yield email

// 等价脱糖为：
findUser(id).flatMap(user =>
  getEmail(user).flatMap(email =>
    sendWelcome(email).map(_ => email)
  )
)
```

**关键脱糖规则：**

- `<-` 绑定 → `flatMap`（最后一个使用 `map`）
- `if` 守卫 → `withFilter`
- `=` 绑定 → 链内的值定义
- `yield` → 最终值的 `map` 表达式

for 推导适用于**任何**具备 `flatMap` 和 `map` 方法的类型，不只是集合。`Option`、`Either`、`Future`、`IO` 以及任意 cats `Monad` 实例都透明可用。

```scala
case class Order(total: Double)
case class Payment(amount: Double)
case class Receipt(id: String)

def findOrder(orderId: String): Either[Error, Order]    = Right(Order(42.0))
def chargeCard(total: Double): Either[Error, Payment]   = Right(Payment(total))
def generateReceipt(order: Order, payment: Payment): Either[Error, Receipt] =
  Right(Receipt("r-1"))

// 错误处理读起来像命令式代码
def processOrder(orderId: String): Either[Error, Receipt] =
  for
    order   <- findOrder(orderId)
    payment <- chargeCard(order.total)
    receipt <- generateReceipt(order, payment)
  yield receipt
```

## 与其他特性的交互

| 特性 | 组合方式 |
|------|----------|
| **for 推导** | `for { a <- fa; b <- fb } yield expr` 脱糖为 `fa.flatMap(a => fb.map(b => expr))`，相当于 Scala 的 do-notation。 |
| **类型类 / givens**（见 [type-classes](type-classes.md)） | `Functor`、`Applicative`、`Monad` 是通过 `given` 实例提供的类型类；`[F[_]: Monad]` 是一个要求证据的上下文绑定。 |
| **类型 lambda**（见 [generics-bounds](generics-bounds.md)） | 当 `F` 有多个类型参数（如 `Either[E, A]`）时，用类型 lambda `[A] =>> Either[E, A]` 将其适配为 Monad 要求的 `F[_]` 形状。 |
| **Monad transformers**（见 [monad-transformers](monad-transformers.md)） | `EitherT`、`OptionT`、`StateT` 堆叠 monadic effect，每一层都要求底层 `F` 是 Monad。 |
| **Tagless final**（见 [tagless-final](tagless-final.md)） | 以 `F[_]: Monad` 参数化的代数可用不同 effect 类型解释，将"描述"与"执行"分离。 |
| **高阶类型** | Scala 3 原生支持高阶类型参数（`F[_]`），这是表达 Functor / Monad 抽象的前提。 |

## 注意事项与局限

1. **标准库无 Monad trait。** Scala 标准库未定义 `Functor`、`Applicative`、`Monad` trait。必须使用 cats（或类似库）获取类型类层级；标准库只在具体类型上提供 `map`、`flatMap` 方法。
2. **for 推导的局限。** for 推导要求 `flatMap`、`map`、（可选）`withFilter` 作为具体方法存在，不会经过类型类实例派发。要配合 cats `Monad` 实例使用 for 推导，需 `import cats.syntax.flatMap.*` 与 `cats.syntax.functor.*`。
3. **Applicative 与 Monad 的取舍。** `Applicative` 允许可并行化的独立计算；`Monad` 隐含顺序串联。当 `Applicative` 足够时使用 `Monad` 会过度约束代码并阻止并行执行（如 `IO.parMapN` 只需 `Applicative`）。
4. **定律满足不由编译器强制。** 没有什么能阻止你写出一个违反结合律或左/右单元律的 `Monad` 实例。使用 `cats.laws` 和 discipline 测试验证定律。
5. **Future 不是合法的 Monad。** `scala.concurrent.Future` 在创建时即开始急切执行，因此 `pure` 后接 `flatMap` 与直接构造行为不同。使用 cats-effect `IO` 获取合法、惰性的替代。

## 示例 A：使用 Applicative 进行泛型校验

```scala
import cats.data.ValidatedNel
import cats.syntax.all.*

type V[A] = ValidatedNel[String, A]

val name: V[String] = "Alice".validNel
val age: V[Int]     = "must be positive".invalidNel

val person = (name, age).mapN((n, a) => s"$n is $a")
// Invalid(NonEmptyList("must be positive"))
// 两个错误都累积——这是 Applicative，而不是 Monad
```

## 示例 B：effect 多态的服务

```scala
import cats.Monad
import cats.syntax.all.*

trait UserRepo[F[_]]:
  def find(id: Long): F[Option[String]]

def greetUser[F[_]: Monad](repo: UserRepo[F], id: Long): F[String] =
  repo.find(id).map:
    case Some(name) => s"Hello, $name"
    case None       => "User not found"
```

## 新手心智模型

把 `F[_]` 想成**容器或上下文**：`Option` 是可能为空的上下文，`List` 是含多个值的上下文，`IO` 是延迟副作用的上下文。**Functor** 让你伸手进去变换值（`map`）；**Applicative** 让你组合多个独立容器；**Monad** 让你串联每步依赖上一步的计算（`flatMap`）。for 推导是语法糖，让 monadic 串联读起来像命令式代码。

## 用例交叉引用

- 用 Applicative 进行校验可在不短路的前提下累积错误，避免部分状态——见 [invalid-states](../usecases/invalid-states.md)。
- for 推导中的 monadic 串联可逐步构建复杂配置——见 [builder-config](../usecases/builder-config.md)。
- 对 `F[_]` 的 Monad 约束可追踪计算所需的 effect——见 [effect-tracking](../usecases/effect-tracking.md)。
- State monad 将状态迁移建模为纯 monadic 计算——见 [state-machines](../usecases/state-machines.md)。

# 引用

- [cats Monad 文档](https://typelevel.org/cats/typeclasses/monad.html)
- [cats Functor 文档](https://typelevel.org/cats/typeclasses/functor.html)
- [cats Applicative 文档](https://typelevel.org/cats/typeclasses/applicative.html)
- Scala 3 参考："Contextual Abstractions — Context Bounds"
