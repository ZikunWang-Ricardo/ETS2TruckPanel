"""Portable Windows setup; no external Python or third-party packages required."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parent))
from setup_core import apply_plan, patch_profile, restore, sha

PACKAGE=Path(__file__).resolve().parents[1]


def ensure_closed():
    for name in ('eurotrucks2.exe','TouchPortal.exe'):
        p=subprocess.run(['tasklist','/FI',f'IMAGENAME eq {name}','/FO','CSV','/NH'],capture_output=True,text=True)
        if p.returncode: raise RuntimeError('无法确认进程状态，未进行安装。')
        if name.lower() in p.stdout.lower(): raise RuntimeError('请正常保存并退出 '+name+' 后重试；不会强制结束程序。')


def find_documents():
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as k:
        return Path(os.path.expandvars(winreg.QueryValueEx(k,'Personal')[0]))


def find_games():
    import winreg
    roots=[]
    for hive,key,value in [(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam','SteamPath'),
                            (winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\WOW6432Node\Valve\Steam','InstallPath')]:
        try:
            with winreg.OpenKey(hive,key) as k: roots.append(Path(winreg.QueryValueEx(k,value)[0]))
        except OSError: pass
    for root in list(roots):
        vdf=root/'steamapps/libraryfolders.vdf'
        if vdf.exists():
            roots.extend(Path(p.replace('\\\\','\\')) for p in re.findall(r'"path"\s+"([^"]+)"',vdf.read_text(encoding='utf-8-sig')))
    games=[]
    for root in roots:
        candidate=root/'steamapps/common/Euro Truck Simulator 2'
        if (candidate/'bin/win_x64/eurotrucks2.exe').is_file() and candidate not in games: games.append(candidate)
    return games


def find_profiles(home):
    return sorted([*home.glob('profiles/*/controls.sii'),*home.glob('steam_profiles/*/controls.sii')],
                  key=lambda p:p.stat().st_mtime,reverse=True)


def pick(items,title):
    print('\n'+title)
    for i,item in enumerate(items,1): print(f'  {i}. {item}')
    if not items: raise ValueError('没有找到可用项目。请先进入游戏并保存控制设置。')
    response=input('输入编号，回车选择第一项：').strip() or '1'
    if not response.isdecimal() or not 1<=int(response)<=len(items):raise ValueError('编号无效；未改动文件。')
    return items[int(response)-1]


def read_payload(package):
    """Whitelist every installable path; archives may not escape the own plugin directory."""
    result={}
    with zipfile.ZipFile(package/'TouchTruck.tpp') as z:
        for name in z.namelist():
            p=Path(name)
            if name.endswith('/'):continue
            if '\\' in name or p.is_absolute() or '..' in p.parts or p.parts[0]!='TouchTruck':
                raise ValueError('插件包路径无效')
            result[name]=z.read(name)
    return result


def installation_plan(package,game,profile,tp_root=None,*,managed_profile=False):
    package,game,profile=map(lambda p:Path(p).resolve(),(package,game,profile))
    if profile.name!='controls.sii':raise ValueError('仅支持修改 controls.sii，不接受游戏进度文件。')
    if not (game/'bin/win_x64/eurotrucks2.exe').is_file():raise ValueError('所选文件夹不是 ETS2 x64 安装目录。')
    controls=json.loads((package/'shortcuts.json').read_text(encoding='utf-8'))
    dll=(package/'SDK/scs-telemetry.dll').read_bytes()
    manifest=json.loads((package/'SDK/manifest.json').read_text(encoding='utf-8'))
    if sha(dll)!=manifest['dll_sha256']:raise ValueError('SDK 校验失败，未修改文件。')
    plan=[(game/'bin/win_x64/plugins/scs-telemetry.dll',dll),
          (profile,patch_profile(profile.read_bytes(),controls,managed=managed_profile))]
    if tp_root is not None:
        tp_root=Path(tp_root).resolve()
        for name,data in read_payload(package).items():plan.append((tp_root/'plugins'/name,data))
        with zipfile.ZipFile(package/'TouchTruck.tpz') as z:
            for name in z.namelist():
                if name=='pages/TouchTruck.tml':plan.append((tp_root/name,z.read(name)))
                elif re.fullmatch(r'icons/touchtruck_[a-z_]+\.png',name):plan.append((tp_root/name,z.read(name)))
                else:raise ValueError('页面包含非预期文件：'+name)
    return plan


def verify_package():
    manifest=json.loads((PACKAGE/'checksums.json').read_text(encoding='utf-8'))
    for name,digest in manifest.items():
        p=(PACKAGE/name).resolve()
        if not p.is_relative_to(PACKAGE.resolve()) or sha(p.read_bytes())!=digest:
            raise ValueError('分享包文件校验失败：'+name)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--rollback',action='store_true')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    verify_package()
    print('TouchTruck 便携版 — Windows x64 / ETS2\n不安装 Touch Portal，不修改游戏进度、经济、任务或云存档文件。')
    if args.check:
        read_payload(PACKAGE)
        print('分享包校验通过，未安装或修改任何文件。')
        return
    ensure_closed()
    backup_root=PACKAGE/'installation-backups'
    if args.rollback:
        receipts=sorted(backup_root.glob('*/receipt.json'),reverse=True)
        receipt=pick(receipts,'选择要恢复的安装备份（最新在前）：')
        restore(receipt)
        print('恢复完成。游戏进度文件未改动。')
        return
    games=find_games()
    if games:game=pick(games,'选择 ETS2 安装目录：')
    else:game=Path(input('未自动找到游戏，请粘贴 ETS2 安装文件夹完整路径：').strip().strip('"'))
    home=find_documents()/'Euro Truck Simulator 2'
    response=input('用户资料目录：'+str(home)+'\n回车使用此目录；使用 -homedir 的玩家可直接输入自定义目录：').strip().strip('"')
    if response:home=Path(response)
    profiles=find_profiles(home)
    profile=pick(profiles,'选择要增加快捷键的档案（最近使用在前；只修改这一份控制配置）：')
    tp=Path(os.environ['APPDATA'])/'TouchPortal'
    install_tp=tp.is_dir()
    if install_tp:print('检测到 Touch Portal 用户目录，将安装自己的插件和 TouchTruck 页面；同名文件先备份。')
    else:print('未检测到 Touch Portal；将只安装游戏端。以后可手动导入包内 TPP / TPZ。')
    managed=False
    current_hash=sha(profile.read_bytes())
    for receipt in backup_root.glob('*/receipt.json'):
        try:
            records=json.loads(receipt.read_text(encoding='utf-8'))
            managed=managed or any(Path(e['target']).resolve()==profile.resolve() and e.get('written')
                                   and e['after_sha256']==current_hash for e in records)
        except (OSError,ValueError,KeyError,TypeError):continue
    plan=installation_plan(PACKAGE,game,profile,tp if install_tp else None,managed_profile=managed)
    receipt=apply_plan(plan,backup_root)
    print('\n安装完成。备份清单：'+str(receipt))
    print('重新启动 Touch Portal，按提示信任自己安装的 TouchTruck 插件；在 iPad 选择 TouchTruck 页面。')
    print('再启动游戏并进入驾驶画面。详见中文说明书.html。')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('\n未完成：'+str(exc))
        print('若提示权限不足，退出游戏和 Touch Portal 后，以同一 Windows 账户“以管理员身份运行” Setup.cmd。')
        sys.exit(1)
