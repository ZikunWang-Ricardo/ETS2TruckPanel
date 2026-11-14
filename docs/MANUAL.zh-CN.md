# ETS2TruckPanel 中文说明书

适用于 Windows 10/11 x64、ETS2 的 64 位版本。针对 iPad Pro 11 英寸横屏设计。
本包不包含、不安装 Touch Portal 主程序或手机 App；使用插件仍需接收者已有 Touch Portal Pro。
本包自带独立 Python 3.13.12 嵌入式环境，无需安装 Python、pip、Trucky 或 Trucky Prime。支持离线安装。

## 一、快速开始

1. 把整个 ZIP 解压到本机可写文件夹，不能直接在压缩包内运行。
2. 先正常保存并退出 ETS2，再完整退出 Touch Portal。安装器不会强制结束任何程序。
3. 双击 Setup.cmd。自动寻找 Steam 各游戏库；找不到时输入游戏安装目录。
4. 选择需要配置的档案编号，回车默认选最近使用的一份。只改选中档案；先确认列表，避免选错。
5. 已有 Touch Portal 用户目录时，会自动放入自己的 TouchTruck 插件、便携环境及页面。没有该目录时，仅配置游戏，保留 TPP/TPZ 供以后导入。
6. 安装完成后启动 Touch Portal。如出现 TouchTruck 插件信任提示，核对命令指向自己的插件目录内 runtime/pythonw.exe，再自行确认。
7. 在 iPad 中选择 TouchTruck 页面，启动游戏并进入驾驶画面，先停车核对仪表和按钮。

双击一次启动即可设置环境；游戏目录或档案不唯一时会让你选择，不会猜测后覆盖所有档案。权限不足时会报错并回退；可以用同一 Windows 账户“以管理员身份运行”Setup.cmd 重试。

## 二、不会影响哪些数据

游戏端只写两个位置：游戏 bin/win_x64/plugins/scs-telemetry.dll，以及选中档案的 controls.sii。
不会写入 save、game.sii、profile.sii、金钱、等级、车辆、任务或 Steam 云存档进度文件；不会更换手柄设备、摇杆轴、方向盘或踏板配置。
新的组合键作为额外输入加入，原有键盘及手柄表达式保留。组合键使用右 Ctrl＋右 Shift，避开默认左 Ctrl 降挡与左 Shift 升挡。
为避免组合键同时触发原按键动作，只在组合键按住时屏蔽对应基础键的原动作；普通单按仍保留。
游戏版本若没有本页面需要的动作，安装器会拒绝写入，而不会把按钮映射到其他功能。
会先备份同名 SDK、控制配置和自己的同名 Touch Portal 文件。安装中途失败会尝试还原已写入文件。仍建议保留备份，任何程序都不能对断电、磁盘损坏或云同步冲突作绝对保证。

## 三、备份与一键恢复

安装备份位于 installation-backups/日期-编号/，含原文件及 receipt.json。此文件夹在接收者第一次安装时才生成，本分享包不含发送者的存档或备份。
退出游戏和 Touch Portal 后双击 Restore.cmd，选择备份即可恢复。后续手动改过配置时，恢复器会拒绝覆盖，避免丢失新设置；请先比较原文件和备份。
不要删除备份后再期待恢复。再次分享时请分享原始 ZIP，切勿把自己安装后的 installation-backups、_setup_runtime、运行日志重新打包。

## 四、Touch Portal 文件

TouchTruck.tpp：独立插件＋Python 运行环境＋桥接源码，使用插件目录相对路径，不依赖制作者电脑。
TouchTruck.tpz：单页面和图标。preview.png 是模拟读数与全部点亮示意，不是实时游戏截图。
若选择手动安装：先在 Touch Portal 导入 TPP 并确认自己的插件启动命令，再导入 TPZ。只手动导入 TPP/TPZ 不会自动修改游戏按键，游戏端仍需运行 Setup.cmd。
运行时文件位于 Touch Portal 用户目录 plugins/TouchTruck/；日志位于其 app/logs/bridge.log。关闭 Touch Portal 会通知桥接退出。

## 五、按钮与快捷键

分享版为全部按钮分配额外组合键，避免依赖其他玩家的默认 E/H 等按键。因此本表与制作电脑早期版本不同，不会自动改动制作电脑。

