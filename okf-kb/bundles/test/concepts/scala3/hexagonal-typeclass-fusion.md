---
type: Concept
title: 六边形架构与 Scala 3 类型类融合设计蓝图
description: 用 Scala 3 类型类（Typeclass）定义六边形架构的微端口（Micro Ports），用 given 实例做适配器、用 extension
  让领域模型在应用服务中丝滑穿梭的弹性六边形架构设计方案。
tags:
- Scala 3
- 六边形架构
- 类型类
- 端口与适配器
- given
- extension
- 依赖注入
- 架构
timestamp: '2026-07-02T02:07:24Z'
---

# 六边形架构与 Scala 3 类型类融合设计蓝图

把经典的**六边形架构（Hexagonal Architecture / Ports & Adapters）**与 Scala 3 的**类型类（Typeclass）**设计模式结合，得到一种"弹性六边形架构"：用 Typeclass 声明端口、用 given 实例实现适配器、用 extension 让领域模型在服务中穿梭。

底层的上下文抽象机制（given/using/extension/命名上下文界定）详见 [Scala 3 上下文抽象与现代架构设计指南](scala3_context_abstraction.md)；类型类的语言基础见 [类型类（Given / Using / Given Import）](../../references/scala3/catalog/type-classes.md)、扩展方法见 [扩展方法（Extension Methods）](../../references/scala3/catalog/extension-methods.md)、上下文函数与 context bound 见 [上下文函数与 Context Bounds](../../references/scala3/catalog/context-functions.md)。

---

# 两个概念在架构中的不同层次

## 六边形架构（Hexagonal Architecture）

宏观的软件架构风格。核心思想是把业务领域（Domain Core）置于最中心，使其不依赖任何外部基础设施（数据库、缓存、网关）。

- **Domain Model（模型）**：纯粹的业务实体（如 `User`），不含任何技术实现——没有 SQL、没有 Redis 客户端、没有 HTTP 客户端。
- **Ports（端口）**：领域层定义的契约接口，声明领域层需要什么行为，但不关心谁去实现（例如 `UserRepository` 端口）。
- **Adapters（适配器）**：基础设施层的具体实现，负责把具体外部技术（MySQL 驱动、Redis 客户端、`HttpClient`）适配到端口上。
- **Services（应用服务）**：编排业务流，通过调用端口来协调数据读写。

## 类型类（Typeclass）

微观的代码设计模式。解决的是**非侵入式地为各种类型外挂"行为能力（Capabilities）"**的问题。它不关心系统边界在哪里，只关心：如何优雅、类型安全、零继承地让一个类型 `T` 具备某种能力。

---

# 核心差异对比

| 维度 | 六边形架构中的 Port & Service | Scala 3 中的 Typeclass & Extension |
|------|------------------------------|------------------------------------|
| 设计粒度 | 宏观（Macro），面向领域边界（用户管理、订单服务） | 微观（Micro），面向行为能力（可序列化、可持久化、可过期） |
| 关注核心 | 依赖倒置（DIP）：外围技术如何适配核心业务 | 特设多态（Ad-hoc Polymorphism）：类型如何按需外挂行为 |
| 接口设计 | 通常是胖接口（Fat Interface）：一个 `UserRepository` 包含 save / find / update / delete | 倡导微能力（Micro Capabilities）：把读、写、更新解耦为独立的 `Readable` / `Writable` / `Updatable` |
| 表达方式 | 经典 OOP 子类型多态（Interface → Implementation Class） | 上下文边界、`given` / `using` 隐式传递与 `extension` 扩展 |

---

# 融合方案：弹性六边形架构

传统六边形架构把"端口"设计成庞大而僵硬的 OOP 接口，导致适配器编写臃肿、难以做细粒度能力组合。融合方案的精髓：

- **用 Typeclass 定义 Ports**（端口的行为规范）。
- **用 Given Instances 实现 Adapters**（适配器）。
- **用 Extension Methods 让 Domain Models 在 Services 中丝滑穿梭**。

