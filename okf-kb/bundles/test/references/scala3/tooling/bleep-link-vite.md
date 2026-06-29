---
type: Reference
resource: sources/articles/bleep-link-vite-design.md
title: bleep link-vite 脚本：Scala.js + Vite 统一开发流水线
description: 用纯 Scala BleepScript 作为全局调度器，驱动 Scala.js + Vite 的统一开发流水线：读 bleep 项目模型定位链接产物、动态生成临时
  vite 配置、双路监听（后台 bleep link --watch + 前台 npx vite），抛弃静态 vite.config.js。
tags:
- Scala
- Scala.js
- bleep
- BleepScript
- Vite
- 前端工程化
- Laminar
timestamp: '2026-06-29T12:42:18Z'
---

# 用途

用一个**纯 Scala 的 BleepScript**作为全局调度器，统一承担 Scala.js 前端工程化的三件事（构建产物路径发现、配置生成、进程编排），消除传统方案对静态 `vite.config.js` + sbt 绑定的 `@scala-js/vite-plugin-scalajs` 插件的依赖。

本脚本是 `scripts.LinkVite`（注册名 `link-vite`），源码：`LinkVite.scala`，目标 bleep 版本 `1.0.0-M10`，适用项目典型形态为 Scala 3 + Scala.js + Laminar + cats-effect。

```
                    bleep link-vite [dev|build] [project]
                              │
        ┌─────────────────────┴──────────────────────────┐
        │  LinkVite.run(started, commands, args)          │
        │  ① projectPaths(crossName).targetDir            │
        │     → 定位 link-output/debug/js/main.js          │
        │  ② writeTempConfig(): 临时目录生成 vite 配置     │
        │     resolve.alias { 'scalajs:main.js' → main.js }│
        └────────┬───────────────────────────┬────────────┘
                 ▼                           ▼
      线程 A（后台）                   线程 B（前台）
      bleep link <project> --watch     npx vite --config <临时>
   改 .scala → 增量重链接             文件监控(Chokidar) → HMR
```

# 设计目标与非目标

**目标**：抛弃静态 `vite.config.js`；不依赖 sbt 绑定的 scala-js vite 插件；自动发现产物路径（直接读 bleep 内部项目模型）；在系统临时目录动态生成 Vite 配置，用 `resolve.alias` 注入产物路径；双路监听一键启动、单终端。

**非目标**：不替代 bleep 本身的编译 / 链接能力，只做编排；不引入新的 Scala.js 打包器（继续用 Vite 原生能力）；不处理 CSS 预处理器（保持前端入口纯净）。

# 参数解析

```
bleep link-vite [dev|build] [project]
```

- 位置参数中含 `build` → 生产构建模式；否则 dev 模式（默认）。
- 其余位置参数取第一个为项目名，缺省 `baidu`。
- `--` 前缀的参数忽略（bleep 自身标志）。

# 产物路径发现

```scala
val crossName = CrossProjectName(ProjectName(projectNameStr), None)
val targetDir = started.projectPaths(crossName).targetDir
val mainJs    = targetDir.resolve("link-output").resolve("debug").resolve("js").resolve("main.js")
```

`targetDir` 即 `.bleep/builds/normal/.bloop/<project>`。链接产物固定在 `link-output/<debug|release>/js/main.js`（本项目默认 debug / fast-opt）。

# 临时配置生成（CJS 纯对象）

`writeTempConfig` 用 `Files.createTempFile(tempDir, "vite-config-", ".js")` 创建文件，写入 **CJS 纯对象**（不 `require('vite')`，规避 Vite 8 ESM-only 的 `ERR_REQUIRE_ESM`）：

```js
module.exports = {
  resolve: { alias: { 'scalajs:main.js': "<ABSPATH>/main.js" } },
  server: {
    port: 5173,
    fs: {
      allow: [
        "<PROJECT_ROOT>",          // 放行 index.html / src
        "<LINK_OUTPUT_DIR>"         // 放行 .bleep 下的产物
      ]
    }
  }
};
```

