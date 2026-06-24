---
type: Reference
resource: https://raw.githubusercontent.com/jpablo/vibe-types/main/plugin/skills/scala3/catalog/T55-monad-transformers.md
title: Monad Transformers
description: Scala 3 中通过 cats 的 EitherT、OptionT、StateT、Kleisli 等 monad transformer
  将多个 monadic effect 组合成单一栈的机制。
tags:
- Monad Transformer
- EitherT
- OptionT
- StateT
- Kleisli
- effect 栈
- cats
- T55
- Scala 3
- vibe-types
timestamp: '2026-06-24T12:04:27Z'
---

# Monad Transformers

## 简介

Monad transformer 让你**将多个 monadic effect 组合成一个单一 monad 栈**。当某个计算既可能失败（`Either`）又要执行 IO（`IO`）时，不能简单地嵌套 `IO[Either[E, A]]` 并用单个 for 推导——类型不对齐。像 `EitherT[IO, E, A]` 这样的 transformer 包装了嵌套结构并提供统一的 `Monad` 实例，使 for 推导能贯穿整个栈工作。

cats 提供标准 transformer：

- **`EitherT[F, E, A]`** 包装 `F[Either[E, A]]`（错误处理）
- **`OptionT[F, A]`** 包装 `F[Option[A]]`（可选性）
- **`StateT[F, S, A]`** 包装 `S => F[(S, A)]`（有状态计算）
- **`ReaderT[F, R, A]`**（又名 `Kleisli[F, R, A]`）包装 `R => F[A]`（依赖注入）
- **`WriterT[F, W, A]`** 包装 `F[(W, A)]`（日志/累积）

> **Since:** Scala 3.0（cats monad transformer 自 cats 1.x 起）

## 可表达的约束

**Monad transformer 确保 effect 以类型良好的栈组合，每层的操作可通过统一 monadic 接口访问，而内层 effect 必须显式 lift 后才能在外层使用。**

## 最小示例

```scala
import cats.data.EitherT
import cats.effect.IO

type AppError = String

def findUser(id: Long): EitherT[IO, AppError, String] =
  EitherT.rightT("Alice")

def checkAge(name: String): EitherT[IO, AppError, Int] =
  EitherT.rightT(30)

val program: EitherT[IO, AppError, String] =
  for
    name <- findUser(1L)
    age  <- checkAge(name)
  yield s"$name is $age"
// 单个 for 推导同时处理 IO 和 Either
```

## 与其他特性的交互

| 特性 | 组合方式 |
|------|----------|
| **Functor/Applicative/Monad**（见 [functor-applicative-monad](functor-applicative-monad.md)） | Transformer 要求底层 `F` 是 Monad；transformer 本身也是 Monad，因此支持 for 推导串联。 |
| **类型类 / givens**（见 [type-classes](type-classes.md)） | Transformer 实例以 given 实例提供；当 `F` 拥有 `Monad` 实例时 `EitherT` 也自动获得 `Monad` 实例。 |
| **Tagless final**（见 [tagless-final](tagless-final.md)） | Tagless final 代数常被解释到 monad transformer 栈，例如 `type App[A] = EitherT[IO, AppError, A]`。 |
| **for 推导** | Transformer 统一了栈，使单个 for 推导可贯穿所有 effect 层串联操作。 |
| **类型 lambda**（见 [generics-bounds](generics-bounds.md)） | `EitherT[IO, AppError, *]` 的 kind 为 `* -> *`，匹配 `F[_]`。类型 lambda 或 kind-projector 语法可将多参数 transformer 适配为期望形状。 |

## 注意事项与局限

1. **性能开销。** 每个 transformer 层在每次 `flatMap` 步骤都增加一次分配。深层栈（如 `EitherT[StateT[ReaderT[IO, Config, _], AppState, _], Error, _]`）可能有可测量开销。可考虑使用 effect 系统（ZIO、cats-effect + `Ref`）作为替代。
2. **必须 lift。** 要在 `EitherT[IO, E, A]` 内使用底层 `IO` 操作，必须 `EitherT.liftF(ioAction)`。忘记 lift 会导致类型不匹配。cats 的 `MonadError` 与 `Ask` 类型类可减少手动 lift。
3. **栈顺序敏感。** `EitherT[StateT[IO, S, _], E, A]` 与 `StateT[EitherT[IO, E, _], S, A]` 语义不同：前者中状态在错误后保留；后者中错误会丢弃状态变更。
4. **类型推断困难。** 复杂 transformer 栈可能超出 Scala 类型推断能力，常需要对中间值显式标注类型或使用类型别名。
5. **可组合性上限。** Transformer 一次只能组合两个 effect，加入第三层意味着再包一层 transformer，导致二次级样板代码。这是 ZIO、cats-effect 等 effect 系统出现的主要动机。

## 新手心智模型

把 monad transformer 想成**把两个插座合并为一个的适配器**。`IO` 提供"副作用"插座，`Either` 提供"错误处理"插座。`EitherT[IO, E, A]` 是一个给你单一支持两者插座的适配器。你把 for 推导插进合并后的插座即可无缝使用两种能力。代价是：当你有一个只适配原插座之一的插头时，需要显式"lift"。

## 示例 A：用 OptionT 处理 IO 中的可选结果

```scala
import cats.data.OptionT
import cats.effect.IO

def lookupEnv(key: String): OptionT[IO, String] =
  OptionT(IO(sys.env.get(key)))

def lookupPort: OptionT[IO, Int] =
  lookupEnv("PORT").mapFilter(_.toIntOption)

val config: OptionT[IO, (String, Int)] =
  for
    host <- lookupEnv("HOST")
    port <- lookupPort
  yield (host, port)
// 任一环境变量缺失则得 None；IO 负责读取环境的副作用
```

## 示例 B：用 StateT 进行有状态计算

```scala
import cats.data.StateT
import cats.effect.IO

type Counter[A] = StateT[IO, Int, A]

def increment: Counter[Unit] = StateT.modify(n => n + 1)
def getCount: Counter[Int]   = StateT.get

val program: Counter[String] =
  for
    _     <- increment
    _     <- increment
    _     <- increment
    count <- getCount
  yield s"Final count: $count"
// program.run(0) => IO((3, "Final count: 3"))
```

## 用例交叉引用

- `EitherT` 与 `OptionT` 确保错误与缺失处理贯穿整条计算链——见 [invalid-states](../usecases/invalid-states.md)。
- `ReaderT`（Kleisli）将配置注入计算栈而无需显式传参——见 [builder-config](../usecases/builder-config.md)。
- Transformer 栈使完整 effect 集合在类型签名中可见——见 [effect-tracking](../usecases/effect-tracking.md)。
- `StateT` 将状态机迁移编码为纯、可组合的 monadic 计算——见 [state-machines](../usecases/state-machines.md)。

# 引用

- [cats EitherT 文档](https://typelevel.org/cats/datatypes/eithert.html)
- [cats OptionT 文档](https://typelevel.org/cats/datatypes/optiont.html)
- [cats StateT 文档](https://typelevel.org/cats/datatypes/state.html)
- [cats Kleisli (ReaderT) 文档](https://typelevel.org/cats/datatypes/kleisli.html)