融合架构示意：

```
      [ 基础设施层 (Adapters) ]
   +------------------------------+
   |   given Writable[User, DB]   |  <-- 适配器实现（将 MySQL 技术适配到 Writable 端口）
   +--------------+---------------+
                  |
                  v
       [ 领域层 (Domain Core) ]
   +------------------------------+
   |  - Model: User               |  <-- 纯净的模型
   |  - Port: trait Writable[A,S] |  <-- 用 Typeclass 声明的微端口
   |  - Port: trait Readable[A,S] |
   +--------------+---------------+
                  ^
                  |
   +--------------+---------------+
   |   class UserService (using)  |  <-- 编排服务（用上下文边界组合所需能力）
   +------------------------------+
         [ 应用层 (Services) ]
```

---

# 实战代码模板

下面是符合弹性六边形架构的 Scala 3 实现，展示如何优雅管理 MySQL 与 Redis，并保持领域层绝对纯净。

## 领域层（Domain Core）：模型与微端口

```scala
package domain

import scala.concurrent.Future

// ====== 1. 纯净的领域模型 ======
case class User(id: String, name: String, email: String)

// ====== 2. 用 Typeclass 声明的"微端口 (Micro Ports)" ======

// 读端口
trait Readable[A, Storage]:
  def find(id: String)(using client: Storage): Future[Option[A]]

// 写端口（带 extension 方便点语法调用）
trait Writable[A, Storage]:
  def save(data: A)(using client: Storage): Future[Unit]

  extension (data: A)
    def saveTo(using client: Storage): Future[Unit] = save(data)

// 更新端口
trait Updatable[A, Storage]:
  def update(data: A)(using client: Storage): Future[Unit]

  extension (data: A)
    def updateIn(using client: Storage): Future[Unit] = update(data)
```

## 基础设施层（Infrastructure & Adapters）：驱动与具体适配器

```scala
package infrastructure

import domain._
import scala.concurrent.Future

// ====== 1. 底层技术客户端（模拟驱动） ======
class MySqlClient:
  def executeInsert(id: String, name: String): Unit =
    println(s"[MySQL] INSERT INTO users (id, name) VALUES ('$id', '$name')")

  def executeUpdate(id: String, name: String): Unit =
    println(s"[MySQL] UPDATE users SET name = '$name' WHERE id = '$id'")

class RedisClient:
  def setWithTtl(key: String, value: String, ttl: Int): Unit =
    println(s"[Redis] SETEX $key $ttl -> $value")

// ====== 2. 适配器实现（Given 实例） ======

// 适配器 1：将 MySQL 适配到 User 的 Writable 端口
given mysqlUserWriter: Writable[User, MySqlClient] with
  def save(user: User)(using db: MySqlClient): Future[Unit] = Future.successful {
    db.executeInsert(user.id, user.name)
  }

// 适配器 2：将 MySQL 适配到 User 的 Updatable 端口
given mysqlUserUpdater: Updatable[User, MySqlClient] with
  def update(user: User)(using db: MySqlClient): Future[Unit] = Future.successful {
    db.executeUpdate(user.id, user.name)
  }

// 适配器 3：将 Redis 适配到 User 的 Writable 端口（充当缓存写入）
given redisUserWriter: Writable[User, RedisClient] with
  def save(user: User)(using redis: RedisClient): Future[Unit] = Future.successful {
    redis.setWithTtl(s"cache:user:${user.id}", user.name, 3600)
  }
```

## 应用层（Application Services）：业务编排与能力组合

应用服务不需要知道底层 Adapter 是谁，它只需通过命名上下文边界声明需要什么能力，并隐式引入底层客户端连接即可。

