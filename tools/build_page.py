"""Build importable Touch Portal packages and an iPad landscape preview."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from touchtruck.telemetry import FLAGS
from tools.instrument_icons import draw_instrument

FONT = ROOT/'vendor/NotoSansCJKsc-Regular.otf'
W, H = 200, 224
BG = '#11171D'
OFF = '#A3AEB6'


def font(size): return ImageFont.truetype(str(FONT), size)
def rgba(color): return tuple(bytes.fromhex(color.lstrip('#'))) + (255,)
def signed(color):
    n = int(color.lstrip('#'), 16) | 0xff000000
    return n - 0x100000000


def symbol(d, kind, color):
    # Small vector-native supplements; existing bitmap pack remains the main source.
    lw = 5
    if kind in ('lane', 'lane_mode'):
        d.line([(105,135),(124,43)], fill=color, width=lw)
        d.line([(215,135),(196,43)], fill=color, width=lw)
        d.rounded_rectangle((143,77,177,127), radius=7, outline=color, width=lw)
        if kind == 'lane_mode': d.text((160,49),'M',font=font(24),fill=color,anchor='mm')
    elif kind == 'acc':
        d.rounded_rectangle((130,42,190,82),radius=8,outline=color,width=lw)
        for y in (96,111,126): d.line((136,y,184,y),fill=color,width=3)
    elif kind.startswith('shade'):
        d.rounded_rectangle((100,43,220,127),radius=6,outline=color,width=lw)
        for y in (56,68,80): d.line((106,y,214,y),fill=color,width=3)
        up = kind.endswith('up')
        y1, y2 = (113,94) if up else (94,113)
        d.line((160,y1,160,y2), fill=color, width=4)
        d.line([(150,y2+(9 if up else -9)),(160,y2),(170,y2+(9 if up else -9))],fill=color,width=4)
    elif kind == 'lamp':
        d.arc((137,43,183,91),180,360,fill=color,width=lw)
        d.line((137,68,144,103,176,103,183,68),fill=color,width=lw)
        d.line((147,114,173,114),fill=color,width=lw)
    elif kind == 'flash':
        d.arc((133,42,211,126),75,285,fill=color,width=lw)
        for y in (54,82,110): d.line((107,y,127,y),fill=color,width=lw)
        d.polygon([(167,60),(151,88),(165,88),(157,111),(184,78),(169,78)],fill=color)
    elif kind == 'cab':
        d.rounded_rectangle((108,43,212,129),radius=12,outline=color,width=lw)
        d.line((116,82,204,82),fill=color,width=lw)
        d.ellipse((137,91,183,137),outline=color,width=lw)
        d.line((160,111,160,135),fill=color,width=3)
    elif kind == 'top':
        d.rounded_rectangle((136,41,184,130),radius=9,outline=color,width=lw)
        d.line((142,64,178,64),fill=color,width=lw)
        d.line((142,102,178,102),fill=color,width=3)
        for x in (112,208):
            d.line((x,71,x,103),fill=color,width=3)
            d.line([(x-7,79),(x,69),(x+7,79)],fill=color,width=3)


def tile(control, archive, on=False):
    image = Image.new('RGBA',(W,H),BG)
    d = ImageDraw.Draw(image)
    unavailable = bool(control.get('unavailable'))
    color = control.get('color','#63D8AD') if on else ('#667079' if unavailable else OFF)
    d.rounded_rectangle((3,3,W-4,H-4),radius=17,fill='#202830',outline=color if on else '#35414B',width=2)
    d.line((26,17,W-26,17),fill='#33404B',width=1)
    glyph=Image.new('RGBA',(320,160),(0,0,0,0))
    draw_instrument(ImageDraw.Draw(glyph),control['id'],color,font)
    glyph=glyph.crop((90,30,230,145))
    image.alpha_composite(glyph,((W-glyph.width)//2,29))
    d.text((W//2,172),control['label'],font=font(23),fill=color,anchor='mm')
    if unavailable: hint='待绑定'
    elif control.get('hold'): hint='按住操作'
    elif control['id']=='acc_mode': hint='距离 / 模式切换'
    elif control['id']=='cruise': hint='ACC需先设定模式'
    elif control.get('state'): hint='实时状态'
    else: hint='点按操作'
    d.text((W//2,202),hint,font=font(13),fill='#748390',anchor='mm')
    return image


def action(control):
    return {'KEY_TYPE':'PLUGIN_ACTION','kIEn':True,'kPlugType':2,'kID':f"touchtruck.action.{control['id']}",
            'kPID':'touchtruck','kPrefix':'TouchTruck','kName':control['label'],'kData':[],'kVals':[],
            'kHHF':'true' if control.get('hold') else 'false','kInline':'true','kStatic':'false','kpip':'',
            'kFormat':control['label'],'kDesc':control['label'],'kmald':'','kmold':'','kCTS':'',
            'kET':0,'kcD':signed('#202830'),'kcL':signed('#63D8AD')}


def build():
    dist=ROOT/'dist'; dist.mkdir(exist_ok=True)
    controls=json.loads((ROOT/'config/controls.json').read_text(encoding='utf-8'))
    archive=None
    old={'kATO':'','BG':signed(BG),'MAX':True,'BGI':'','kGB':False,'GUid':-1,'kATY':0,
         'kFM':3,'kBN':False,'VERSION':2,'kENA':0,'GUdata':'','PO':1}
    template={'FF':'Default','A':[],'BD':1,'BE':signed('#202830'),'BG':signed('#202830'),
              'E':[],'GUid':-1,'ITS':True,'BiR':True,'BiT':True,'COLS':1,'TA':5,
              'TC':-1,'inS':'','IiS':True,'T':'','TP':2,'GUdata':'','inB':False,
              'TS':-1,'inC':0,'ROWS':1}
    def button(name):
        b=copy.deepcopy(template)
        b.update(id='touchtruck.button.'+name,T='',A=[],E=[],C=[],ROWS=1,COLS=1,
                 BG=signed('#202830'),BE=signed('#202830'),TC=signed('#D9E2EA'),TS=26,
                 TA=5,ITS=True,BiT=True,IiS=True)
        b.pop('HA',None)
        return b
    page={k:v for k,v in old.items() if k!='BUTTONS'}
    page.update(KEY_TITLE='TouchTruck',KEY_ID='1794609000001',KEY_COLUMNS=8,KEY_ROWS=5,
                BG=signed(BG),BTN_MARGIN=4.0,MAX=True,PO=1)
    grid=[[{} for _ in range(15)] for _ in range(15)]
    files={}
    preview=Image.new('RGB',(W*8,H*5),BG)
    preview_on=preview.copy()
    plugin_states=[]
    plugin_events=[]
    for name in FLAGS:
        plugin_states.append({'id':'touchtruck.'+name,'type':'choice','desc':name,'default':'Off','valueChoices':['On','Off']})
        plugin_events.append({'id':'touchtruck.event.'+name,'name':name+' change','format':name+' is $val',
                              'type':'communicate','valueType':'choice','valueChoices':['On','Off'],
                              'valueStateId':'touchtruck.'+name})
    headers=[('speed','车速','km/h',0,2),('fuel','剩余燃油','L',2,2),('range','预计续航','km',4,2),
             ('cruise_speed','巡航设定','km/h',6,1),('connection','TOUCHTRUCK','',7,1)]
    for key,label,unit,col,span in headers:
        default='未连接' if key=='connection' else '—'
        plugin_states.append({'id':'touchtruck.'+key,'type':'text','desc':label,'default':default})
        im=Image.new('RGB',(W*span,H),BG); d=ImageDraw.Draw(im)
        d.rounded_rectangle((3,3,W*span-4,H-4),radius=17,fill='#182128',outline='#35414B',width=2)
        d.text((W*span//2,39),label,font=font(21),fill='#9EACB8',anchor='mm')
        d.text((W*span//2,184),unit if unit else '独立遥测 / 车辆控制',font=font(14),fill='#71818F',anchor='mm')
        fname='touchtruck_header_'+key+'.png'
        buf=io.BytesIO(); im.save(buf,format='PNG'); files['icons/'+fname]=buf.getvalue()
        b=button('header_'+key); b.update(I=fname,T=default,COLS=span,TS=36,TC=signed('#A6E9D4'))
        b['E']=[{'KEY_TYPE':'AUTO_UPDATE_EVENT','kIEn':True,'kTxt':'${value:touchtruck.'+key+'}'}]
        grid[0][col]=b
        for target,live in ((preview,False),(preview_on,True)):
            part=im.copy(); d=ImageDraw.Draw(part)
            sample={'speed':'72','fuel':'325','range':'980','cruise_speed':'80','connection':'已连接'}
            d.text((W*span//2,110),sample[key] if live else default,font=font(44 if span>1 else 32),fill='#A6E9D4',anchor='mm')
            target.paste(part,(W*col,0))
    plugin_actions=[]
    for c in controls:
        b=button(c['id']); fname='touchtruck_'+c['id']+'_off.png'; b['I']=fname
        off=tile(c,archive)
        for on in (False,True):
            im=tile(c,archive,on)
            buf=io.BytesIO();im.save(buf,format='PNG')
            files['icons/touchtruck_'+c['id']+('_on.png' if on else '_off.png')]=buf.getvalue()
        if c.get('keys'):
            plugin_actions.append({'id':'touchtruck.action.'+c['id'],'name':c['label'],'prefix':'TouchTruck',
                                   'type':'communicate','format':c['label'],'data':[],
                                   'hasHoldFunctionality':bool(c.get('hold'))})
            if c.get('hold'): b['HA']=action(c)
            else: b['A']=[action(c)]
        if c.get('state'):
            for val,suffix in (('On','on'),('Off','off')):
                sid='touchtruck.'+c['state']; eid='touchtruck.event.'+c['state']
                b['E'] += [dict(KEY_TYPE='PLUGIN_EVENT',kIEn=True,kVSI=sid,kPID=eid,kID=eid,kVal=val,
                                kVT='choice',kChoices=['On','Off'],kName=c['label']+'状态',kFormat=c['label']+' $val',kCO='none'),
                           dict(KEY_TYPE='CHANGE_BUTTON_VISUALS_ACTION',kIEn=True,KEY_IS_CHANGE_ICON=True,
                                KEY_FILENAME='touchtruck_'+c['id']+'_'+suffix+'.png',KEY_IS_CHANGE_TITLE=False,
                                KEY_IS_CHANGE_BG_COLOR=False,KEY_IS_CHANGE_TEXT_COLOR=False,KEY_IS_CHANGE_IS_FULL_ICON=False)]
        grid[c['row']][c['col']]=b
        preview.paste(off,(W*c['col'],H*c['row']))
        preview_on.paste(tile(c,archive,bool(c.get('state'))),(W*c['col'],H*c['row']))
    page['BUTTONS']=grid
    plugin={'sdk':4,'version':1,'name':'TouchTruck','id':'touchtruck',
            'configuration':{'colorDark':'#202830','colorLight':'#63D8AD'},
            'plugin_start_cmd':'"%TP_PLUGIN_FOLDER%/TouchTruck/runtime/pythonw.exe" "%TP_PLUGIN_FOLDER%/TouchTruck/app/run_bridge.py"',
            'categories':[{'id':'touchtruck.controls','name':'TouchTruck','actions':plugin_actions,
                           'states':plugin_states,'events':plugin_events}]}
    (ROOT/'plugin').mkdir(exist_ok=True)
    (ROOT/'plugin/entry.tp').write_text(json.dumps(plugin,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(dist/'TouchTruck.tpz','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('pages/TouchTruck.tml',json.dumps(page,ensure_ascii=False))
        for n,data in files.items(): z.writestr(n,data)
    with zipfile.ZipFile(dist/'TouchTruck.tpp','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('TouchTruck/entry.tp',json.dumps(plugin,ensure_ascii=False,indent=2))
        # Runtime deliberately stays in the user-selected workspace, not AppData.
    preview.resize((1600,1120),Image.Resampling.LANCZOS).save(dist/'preview.png')
    preview_on.resize((1600,1120),Image.Resampling.LANCZOS).save(dist/'preview-demo.png')
    manifest={'release':'V.1.12.1','revision':12,'mapping':'Local\\SCSTelemetry','size':32768,
              'source':'https://github.com/RenCloud/scs-sdk-plugin/releases/tag/V.1.12.1',
              'dll_sha256':hashlib.sha256((ROOT/'vendor/rencloud/release_v_1_12_1/Win64/scs-telemetry.dll').read_bytes()).hexdigest(),
              'header_sha256':hashlib.sha256((ROOT/'vendor/scs-telemetry-common.hpp').read_bytes()).hexdigest()}
    (ROOT/'vendor/telemetry-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Built TouchTruck.tpz, TouchTruck.tpp, preview.png, preview-demo.png')


if __name__=='__main__': build()
