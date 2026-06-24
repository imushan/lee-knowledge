# Reference

* [Functor、Applicative 与 Monad](functor-applicative-monad.md) - Scala 3 中用于表达上下文计算的 Functor、Applicative、Monad 抽象层级，以及 cats 提供的类型类实例与 for 推导的脱糖机制。
* [Given/隐式解析 (Trait Solver)](trait-solver.md) - Scala 3 的 given 解析算法在定义良好的作用域中搜索并按特异性选择唯一最佳 given 实例，保证能力注入的无歧义性。
* [inline 与编译期操作](compile-time-ops.md) - inline 关键字保证调用点展开与编译期求值，compiletime.ops 将算术、布尔、字符串操作提升到类型层，实现条件编译与编译期特化。
* [Kind 多态 (Universes & Kinds)](universes-kinds.md) - Scala 3 通过 AnyKind 上界允许类型参数跨任意 kind 抽象，可统一处理正当类型、一阶与高阶类型构造器。
* [Match Types（类型级模式匹配）](match-types.md) - Scala 3 中的类型级构造，根据 scrutinee 类型的结构归约到多个右侧类型之一，实现类型级条件选择与递归计算。
* [Matchable 与 TypeTest](type-narrowing.md) - Matchable 限制哪些值可作为模式匹配的 scrutinee，TypeTest 通过显式见证保证对抽象类型的运行时类型检查是可靠的。
* [Monad Transformers](monad-transformers.md) - Scala 3 中通过 cats 的 EitherT、OptionT、StateT、Kleisli 等 monad transformer 将多个 monadic effect 组合成单一栈的机制。
* [Nothing 与底类型 (Never / Bottom Type)](never-bottom.md) - Nothing 是 Scala 的底类型，无任何居民，使发散计算与任意类型上下文保持类型兼容；explicit-nulls 把 Null 从引用类型层级中解耦。
* [Tagless Final 模式](tagless-final.md) - Scala 3 中以高阶类型参数 F[_] 定义代数 trait、将业务逻辑与具体 effect 实现分离的 tagless final 设计模式。
* [Typestate 编程](typestate.md) - Scala 3 中利用 phantom 类型参数将对象状态编码到类型层，使方法仅在正确状态下可调用的 typestate 技术。
* [Witness 与 Evidence 类型](witness-evidence.md) - Scala 3 中通过 =:、<:<、自定义 given evidence 在类型层编码前提条件证据，并由编译器经 given 搜索供给的机制。
* [上下文函数与 Context Bounds](context-functions.md) - Scala 3 中抽象上下文依赖的两种机制：上下文函数类型 T ?=> U 将隐式参数提升为一等类型，context bound [T: Ord] 简化类型类证据声明。
* [不可变性标记 (Immutability Markers)](immutability-markers.md) - Scala 通过 val、final、sealed 与不可变集合在绑定、成员、层级与数据四个层面强制不可变性，全部由编译器检查。
* [不透明类型别名（Opaque Types）](newtypes-opaque.md) - 通过不透明类型别名创建与表示同构但在外部完全抽象的新类型，零运行时开销地防止语义不同值混用。
* [代数数据类型（Enum / ADT / GADT）](algebraic-data-types.md) - 通过 enum 将值空间封闭为编译器可知的有限备选项，实现穷尽模式匹配并按分支细化类型信息。
* [依赖类型（路径依赖类型与 match 类型）](dependent-types.md) - 通过路径依赖类型、match 类型、单例类型与依赖函数类型，将输出类型绑定到输入值或输入类型，在编译期验证两者关系。
* [关联类型（通过类型成员）](associated-types.md) - Scala 中通过抽象类型成员实现的关联类型，与 Rust 的 associated types 和 Haskell 的 type families 对应，由实现者决定具体类型。
* [单例类型、字面量类型与编译期值参数](const-generics.md) - 通过单例/字面量类型、inline 参数、constValue 与 compiletime.ops，将字面量值提升到类型层，实现 const generics 风格的维度与容量约束。
* [变型与子类型规则（Variance & Subtyping）](variance-subtyping.md) - 通过协变、逆变与不变标注声明并强制泛型类型的可替换性规则，在编译期保证 Liskov 替换原则成立。
* [变更与移除的特性](changed-dropped.md) - Scala 3 相对 Scala 2 的类型系统行为变更与移除：改进的类型推断、新的隐式解析算法、移除存在类型、限制抽象类型上的类型投影。
* [可调用类型与重载（Callable Types & Overloading）](callable-typing.md) - 以函数类型、SAM 转换、eta 展开、重载、传名参数与上下文函数类型精确表达一次计算所需的输入、上下文与求值策略，并由编译器在调用处强制匹配。
* [基于 trait 的动态分派 (Trait Objects)](trait-objects.md) - Scala 3 的 trait 与抽象类通过 JVM 虚方法分派提供运行时多态，sealed/open/Matchable 控制扩展与匹配边界。
* [多元宇宙相等性（Multiversal Equality）](equality-safety.md) - 通过二元类型类 CanEqual[L, R] 限定哪些类型对可以用 == 或 != 比较，使语义上无意义的跨类型比较在编译期被拒绝。
* [字面量类型（单例类型）](literal-types.md) - Scala 3 中每个字面量值都有单例类型，将值约束为确切的一个字面量，是 const generics、编译期运算和 match types 的基础。
* [存在类型](existential-types.md) - Scala 3 通过抽象类型成员、通配符类型? 与路径依赖类型编码“存在某个类型但隐藏其具体身份”的存在类型机制。
* [宏：quotes 与 splices](macros-metaprogramming.md) - 通过 quotes `'{ }` 与 splices `${ }` 构建类型安全、跨阶段卫生的编译期代码生成，支持 AST 检查、变换与自定义编译错误。
* [实验与预览特性：命名类型参数、into、模块化](experimental-preview.md) - Scala 3 中三个前向特性：命名类型参数、into 类型（控制隐式转换位置）、模块化改进（tracked 参数、应用构造类型、精炼类型父类）。
* [封装修饰符（open / export / transparent trait）](encapsulation.md) - open 限定谁可继承、export 控制以委托暴露哪些成员、transparent 决定哪些父类型出现在推导类型中，三者共同表达可扩展性与封装契约。
* [扩展方法（Extension Methods）](extension-methods.md) - 允许在不修改原类型源码的情况下为其追加方法，并可结合 given 实例实现仅在具备类型类证据时才可见的条件化方法。
* [抹除定义（Erased Definitions / Phantom Evidence）](erased-phantom.md) - 用 erased 修饰参数或 val 使其仅存在于编译期并在代码生成前被完全抹除，实现零成本的类型级证据与幻影类型状态机。
* [捕获检查、CanThrow 与纯函数](effect-tracking.md) - 通过捕获检查为每个值类型附带一个捕获集，静态追踪它可能引用的副作用能力（IO、可变状态、异常），禁止能力逃逸出所属作用域。
* [显式 null（T | Null、.nn、unsafeNulls）](null-safety.md) - 通过 -Yexplicit-nulls 将 Null 从所有引用类型的子类型中移除，要求可空引用显式写作 T | Null，将 NPE 变为编译期错误。
* [泛型与有界多态（Generics & Bounds）](generics-bounds.md) - 通过上界、下界、上下文边界与 F-有界多态约束类型参数，使泛型代码仅在所需操作存在时才可实例化。
* [注解与编译器指令 (Annotations)](notation-attributes.md) - Scala 注解是附加在定义上的元数据标记，可在编译期强制约束、优化生成代码或重命名字节码，如 @tailrec、@inline、@targetName 等。
* [类型 Lambda（Type Lambdas）](type-lambdas.md) - Scala 3 中的匿名高阶类型表达式，允许在类型位置直接部分应用或重排类型构造器参数，无需命名别名。
* [类型别名（Type Aliases）](type-aliases.md) - 用 type 为已有类型引入完全透明的别名，或用抽象类型成员声明“存在但未揭示”的类型，不创建新的类型边界。
* [类型类派生（Type-Class Derivation）](derivation.md) - 通过 derives 子句让编译器基于类型的编译期结构自动生成类型类实例，免除手写模板并保证结构一致性。
* [类型类（Given / Using / Given Import）](type-classes.md) - 通过 given 实例与 using 子句要求编译期类型证据并由编译器自动供给，构成 Scala 3 类型类分派的基础。
* [细化类型（Refinement Types）](refinement-types.md) - 用谓词收窄基础类型，使带谓词的值只能在通过编译期或运行期检查后才能构造，把校验编入类型本身。
* [结构类型、细化类型与命名元组](structural-typing.md) - 通过结构类型与命名元组实现静态检查的鸭子类型与记录式类型，按成员签名而非具名层级约束值。
* [联合类型与交叉类型（A | B / A & B）](union-intersection.md) - 以类型组合子表达多类型的析取或合取，无需引入共同父类型即可限定接受值或同时要求多种能力。
* [自身类型 (Self Types)](self-type.md) - 自身类型注解声明 trait 对其他能力的依赖关系而不建立继承链，是 Cake 模式与模块化组合的基础。
* [记录类型与数据建模 (Record Types)](record-types.md) - Scala 3 通过 case class、命名元组与普通元组三种机制覆盖从领域建模到临时数据打包的完整数据建模谱系，由编译器保证字段形状的正确性。
* [路径依赖类型](path-dependent-types.md) - Scala 中类型成员的身份依赖于访问它的运行时路径（对象实例），编译器将不同实例的类型成员视为不相关类型。
* [连贯性与实例作用域（Coherence & Instance Scoping）](coherence-orphan.md) - Scala 3 无孤儿规则，通过给定实例的作用域与 import 规则实现“每个使用点至多一个实例”的局部连贯性，歧义时报错而非静默选择。
* [递归类型](recursive-types.md) - Scala 3 中通过 sealed trait/enum 层级定义自引用类型以建模树、表达式、流等递归与共递归数据结构的技术。
* [隐式转换、by-name 上下文参数与 deferred givens](conversions-coercions.md) - 通过 Conversion 类型类控制隐式拓宽、用 by-name 上下文参数打破循环 given 依赖、用 deferred givens 跨 trait 层级传播类型类要求。