```scala
package application

import domain._
import infrastructure._
import scala.concurrent.ExecutionContext.Implicits.global
import scala.concurrent.Future

class UserService(using db: MySqlClient, redis: RedisClient):

  /**
   * 业务流：创建用户。
   * 要求：T 必须能写进 MySQL，且能写进 Redis。
   * 这里用"命名上下文边界"声明了两个 Port 能力契约。
   */
  def registerUser[T](user: T)(using
    mysqlPort: Writable[T, MySqlClient],
    redisPort: Writable[T, RedisClient]
  ): Future[Unit] =
    println(s"--- 开始注册用户业务编排 ---")
    for {
      // 1. 通过 mysqlPort 将数据存入 MySQL
      _ <- mysqlPort.save(user)
      // 2. 通过 redisPort（利用其内置的 extension 方法）同步写入 Redis 缓存
      _ <- user.saveTo(using redis)
    } yield println("--- 用户注册及缓存同步完成 ---")

  /**
   * 业务流：更新用户。
   * 要求：T 必须能在 MySQL 中被更新。
   */
  def modifyUser[T](user: T)(using mysqlUpdatePort: Updatable[T, MySqlClient]): Future[Unit] =
    println(s"--- 开始修改用户业务编排 ---")
    // 直接使用 extension 优雅点出更新
    user.updateIn(using db)
```

---

# 落地架构建议

## 建议 1：保持领域模型（Models）的"贫血与纯净"

不要把数据库操作、Redis Key 拼接、HTTP 发送逻辑写在 `case class` 内部，让它们作为纯粹的数据载体。所有行为能力一律声明为外挂的 `trait Typeclass[A]`。这与 [领域建模](../../references/scala3/usecases/domain-modeling.md) 的理念一致。

## 建议 2：用"微端口（Micro Ports）"替代"胖接口"

传统六边形架构喜欢写一个全能的 `UserRepository`。在 Scala 3 中建议拆分为 `Readable[User, DB]`、`Writable[User, DB]` 等多个极细粒度的 Typeclass。

好处：可以给只读的 API 实体只挂载 `Readable`，而不用强行实现无意义的 `save`。这完全契合接口隔离原则（ISP），也与 [扩展性（Extensibility）](../../references/scala3/usecases/extensibility.md) 的设计目标一致。

## 建议 3：利用 Service 层的 using 做依赖注入（DI）

传统六边形架构和 Spring 框架喜欢用复杂的 IoC 容器。Scala 3 中底层基础设施客户端（`MySqlClient`、`RedisClient`）应作为上下文参数传给 Service：

```scala
class OrderService(using db: MySqlClient, redis: RedisClient)
```

这是 Scala 3 原生、最轻量、编译期安全且无需反射的依赖注入机制。其解析机制见 [Given/隐式解析 (Trait Solver)](../../references/scala3/catalog/trait-solver.md)。

## 建议 4：不要"为了抽象而抽象"

若一个业务服务仅跟 MySQL 打交道，且没有其他异构数据源替代的可能，可直接在 Service 中写死依赖（用传统 Class 依赖），不必强行套用 Typeclass。

**什么时候一定要用 Typeclass？** 当系统存在异构多介质存取（同一份数据既要存 MySQL 建索引、又要存 Redis 做缓存、还要推给 Kafka/API），或不同数据类型需要共享相同的流水线处理逻辑时，"Typeclass 化端口"的设计才能发挥其扩展弹性与类型安全优势。

---

# Citations

- 本蓝图为原创设计文档（用户在对话中提供全文，无外部 URL）。
- 上下文抽象语言基础：[Scala 3 上下文抽象与现代架构设计指南](scala3_context_abstraction.md)
- 类型类与上下文函数的语言机制：[类型类（Given / Using / Given Import）](../../references/scala3/catalog/type-classes.md)、[上下文函数与 Context Bounds](../../references/scala3/catalog/context-functions.md)、[扩展方法（Extension Methods）](../../references/scala3/catalog/extension-methods.md)、[泛型与有界多态](../../references/scala3/catalog/generics-bounds.md)
- 相关用例：[领域建模](../../references/scala3/usecases/domain-modeling.md)、[扩展性](../../references/scala3/usecases/extensibility.md)、[结构化契约](../../references/scala3/usecases/structural-contracts.md)