| 功能 | 分享版组合键 | 操作 |
|---|---|---|
| 引擎启停 | 右 Ctrl＋右 Shift＋F1 | 点按 |
| 驻车制动 | 右 Ctrl＋右 Shift＋F2 | 点按 |
| 挂车连接 | 右 Ctrl＋右 Shift＋F3 | 点按 |
| 差速锁 | 右 Ctrl＋右 Shift＋F4 | 点按 |
| 提升桥 | 右 Ctrl＋右 Shift＋F5 | 点按 |
| 发动机制动 | 右 Ctrl＋右 Shift＋F6 | 按住，最多8秒 |
| 舱内视角 | 右 Ctrl＋右 Shift＋F7 | 点按 |
| 俯视视角 | 右 Ctrl＋右 Shift＋F8 | 点按 |
| 左转向 | 右 Ctrl＋右 Shift＋F9 | 点按 |
| 右转向 | 右 Ctrl＋右 Shift＋F10 | 点按 |
| 危险报警灯 | 右 Ctrl＋右 Shift＋F11 | 点按 |
| 灯光切换 | 右 Ctrl＋右 Shift＋F12 | 点按 |
| 远光灯 | 右 Ctrl＋右 Shift＋NUM0 | 点按 |
| 灯光喇叭 | 右 Ctrl＋右 Shift＋NUM1 | 按住，最多8秒 |
| 喇叭 | 右 Ctrl＋右 Shift＋NUM2 | 按住，最多8秒 |
| 雨刷 | 右 Ctrl＋右 Shift＋NUM3 | 点按 |
| 巡航启停 | 右 Ctrl＋右 Shift＋NUM4 | 点按 |
| 巡航减速 | 右 Ctrl＋右 Shift＋NUM5 | 点按 |
| 巡航加速 | 右 Ctrl＋右 Shift＋NUM6 | 点按 |
| 车道辅助模式 | 右 Ctrl＋右 Shift＋NUM7 | 点按 |
| 车道保持辅助 | 右 Ctrl＋右 Shift＋NUM8 | 点按 |
| 车内照明灯 | 右 Ctrl＋右 Shift＋NUM9 | 点按 |
| 遮阳帘升 | 右 Ctrl＋右 Shift＋KEY1 | 按住，最多8秒 |
| 遮阳帘降 | 右 Ctrl＋右 Shift＋KEY2 | 按住，最多8秒 |
| 左窗打开 | 右 Ctrl＋右 Shift＋KEY3 | 按住，最多8秒 |
| 左窗关闭 | 右 Ctrl＋右 Shift＋KEY4 | 按住，最多8秒 |
| 右窗打开 | 右 Ctrl＋右 Shift＋KEY5 | 按住，最多8秒 |
| 右窗关闭 | 右 Ctrl＋右 Shift＋KEY6 | 按住，最多8秒 |
| ACC跟车模式 | 右 Ctrl＋右 Shift＋KEY7 | 点按 |

## 六、使用说明与限制

游戏必须位于前台才发送输入。喇叭、灯光喇叭、发动机制动、车窗和遮阳帘按住操作，松开释放；为应对丢失松开事件，最多保持8秒，可松开后再按。
遮阳帘目前控制驾驶员左侧；车型没有可动遮阳帘时游戏不会产生效果。
巡航启停与 ACC 跟车模式是不同游戏动作；巡航速度、车辆状态及驾驶辅助条件仍由游戏决定。
车内照明灯对应 cabinlight；驾驶辅助、车窗位置、遮阳帘和车内照明灯没有实现真实遥测开关反馈，不伪造状态。
显示单位固定为 km/h、升和 km。没有游戏遥测时数字显示“—”，连接状态显示未连接。
SDK 固定为 RenCloud V.1.12.1 / revision 12；未知版本会停止解析，不能盲目替换 DLL。
安装器不会关闭 TrackIR/Tobii。若仅舱内右摇杆无法看向，先检查头部追踪；需要停用时应自己备份并调整游戏设置，避免影响使用头部追踪的玩家。
自动寻找标准 Documents（含系统重定向的 OneDrive）下 profiles 和 steam_profiles；备份档案目录不会参与选择。自定义用户目录可手动输入。
不支持加密/二进制 controls.sii 或缺少所需动作的旧游戏版本；遇到这种情况会明确报错，不改写。

## 七、常见问题

安装器提示游戏或 Touch Portal 正在运行：完整退出后再运行；最小化到托盘不等于退出。
游戏目录受保护：用同一账户以管理员身份启动，不要使用其他 Windows 账户的管理员凭据，否则可能找到不同用户资料。
按钮无效：确认进入的是选中的档案、TouchTruck 插件已配对、游戏在前台；游戏与桥接需处于兼容的权限级别。
按钮触发错误功能：不要混用旧版快捷键配置与分享版插件。本包有匹配的安装记录且配置未被后续改动时，可以重复安装；遇到旧版或无法证明来源的右 Ctrl＋右 Shift 组合，安装器会拒绝覆盖，请先恢复旧版或人工检查。
修改设置后云同步提示冲突：检查时间与备份，自行选择正确版本，不要盲目恢复全部进度。
需要核对文件：powershell -NoProfile -ExecutionPolicy Bypass -File setup/bootstrap.ps1 -Check 只校验分享包，不安装。

## 八、来源、许可与目录

SCS SDK 官方：https://modding.scssoft.com/wiki/Documentation/Engine/SDK/Telemetry
RenCloud 插件：https://github.com/RenCloud/scs-sdk-plugin/releases/tag/V.1.12.1
Python：https://www.python.org/downloads/release/python-31312/
Touch Portal API：https://www.touch-portal.com/api/
SDK 及 Python 许可证在 licenses/。SDK 下载链接与固定哈希在 SDK/，本包文件哈希在 checksums.json。
公开版全部图标为本项目自行绘制。代码与自绘图标遵循仓库 GPL-3.0 许可证；第三方 SDK 和 Python 保留各自许可。
本项目使用的 Python 桥接源码位于 TPP 的 TouchTruck/app/touchtruck/，安装器源码在 setup/。
