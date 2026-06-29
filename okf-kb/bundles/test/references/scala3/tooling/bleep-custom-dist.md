---
type: Reference
resource: sources/articles/bleep-custom-dist-design.md
title: bleep custom-dist 脚本：封装内置 Dist 打包后端服务
description: 用 BleepScript 封装 bleep 内置 Dist 命令打包后端服务（api-server），并用 os-lib 把产物搬到约定输出目录
  out/。最简的一种 script：不编排外部进程、不生成配置，直接调用内置命令 API。
tags:
- Scala
- bleep
- BleepScript
- 打包
- Dist
- os-lib
timestamp: '2026-06-29T12:42:32Z'
---

# 用途

把一个后端服务项目（典型：http4s + Tapir + doobie 的 `api-server`）打包成可分发的本地产物（含依赖 jar + 启动脚本），并搬到项目根的**约定目录 `out/`**，供后续部署 / 打包脚本消费。封装为一条命令 `bleep my-dist`。

本脚本是 `bleep.scripts.CustomDist`（注册名 `my-dist`），源码：`CustomDist.scala`，目标 bleep 版本 `0.0.14`。它是三个脚本里**最简的一种**——不编排外部进程、不生成配置，直接调用 bleep 内置命令 API。

# 实现思路

```scala
val distCommand = bleep.commands.Dist(started, watch = false, options = distOptions)
distCommand.run(started)
```

`bleep.commands.Dist` 是 bleep-core 公开的打包命令（等价于 CLI `bleep dist`）。脚本只做两件事：

1. **调用内置 Dist** 打包 `api-server`（产物落到 `target/dist`）。
2. **搬运产物**：用 os-lib 把 `target/dist` 移动（覆盖）到项目根的 `out/`。

```scala
val projectName = model.ProjectName("api-server")
val crossName   = model.CrossProjectName(projectName, None)
val distOptions = bleep.commands.Dist.Options(
  project = crossName, overrideMain = None, overridePath = None
)
new bleep.commands.Dist(started = started, watch = false, options = distOptions).run(started)

val sourcedistDir = started.projectPaths(crossName).targetDir.resolve("dist")
val targetDir     = started.buildPaths.buildDir.resolve("out")   // 项目根 out/

if (os.exists(os.Path(sourcedistDir))) {
  os.remove.all(os.Path(targetDir))           // 先清空目标
  os.move(os.Path(sourcedistDir), os.Path(targetDir))
}
```

# 关键点

- **内置命令 vs 子进程**：`bleep.commands.Dist` 是公开 API，可直接 `new Dist(...).run(started)`——比 spawn `bleep dist` 子进程更直接、无额外进程开销。这与 [bleep-link-vite](bleep-link-vite.md)（因 `Commands` 无 `link` 方法而被迫用子进程）形成对比：**能用内置 API 就用内置 API**。详见 [bleep-scripts](../../../concepts/scala3/tooling/bleep-scripts.md)。
- **依赖**：除 `bleep-core` 外，额外依赖 `com.lihaoyi::os-lib`（用于 `os.move` / `os.remove.all` 的文件搬运）。
- **路径**：
  - 产物源：`started.projectPaths(crossName).targetDir.resolve("dist")`
  - 目标：`started.buildPaths.buildDir.resolve("out")`（项目根 `out/`）
- **覆盖语义**：`os.remove.all(targetDir)` 先清空目标，再 `os.move`——每次构建 `out/` 都是干净的最新产物。

# 局限 / 可改进

- **硬编码项目名**：`model.ProjectName("api-server")` 写死，未参数化。如要支持多项目打包，应从 `args` 取项目名（参考 [bleep-link-vite](bleep-link-vite.md) 的参数解析）。
- **硬编码输出目录**：`out/` 固定，未参数化。
- **无失败处理**：`os.exists` 检查源目录，但 Dist 本身的 `run` 异常会直接冒泡（可接受）。
- **目标项目固定为单 JVM 服务**：脚本逻辑专为"一个 mainClass 服务的打包"设计。

# 接入（bleep.yaml）

```yaml
projects:
  scripts:
    extends: template-common          # JVM 模板
    dependencies:
      - build.bleep::bleep-core:0.0.14
      - com.lihaoyi::os-lib:0.11.3

scripts:
  my-dist:
    main: bleep.scripts.CustomDist
    project: scripts
```

运行：`bleep my-dist` → 产物出现在 `<项目根>/out/`。

# 相关概念

- [BleepScript 复用脚本姿势](../../../concepts/scala3/tooling/bleep-scripts.md) — 本脚本遵循的共性模式；对比"内置 API vs 子进程"的取舍
- [bleep link-vite 脚本](bleep-link-vite.md) — 被迫用子进程的另一极端案例

# Citations

- `bleep_scripts/custom-dist/custom-dist-design.md`（已钉死到原料层：[bleep-custom-dist-design](../../../../../sources/articles/bleep-custom-dist-design.md)；原始位置 `/home/ai/lee/workspace/bleep_scripts/custom-dist/custom-dist-design.md`）
- 源码：`bleep_scripts/custom-dist/CustomDist.scala`
