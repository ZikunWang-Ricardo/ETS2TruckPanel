# ETS2TruckPanel — English User Manual

[中文说明书](MANUAL.zh-CN.md) · [Project home](../README.md)

## 1. What is included

This project provides a Touch Portal truck-control page and an independent ETS2 telemetry bridge. The installed plugin is named **TouchTruck** for compatibility with its existing action/state IDs.

The downloadable Windows x64 package contains:

- `Setup.cmd`: offline setup launcher.
- `Restore.cmd`: restore a selected installation backup.
- `TouchTruck.tpp`: plugin, bridge source and embedded Python 3.13.12 runtime.
- `TouchTruck.tpz`: page and original instrument icons.
- `SDK/`: pinned RenCloud V.1.12.1 telemetry DLL, checksum and official SDK/download links.
- Chinese HTML/Markdown instructions and both language manuals under `docs/`.
- `checksums.json` and third-party license notices.

It does not include Touch Portal itself, Trucky, personal game saves or the developer's backups. Python, pip and a Trucky subscription are not required. Touch Portal with a plugin-capable Pro license is required separately.

## 2. Requirements

Windows 10/11 x64 and ETS2 x64. Initial development/testing used ETS2 1.62.3.3. The installer refuses profiles missing required actions rather than assigning unrelated commands. Other game versions, mods and controllers have not been exhaustively certified.

The game must have been run at least once and its control settings saved as a readable `controls.sii`. Binary/encrypted configuration files are not supported. This package targets ETS2, not an ATS automatic installer.

## 3. Install

1. Download the Windows binary ZIP from GitHub Releases. GitHub's automatic **Source code** archives do not include the runtime or generated installer package.
2. Extract the entire ZIP into a writable local folder. Do not run it from within an archive viewer.
3. Save your game and fully exit ETS2 and Touch Portal. Minimizing Touch Portal to its tray is not exiting it. The setup program will not force-close either application.
4. Double-click `Setup.cmd`.
5. Choose the detected Steam game directory. When detection fails, paste the ETS2 installation folder containing `bin/win_x64/eurotrucks2.exe`.
6. Confirm the game user-data directory. Press Enter for the detected Documents/OneDrive location, or paste the directory supplied to a custom `-homedir` launch argument.
7. Choose **one** profile from `profiles` or `steam_profiles`. Most recently modified profiles appear first. Enter accepts the first entry; confirm that it is your intended profile.
8. Existing Touch Portal user data is detected automatically. Setup installs its own plugin, embedded environment, page and icons there. If no Touch Portal directory exists, only the game side is configured; the TPP and TPZ remain available for manual import later.
9. Restart Touch Portal. If its trust dialog appears, verify that the command references the plugin's own `runtime/pythonw.exe`, then personally confirm it.
10. Select the **TouchTruck** page on your tablet, start ETS2 and enter the driving view. Test controls while parked.

The installer console is currently Chinese. Its main prompts mean:

| Prompt | Meaning |
|---|---|
| 选择 ETS2 安装目录 | Select game installation directory |
| 用户资料目录 | Game user-data directory; Enter accepts the shown default |
| 选择要增加快捷键的档案 | Select the one profile to configure |
| 输入编号，回车选择第一项 | Enter a list number; Enter alone selects the first |
| 安装完成 | Installation completed |
| 未完成 | Setup stopped; read the reason before retrying |

If the game directory requires additional permissions, retry `Setup.cmd` with **Run as administrator using the same Windows account**. Using another account's administrator credentials may point setup at the wrong Documents/AppData directories. Normal setups do not install services, drivers or modify the system PATH.

## 4. Save and input preservation

Game-side changes are limited to:

- `bin/win_x64/plugins/scs-telemetry.dll` in the selected game installation.
- `controls.sii` in the selected profile.

Career saves, money, jobs, trucks, `game.sii` and `profile.sii` are not edited. Existing keyboard/controller expressions and controller device/axis configuration are retained. The new panel commands are additional right-Ctrl + right-Shift combinations; ordinary base-key actions remain available when this chord is not held.

Unknown existing use of the reserved modifier chord is rejected rather than silently replaced. Reinstallation may unwrap its own prior bindings only when a matching local installation receipt proves ownership of the current profile bytes. If settings changed afterward, restore or inspect them first. A similar-looking expression alone is not treated as permission to delete a user's shortcut.

Every target is backed up before any writes. Writes are journalled, and failed setup attempts try to restore already-written targets. This does not guarantee protection against power loss, disk failure or Steam cloud-sync conflicts. Keep your backups and resolve cloud conflicts deliberately.

## 5. Restore

Exit ETS2 and Touch Portal, double-click `Restore.cmd`, and select an installation receipt from `installation-backups/`.

