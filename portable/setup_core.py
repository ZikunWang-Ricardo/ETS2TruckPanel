"""Shareable installer core: additive bindings and journalled, reversible writes."""
import hashlib
import json
import os
from pathlib import Path
import re
import time
import uuid

CHORD='keyboard.rctrl?0 & keyboard.rshift?0'
LEGACY='keyboard.lctrl?0 & keyboard.lalt?0'
KEYS=[*(('f'+str(i),58+i if i<=10 else 76+i) for i in range(1,13)),
      ('num0',82),('num1',79),('num2',80),('num3',81),('num4',75),
      ('num5',76),('num6',77),('num7',71),('num8',72),('num9',73),
      *((f'key{i}',i+1) for i in range(1,8))]


def portable_controls(controls):
    result=json.loads(json.dumps(controls))
    if len(result)>len(KEYS): raise ValueError('Too many controls')
    for c,(key,scan) in zip(result,KEYS):
        c.update(bind=key,keys=[285,54,scan])
        c.pop('unavailable',None)
    return result


def patch_profile(raw, controls, *, managed=False):
    text=raw.decode('utf-8-sig')
    if not text.lstrip().startswith('SiiNunit'): raise ValueError('控制配置不是明文 SII；请先用游戏保存一次设置。')
    bindings={c['mix']:c['bind'] for c in controls}
    if len(set(bindings.values()))!=len(bindings): raise ValueError('Duplicate button shortcuts')
    for name in bindings:
        if len(re.findall(r'"mix '+re.escape(name)+r' `([^`]*)`"',text))!=1:
            raise ValueError('游戏版本缺少或重复的动作：'+name+'；未改动任何文件。')
    # A matching expression alone is NOT evidence we own it. A matching prior
    # installation receipt is required before stripping any reserved-chord wrappers.
    if CHORD in text and not managed:
        raise ValueError('发现已有右 Ctrl＋右 Shift 自定义组合，且没有匹配的本包安装记录；未修改文件。请先恢复旧版或人工检查。')
    for chord in ((CHORD,) if managed else ()):
        text=re.sub(r'\(keyboard\.([a-z0-9]+)\?0 & !\('+re.escape(chord)+r'\)\)',r'keyboard.\1?0',text)
        for name in bindings:
            pattern=r'("mix '+re.escape(name)+r' `)\('+re.escape(chord)+r' & keyboard\.[a-z0-9]+\?0\) \| \(([^`]*)\)(`")'
            text=re.sub(pattern,lambda m:m[1]+m[2]+m[3],text)
    # Refuse unknown custom use of this reserved chord rather than stealing it.
    if CHORD in text:
        raise ValueError('发现已有的自定义修饰键组合，无法安全自动迁移；未修改文件。')
    for key in bindings.values():
        text=re.sub(r'keyboard\.'+key+r'\?0\b',lambda m:f'({m[0]} & !({CHORD}))',text)
    for name,key in bindings.items():
        pattern=r'("mix '+re.escape(name)+r' `)([^`]*)(`")'
        text=re.sub(pattern,lambda m:m[1]+f'({CHORD} & keyboard.{key}?0) | ('+m[2]+')'+m[3],text)
    return (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+text.encode('utf-8')


def sha(data): return hashlib.sha256(data).hexdigest()


def atomic_write(target, data):
    target=Path(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_name(target.name+'.touchtruck-'+uuid.uuid4().hex+'.tmp')
    try:
        temp.write_bytes(data)
        os.replace(temp,target)
    finally:
        if temp.exists(): temp.unlink()


def apply_plan(plan, backup_root):
    """All content prepared first. One receipt records every file before mutation."""
    paths=[str(Path(p).resolve()).lower() for p,_ in plan]
    if len(paths)!=len(set(paths)): raise ValueError('Duplicate installation targets')
    folder=Path(backup_root)/(time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
    folder.mkdir(parents=True)
    entries=[]
    # Snapshot every original before writing any target.
    for i,(target,data) in enumerate(plan):
        target=Path(target).resolve()
        old=target.read_bytes() if target.exists() else None
        if old is not None: (folder/f'{i}.bak').write_bytes(old)
        entries.append({'target':str(target),'backup':f'{i}.bak' if old is not None else None,
                        'before_sha256':sha(old) if old is not None else None,
                        'after_sha256':sha(data),'written':False})
    receipt=folder/'receipt.json'
    def save(): atomic_write(receipt,json.dumps(entries,ensure_ascii=False,indent=2).encode('utf-8'))
    save()
    try:
        for entry,(_,data) in zip(entries,plan):
            target=Path(entry['target'])
            current=sha(target.read_bytes()) if target.exists() else None
            if current!=entry['before_sha256']: raise RuntimeError('安装时文件发生变化：'+str(target))
            entry['written']=True
            save()  # Journal intent before mutation, permitting recovery after interruption.
            atomic_write(target,data)
    except Exception:
        for entry in reversed(entries):
            target=Path(entry['target'])
            if entry['written'] and target.exists() and sha(target.read_bytes())==entry['after_sha256']:
                if entry['backup']: atomic_write(target,(folder/entry['backup']).read_bytes())
                else: target.unlink()
        raise
    return receipt


def restore(receipt):
    receipt=Path(receipt)
    entries=json.loads(receipt.read_text(encoding='utf-8'))
    if not isinstance(entries,list): raise ValueError('Invalid receipt')
    pending=[]
    for e in entries:
        if not e['written']: continue
        target=Path(e['target'])
        data=(receipt.parent/e['backup']).read_bytes() if e['backup'] else None
        if data is not None and sha(data)!=e['before_sha256']: raise ValueError('备份校验失败')
        current=sha(target.read_bytes()) if target.exists() else None
        if current==e['before_sha256']: continue
        if current!=e['after_sha256']:
            raise ValueError('文件已被后续修改，为保护现有设置，不覆盖：'+str(target))
        pending.append((target,data))
    for target,data in reversed(pending):
        if data is None: target.unlink()
        else: atomic_write(target,data)
