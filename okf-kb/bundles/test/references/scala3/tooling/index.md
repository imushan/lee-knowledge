# Reference

* [bleep custom-dist 脚本：封装内置 Dist 打包后端服务](bleep-custom-dist.md) - 用 BleepScript 封装 bleep 内置 Dist 命令打包后端服务（api-server），并用 os-lib 把产物搬到约定输出目录 out/。最简的一种 script：不编排外部进程、不生成配置，直接调用内置命令 API。
* [bleep link-vite 脚本：Scala.js + Vite 统一开发流水线](bleep-link-vite.md) - 用纯 Scala BleepScript 作为全局调度器，驱动 Scala.js + Vite 的统一开发流水线：读 bleep 项目模型定位链接产物、动态生成临时 vite 配置、双路监听（后台 bleep link --watch + 前台 npx vite），抛弃静态 vite.config.js。
* [bleep mcp-setup 脚本：接入 ScalaSemantic MCP](bleep-mcp-setup.md) - 用 BleepScript 复刻 sbt-scalasemantic-mcp 插件的编排逻辑，在 bleep 项目里一条 bleep mcp-setup 命令完成 ScalaSemantic MCP 服务器的接入：装 launcher、prefetch jar、合并写 .mcp.json。