> **关键坑**：`server.fs.allow` 会**覆盖** Vite 默认白名单（默认含项目根），因此必须同时显式放行项目根，否则 `index.html` / `src/` 会被 403。

前端入口 `src/main.js` 只需 `import 'scalajs:main.js'`——`scalajs:main.js` 是约定虚拟标识符，Vite 的 `resolve.alias`（内置 `@rollup/plugin-alias`）在 `resolveId` 阶段把它替换为产物绝对路径。bleep 的 `jsKind: none` 产物是 IIFE，文件末尾自动调用 `Main.main`，故 side-effect 导入即触发 Laminar 应用挂载。

# 进程编排与子进程选择

```scala
// 线程 A：后台
val linkProc = Process(List("bleep", "link", projectNameStr, "--watch", "--no-tui")).run(rawIO)
// 线程 B：前台（阻塞主线程）
val viteProc = Process(List("npx", "vite", "--config", tempCfg.toString)).run(rawIO)
viteProc.exitValue()   // 阻塞
```

`rawIO` 是自定义 `ProcessIO`，把子进程 stdout/stderr 原样转发，保留 ANSI 颜色（`transfer()` 用 4KB 缓冲做字节级 copy，不按行截断）。

**为什么不用 `commands.link(watch = true)`？** 原始设计假设 `Commands` 提供 `link` 方法。**实测**：bleep M10 的脚本 `Commands` API 只暴露 `compile / run / test / script / publishLocal / publish`，**没有 `link`**（链接由 CLI / BSP 内部的 `bleep.bsp.LinkExecutor` 实现）。故以子进程方式实现后台链接，多一次进程启动（毫秒级），换来与 CLI 完全一致的行为。详见 [bleep-scripts 的内置 API vs 子进程](../../../concepts/scala3/tooling/bleep-scripts.md)。

# build 模式

非 watch、阻塞、失败即 `sys.error`、结束即清理：

```scala
val linkExit  = Process(List("bleep", "link", projectNameStr, "--no-tui")).run(rawIO).exitValue()
val buildExit = Process(List("npx", "vite", "build", "--config", tempCfg.toString)).run(rawIO).exitValue()
cleanup(tempCfg, tempDir)
```

# 错误处理与边界

| 场景 | 处理 |
|------|------|
| 项目名不存在 | `started.projectPaths` 抛 bleep 异常，脚本终止 |
| 首次无产物 | `waitForFile(mainJs, 90s)` 轮询等待后台链接产出，消除 Vite 首次请求 404 的竞态 |
| bleep link / vite build 非零退出（build 模式） | `sys.error` 终止 |
| `Ctrl+C`（SIGINT） | shutdown hook：`linkProc.destroy()` + `viteProc.destroy()` + `cleanup` 删临时文件 |
| `kill -9`（SIGKILL） | 绕过 hook，临时文件残留，需手动删 `/tmp/link-vite-*` |
| 项目根存在 `vite.config.*` | `--config` 旁路静态配置（不生效、不报错）；脚本检测到打印警告，不阻止运行 |
| 端口 5173 占用 | vite 自行报错（脚本不抢端口管理） |

# 使用方式

```bash
# 开发（默认 dev）
bleep link-vite          # 默认 dev + 默认 baidu
bleep link-vite dev baidu
# 生产构建
bleep link-vite build baidu
```

dev 启动后浏览器打开 `http://localhost:5173`，改 `.scala` 保存即自动刷新。build 产出 `dist/`（实测 1.6MB → gzip 274KB）。

# 相关概念

- [BleepScript 复用脚本姿势](../../../concepts/scala3/tooling/bleep-scripts.md) — 本脚本遵循的共性模式；解释为何链接用子进程而非内置 API

# Citations

- `bleep_scripts/link-vite/link-vite-design.md`（已钉死到原料层：[bleep-link-vite-design](../../../../../sources/articles/bleep-link-vite-design.md)；原始位置 `/home/ai/lee/workspace/bleep_scripts/link-vite/link-vite-design.md`）
- 源码：`bleep_scripts/link-vite/LinkVite.scala`
