# ETS2TruckPanel v0.1.0

## 简体中文

首个公开版本：为 ETS2 提供单页触屏驾驶面板、实时遥测和可恢复的一键设置。

**下载 `ETS2TruckPanel-v0.1.0-windows-x64.zip`，不要把下方自动生成的 Source code ZIP 当成安装包。**

1. 完整解压，正常保存并退出 ETS2 和 Touch Portal。
2. 双击 `Setup.cmd`，确认游戏目录、用户资料目录和档案。
3. 启动 Touch Portal，核对并确认自己的 TouchTruck 插件信任提示，在平板选择 TouchTruck 页面。
4. 启动游戏，在停车状态测试按钮。

安装包自带 Python 环境、开源遥测 DLL、页面、原创图标、备份恢复工具及中英文说明书。不包含 Touch Portal 主程序，仍需自行准备 Touch Portal Pro 插件授权；不依赖 Trucky 或其订阅。

只调整所选档案的控制配置并安装 SDK，不修改游戏进度。修改前备份，原键盘/手柄输入保留；未知冲突会被拒绝。双击 `Restore.cmd` 可选择备份恢复，后续已修改的文件不会被强行覆盖。

已验证：31 项本地自动化测试，包括安装/恢复、内置运行环境、中文与空格路径、TCP 断线重连和隐私检查。

初始环境为 Windows x64 / ETS2 1.62.3.3。其他车型、模组、控制器和版本尚未全面验证。遮阳帘依赖车型；部分辅助功能无遥测亮灭反馈。仅舱内看向异常时请检查头部追踪设置；安装器不会自动修改 TrackIR/Tobii。

沿用仓库 GPL-3.0；第三方 SDK、Python 和构建字体保留各自许可。公开版不含 Trucky 图标。

## English

First public release: a single-page ETS2 touch-screen driving panel with live telemetry and reversible offline setup.

**Download `ETS2TruckPanel-v0.1.0-windows-x64.zip`. GitHub's automatic Source code archives are not ready-to-install packages.**

Extract everything, save and fully exit ETS2 and Touch Portal, then double-click `Setup.cmd`. Confirm the game directory, user-data directory and one profile. Restart Touch Portal, review its TouchTruck plugin trust prompt, select the TouchTruck page on the tablet, and test in-game while parked.

The package contains embedded Python, an open-source telemetry DLL, original icons, the page/plugin, backups/restore support and Chinese/English manuals. Touch Portal itself and its plugin-capable Pro license are required separately. Trucky is not required.

Only the selected control configuration and telemetry DLL are installed on the game side. Career saves are not edited. Existing inputs are retained; ambiguous conflicts are rejected. `Restore.cmd` uses per-file backups and refuses to overwrite later user changes.

Validation: 31 local automated tests covering install/restore, the embedded runtime, relocated Unicode/space paths, TCP reconnection and privacy checks. Initial environment: Windows x64, ETS2 1.62.3.3. Wider game/mod/controller compatibility is not exhaustively tested. Sunshade behavior depends on the truck, and some auxiliary controls lack telemetry-backed indicators. Head-tracking settings are not changed automatically.

Project code/artwork retain GPL-3.0. Third-party components keep their respective licenses. Check `SHA256SUMS.txt` and the manuals attached below.