Restoration checks all targets first. If a file has been changed after installation, it refuses to overwrite that file rather than losing newer settings. Backups and the receipt must be kept together. A restore removes files that setup created and restores originals that setup replaced; it does not delete gameplay progress.

To share again, redistribute the original downloaded ZIP. Do not repackage a folder after setup: it may now contain the recipient's backups, paths, runtime cache or logs.

## 6. Controls

All shortcuts below are **right Ctrl + right Shift + the listed key**. These are extra bindings, not replacements for existing inputs. They intentionally differ from the earliest private development version.

| Button | Additional key | Behavior |
|---|---|---|
| Engine | F1 | Tap |
| Parking brake | F2 | Tap |
| Trailer coupling | F3 | Tap |
| Differential lock | F4 | Tap |
| Lift axle | F5 | Tap |
| Engine brake | F6 | Hold |
| Interior camera | F7 | Tap |
| Top-down camera | F8 | Tap |
| Left turn signal | F9 | Tap |
| Right turn signal | F10 | Tap |
| Hazards | F11 | Tap |
| Light cycle | F12 | Tap |
| High beams | Numpad 0 | Tap |
| Light horn | Numpad 1 | Hold |
| Horn | Numpad 2 | Hold |
| Wipers | Numpad 3 | Tap |
| Cruise activation | Numpad 4 | Tap |
| Cruise decrease | Numpad 5 | Tap |
| Cruise increase | Numpad 6 | Tap |
| Lane-assistance mode | Numpad 7 | Tap |
| Lane keeping | Numpad 8 | Tap |
| Cabin light | Numpad 9 | Tap |
| Driver's sunshade up | Number row 1 | Hold |
| Driver's sunshade down | Number row 2 | Hold |
| Left window open | Number row 3 | Hold |
| Left window close | Number row 4 | Hold |
| Right window open | Number row 5 | Hold |
| Right window close | Number row 6 | Hold |
| ACC following mode | Number row 7 | Tap |

## 7. Runtime behavior

Input is sent only while the game window is in the foreground. Hold actions release on button-up, focus loss, Touch Portal disconnect or page-change broadcasts. An eight-second limit protects against a lost release event; release and press again for longer movement. Losing an established telemetry connection releases currently held controls; subsequent explicit controls can still work independently of telemetry.

The dashboard uses km/h, liters and kilometers. Missing/stale telemetry clears readings instead of showing old data as live. SDK memory layout revision 12 is pinned; unknown revisions are not decoded.

Cruise activation and ACC following/distance mode are different game commands. Configure the desired ACC mode and meet the game's speed/vehicle conditions before engaging cruise. Sunshade movement depends on the selected truck; the panel currently controls the driver's left-side shade.

Lane-assistance modes, windows, sunshade and cabin light do not have implemented telemetry-backed on/off feedback. Their icons do not claim a game state the bridge cannot read.

## 8. Manual Touch Portal import

Import `TouchTruck.tpp` first, review its startup command and trust it when appropriate, then import `TouchTruck.tpz`. All runtime dependencies are inside the TPP, and the command uses the Touch Portal plugin-folder placeholder rather than a developer machine path.

Manual TPP/TPZ import alone does not configure game shortcuts. Run the game-side setup as well. The installed bridge lives under the Touch Portal user directory at `plugins/TouchTruck/app/`; rotating logs are under `app/logs/bridge.log`.

## 9. Troubleshooting

- **Only interior look is broken:** inspect head tracking/TrackIR/Tobii first. Setup does not disable these because other users may rely on them.
- **Buttons do nothing:** check the selected game profile, plugin pairing, game foreground focus and application privilege levels.
- **Wrong function is triggered:** do not mix old private shortcut settings with the public plugin. Inspect the shortcut table and installation receipt before reinstalling.
- **Telemetry missing:** check the DLL location, restart the game after installation, and inspect plugin logs. An old game or a changed SDK layout may be incompatible.
- **Read-only configuration / missing actions:** setup stops without modifying the profile. Save settings in a compatible game version and retry.
- **Steam sync conflict:** inspect timestamps and backups and choose the correct version yourself; never blindly replace an entire career save.

Read-only integrity check from the extracted package:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File setup/bootstrap.ps1 -Check
```

## 10. Sources and licenses

- SCS SDK: https://modding.scssoft.com/wiki/Documentation/Engine/SDK/Telemetry
- RenCloud plugin/source: https://github.com/RenCloud/scs-sdk-plugin/releases/tag/V.1.12.1
- Python: https://www.python.org/downloads/release/python-31312/
- Touch Portal API: https://www.touch-portal.com/api/

Project source and original icons follow the repository's existing GPL-3.0 license. RenCloud and Python retain their own notices under `licenses/` in the release. Public packages contain no Trucky icon pack and no proprietary Touch Portal installer.
