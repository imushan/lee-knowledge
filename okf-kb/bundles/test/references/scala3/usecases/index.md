# Reference

* [DSL 与构建器模式（DSL and Builder Patterns）](builder-config.md) - 构建类型安全的 DSL 与流式 API，让编译器强制约束正确的使用方式，非法构造序列或缺字段即为编译错误。
* [不可变性](immutability.md) - 确保数据一旦创建便不可变，消除竞态、别名与陈旧引用类问题，让编译器更激进地推理代码。
* [协议状态机（Protocol State Machines）](state-machines.md) - 在编译期强制合法调用顺序与协议合规，让调用序列违背成为类型错误而非运行时异常。
* [可空性与可选性（UC16）](nullability.md) - 通过 Scala 3 显式可空（explicit nulls）在类型系统中大幅减少 NPE。
* [可调用契约](callable-contracts.md) - 对可调用值表达契约——函数类型、SAM 转换、传名参数、eta 展开——让编译器在每个调用点校验元数、参数类型与求值策略。
* [型变与子类型化（UC17）](variance.md) - 精确控制协变、逆变与子类型关系，避免不安全的转换或过僵的 API。
* [屏蔽非法状态](invalid-states.md) - 在编译期让非法状态不可表达，使任何能够构造出来的值都天然合法，从而消除运行时校验。
* [并发（通过库）（UC21）](concurrency.md) - 通过 ZIO、Cats Effect、Akka Typed 与 Ox 等库在类型层面跟踪并发效应并强制结构化并发。
* [序列化编解码器（UC19）](serialization.md) - 通过 derives、Mirror 与 inline 在编译期自动派生类型安全的序列化编解码器。
* [扩展性（Extensibility）](extensibility.md) - 设计扩展点——控制什么可扩展、什么不可扩展，用显式契约替代 Scala 2 隐式开放的继承模型。
* [效果追踪（Effect Tracking）](effect-tracking.md) - 在类型层面追踪副作用——IO、异常、变异、能力；函数签名声明它能做什么，编译器拒绝未声明的效果。
* [泛型约束](generic-constraints.md) - 限制类型参数只能实例化为提供所需能力的类型，编译器拒绝缺失证据的实例化。
* [相等性与比较（UC15）](equality.md) - 通过 Scala 3 的多宇宙相等性（multiversal equality）在编译期阻止无意义的相等比较。
* [穷尽匹配](exhaustiveness.md) - 确保每个模式匹配都覆盖所有可能情况，编译器拒绝不完整匹配并定义“全部情况”的含义。
* [类型级算术（UC18）](type-arithmetic.md) - 使用 compiletime.ops 与匹配类型在编译期执行数值计算并强制数值约束。
* [结构化契约](structural-contracts.md) - 按值暴露的成员而非类层级来接受值，编译器静态验证鸭子类型契约。
* [编译期编程（Compile-Time Programming）](compile-time.md) - 将计算与验证从运行时移到编译期，让错误在编译阶段暴露，常量由编译器求值而非由 JVM 求值。
* [访问与封装（Access and Encapsulation）](encapsulation.md) - 控制可见性并防止对内部实现的无权访问，编译器强制模块边界，客户端无法依赖不应看到的表示。
* [错误处理（Error Handling）](error-handling.md) - 以类型安全的方式处理错误，让编译器追踪可能发生的错误并确保被处理，避免静默吞没异常。
* [领域建模](domain-modeling.md) - 用精确的领域类型在编译期拒绝非法值，让类型系统携带证明而非靠运行时断言。
