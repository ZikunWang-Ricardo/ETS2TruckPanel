"""Build a clean offline share ZIP from a whitelist, never from user backups."""
import hashlib
import html
import io
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'portable'))
from setup_core import portable_controls

OUTPUT=ROOT/'release/TouchTruck-Share-Windows-x64'
GENERATED=set()


def write(name,data):
    GENERATED.add(name)
    p=OUTPUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(data.encode('utf-8') if isinstance(data,str) else data)


def build():
    if OUTPUT.exists():
        # A deterministic whitelist is used; refuse dirty staging rather than packaging stale private files.
        expected={'setup','SDK','licenses','Setup.cmd','Restore.cmd','TouchTruck.tpz','TouchTruck.tpp',
                  'shortcuts.json','preview.png','中文说明书.md','中文说明书.html','checksums.json','README.txt','_setup_runtime','docs'}
        unexpected={p.name for p in OUTPUT.iterdir()}-expected
        if unexpected:raise RuntimeError('Staging contains unexpected files: '+str(unexpected))
    OUTPUT.mkdir(parents=True,exist_ok=True)
    controls=portable_controls(json.loads((ROOT/'config/controls.json').read_text(encoding='utf-8')))
    write('shortcuts.json',json.dumps(controls,ensure_ascii=False,indent=2))
    write('TouchTruck.tpz',(ROOT/'dist/TouchTruck.tpz').read_bytes())
    write('preview.png',(ROOT/'dist/preview-demo.png').read_bytes())
    for name in ('Setup.cmd','Restore.cmd'):
        write(name,(ROOT/'portable'/name).read_text(encoding='utf-8').replace('\n','\r\n'))
    for name in ('install.py','setup_core.py','bootstrap.ps1'):
        data=(ROOT/'portable'/name).read_bytes()
        # Windows PowerShell 5.1 reads UTF-8 with BOM reliably.
        if name.endswith('.ps1'):data=b'\xef\xbb\xbf'+data
        write('setup/'+name,data)
    plugin=json.loads((ROOT/'plugin/entry.tp').read_text(encoding='utf-8'))
    plugin['version']=2
    plugin['plugin_start_cmd']='"%TP_PLUGIN_FOLDER%/TouchTruck/runtime/pythonw.exe" "%TP_PLUGIN_FOLDER%/TouchTruck/app/run_bridge.py"'
    runtime_source=ROOT/'vendor/python-3.13.12-embed-amd64.zip'
    runtime_files={}
    with zipfile.ZipFile(runtime_source) as z:
        for name in z.namelist():
            if '/' in name or '\\' in name:raise ValueError('Unexpected runtime layout')
            runtime_files[name]=z.read(name)
    # This is the sole addition to Python's isolated module search path.
    pth=next(n for n in runtime_files if n.endswith('._pth'))
    runtime_files[pth]=runtime_files[pth].replace(b'#import site',b'../app\n#import site')
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('TouchTruck/entry.tp',json.dumps(plugin,ensure_ascii=False,indent=2))
        for name,data in runtime_files.items():z.writestr('TouchTruck/runtime/'+name,data)
        for name in ('__init__.py','bridge.py','input.py','telemetry.py'):
            z.writestr('TouchTruck/app/touchtruck/'+name,(ROOT/'touchtruck'/name).read_bytes())
        z.writestr('TouchTruck/app/config/controls.json',json.dumps(controls,ensure_ascii=False,indent=2))
        z.writestr('TouchTruck/app/run_bridge.py','from touchtruck.bridge import main\nif __name__ == "__main__": main()\n')
    write('TouchTruck.tpp',buffer.getvalue())
    dll=(ROOT/'vendor/rencloud/release_v_1_12_1/Win64/scs-telemetry.dll').read_bytes()
    write('SDK/scs-telemetry.dll',dll)
    write('SDK/manifest.json',json.dumps({'release':'V.1.12.1','dll_sha256':hashlib.sha256(dll).hexdigest(),
                                        'source':'https://github.com/RenCloud/scs-sdk-plugin/releases/tag/V.1.12.1'},indent=2))
    write('licenses/SCS-Telemetry-MIT.txt',(ROOT/'vendor/SCS-Telemetry-MIT.txt').read_bytes())
    license_name=next(n for n in runtime_files if n.lower()=='license.txt')
    write('licenses/Python-LICENSE.txt',runtime_files[license_name])
    write('SDK/官方下载链接.txt',
          'SCS 官方 Telemetry SDK：\nhttps://modding.scssoft.com/wiki/Documentation/Engine/SDK/Telemetry\n\n'
          '本包使用的 RenCloud 开源遥测插件（固定 V.1.12.1 / revision 12）：\nhttps://github.com/RenCloud/scs-sdk-plugin/releases/tag/V.1.12.1\n\n'
          '自带 Python 嵌入式环境：\nhttps://www.python.org/ftp/python/3.13.12/python-3.13.12-embed-amd64.zip\n'
          'Python 压缩包 SHA256：'+hashlib.sha256(runtime_source.read_bytes()).hexdigest()+'\n')
    rows=[]
    for c in controls:
        rows.append(f"| {c['label']} | 右 Ctrl＋右 Shift＋{c['bind'].upper()} | {'按住，最多8秒' if c.get('hold') else '点按'} |")
    table='\n'.join(['| 功能 | 分享版组合键 | 操作 |','|---|---|---|',*rows])
    text='''# TouchTruck 中文说明书

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

'''+table+'''

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
公开版全部仪表图标由本项目自行绘制，不包含 Trucky 图标包。项目代码和自绘图标沿用仓库 GPL-3.0 许可证；第三方 SDK 和 Python 分别遵循其原有许可证。
本项目使用的 Python 桥接源码位于 TPP 的 TouchTruck/app/touchtruck/，安装器源码在 setup/。
'''
    write('中文说明书.md',text)
    # Offline readable/printable Chinese manual, including its real shortcut table.
    chunks=[]
    in_table=False
    for line in text.splitlines():
        if line.startswith('|'):
            if line.startswith('|---'):continue
            if not in_table:chunks.append('<table>');in_table=True
            chunks.append('<tr>'+''.join('<td>'+html.escape(cell.strip())+'</td>' for cell in line.strip('|').split('|'))+'</tr>')
            continue
        if in_table:chunks.append('</table>');in_table=False
        if line.startswith('# '):chunks.append('<h1>'+html.escape(line[2:])+'</h1>')
        elif line.startswith('## '):chunks.append('<h2>'+html.escape(line[3:])+'</h2>')
        elif line:chunks.append('<p>'+html.escape(line)+'</p>')
    if in_table:chunks.append('</table>')
    write('中文说明书.html','<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>TouchTruck 中文说明书</title><style>body{max-width:960px;margin:40px auto;padding:0 24px;font:17px/1.8 "Microsoft YaHei",sans-serif;color:#20313d}h1,h2{color:#183c4a}table{border-collapse:collapse;width:100%}td{border:1px solid #c8d5dc;padding:7px 12px}tr:first-child{background:#e4eef1;font-weight:bold}p{overflow-wrap:anywhere}@media print{body{margin:0;font-size:11pt}h2{break-after:avoid}tr{break-inside:avoid}}</style>'+''.join(chunks)+'</html>')
    write('README.txt','先解压整个文件夹，退出游戏与 Touch Portal，然后双击 Setup.cmd。\n详细中文说明：中文说明书.html\n恢复：Restore.cmd\n不包含 Touch Portal 主程序，不需要安装 Python，不包含制作者存档或个人备份。\n')
    write('licenses/ETS2TruckPanel-GPL-3.0.txt',(ROOT/'LICENSE').read_bytes())
    write('licenses/Noto-OFL.txt',(ROOT/'vendor/Noto-OFL.txt').read_bytes())
    for lang in ('en','zh-CN'):
        write('docs/Manual.'+lang+'.md',(ROOT/('docs/MANUAL.'+lang+'.md')).read_bytes())
    # No accidental files may enter the share artifact.
    checksums={name:hashlib.sha256((OUTPUT/name).read_bytes()).hexdigest() for name in sorted(GENERATED)}
    write('checksums.json',json.dumps(checksums,ensure_ascii=False,indent=2))
    destination=ROOT/'dist/ETS2TruckPanel-v0.1.0-windows-x64.zip'
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as z:
        for name in [*checksums,'checksums.json']:z.write(OUTPUT/name,'TouchTruck-Share-Windows-x64/'+name)
    print(destination)
    print(f'{destination.stat().st_size/1024/1024:.1f} MiB; {len(checksums)+1} files; runtime self-contained')


if __name__=='__main__':build()
