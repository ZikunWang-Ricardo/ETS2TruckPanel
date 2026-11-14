"""Original geometric instrument artwork. Licensed with this project's GPL-3.0."""


def draw_instrument(d, kind, color, font):
    w=5
    def line(points,width=w):d.line(points,fill=color,width=width)
    def box(bounds,r=7):d.rounded_rectangle(bounds,radius=r,outline=color,width=w)
    def text(value,x=160,y=87,size=25):d.text((x,y),value,font=font(size),fill=color,anchor='mm')
    def arrow(up=True,x=160,y=110):
        line((x,y+14 if up else y-14,x,y-14 if up else y+14),4)
        yy=y-14 if up else y+14
        line([(x-9,yy+(9 if up else -9)),(x,yy),(x+9,yy+(9 if up else -9))],4)
    if kind=='engine':
        line([(110,65),(125,65),(125,54),(180,54),(190,68),(210,68),(210,116),(190,116),(180,127),(122,127),(122,113),(110,113),(110,65)])
        line((146,45,171,45));line((157,45,157,54))
        d.polygon([(162,67),(143,95),(158,95),(151,116),(178,84),(163,84)],fill=color)
    elif kind in ('parking','engine_brake'):
        d.ellipse((126,50,194,124),outline=color,width=w)
        d.arc((108,42,212,132),110,250,fill=color,width=w)
        d.arc((108,42,212,132),-70,70,fill=color,width=w)
        text('P' if kind=='parking' else 'B',size=37)
    elif kind=='trailer':
        box((108,52,207,106));line((108,106,108,118,123,118))
        d.ellipse((129,109,149,130),outline=color,width=4);d.ellipse((171,109,191,130),outline=color,width=4)
        line((207,98,219,98));d.ellipse((215,93,225,103),outline=color,width=3)
    elif kind=='diff_lock':
        for y in (55,118):
            line((115,y,205,y));box((106,y-11,122,y+11),3);box((198,y-11,214,y+11),3)
        line((160,55,160,75));line((160,101,160,118));box((146,75,174,101),4)
        d.arc((151,66,169,86),180,360,fill=color,width=3)
    elif kind=='axle':
        line((110,66,210,66));line((111,70,111,96,209,96,209,70))
        for x in (128,192):d.ellipse((x-14,100,x+14,130),outline=color,width=4)
        arrow(True,160,110)
    elif kind in ('left','right'):
        points=[(111,88),(150,51),(150,71),(209,71),(209,105),(150,105),(150,125)]
        if kind=='right':points=[(320-x,y) for x,y in points]
        d.polygon(points,fill=color)
    elif kind=='hazard':
        line([(160,42),(216,130),(104,130),(160,42)])
        line([(160,62),(198,119),(122,119),(160,62)],3)
        line((160,85,160,103),4);d.ellipse((157,109,163,115),fill=color)
    elif kind in ('lights','high_beam','flash'):
        d.arc((152,48,219,127),80,280,fill=color,width=w)
        line((180,50,180,125))
        for y in (62,84,106):line((107,y+(12 if kind=='lights' else 0),144,y),4)
        if kind=='flash':d.polygon([(199,67),(187,89),(199,89),(190,113),(214,82),(201,82)],fill=color)
    elif kind=='horn':
        d.ellipse((107,76,129,102),outline=color,width=w)
        line([(129,80),(161,80),(205,54),(205,124),(161,98),(129,98)])
        line((212,69,221,61),3);line((215,88,228,88),3);line((212,108,221,116),3)
    elif kind=='wipers':
        d.arc((100,48,220,134),180,360,fill=color,width=w)
        line([(102,90),(133,130),(187,130),(218,90)],4)
        line((160,128,127,65));line((112,70,145,57),5)
    elif kind.startswith('cruise'):
        d.arc((111,47,209,140),180,360,fill=color,width=w)
        for p in ((124,71,131,79),(160,51,160,62),(195,71,188,79)):line(p,3)
        line((160,101,181,73),4);d.ellipse((155,96,165,106),fill=color)
        text('−' if kind=='cruise_down' else '+' if kind=='cruise_up' else 'SET',y=125,size=23)
    elif kind.startswith('lane'):
        line((105,132,124,43));line((215,132,196,43));box((143,76,177,126))
        if kind=='lane_mode':text('M',y=53,size=22)
    elif kind=='cabin_light':
        d.arc((137,43,183,91),180,360,fill=color,width=w)
        line((137,68,144,103,176,103,183,68));line((147,114,173,114))
        for x1,y1,x2,y2 in ((119,63,107,59),(201,63,213,59),(160,34,160,23)):line((x1,y1,x2,y2),3)
    elif kind.startswith('shade'):
        box((106,43,214,130))
        for y in (56,68,80):line((112,y,208,y),3)
        arrow(kind.endswith('up'),160,111)
    elif kind in ('lwinopen','lwinclose','rwinopen','rwinclose'):
        box((108,43,212,132));line((115,79,205,79),3)
        text('L' if kind.startswith('l') else 'R',x=127,y=61,size=19)
        arrow(kind.endswith('close'),165,106)
    elif kind=='acc_mode':
        box((132,42,188,79))
        for y in (96,111,126):line((135,y,185,y),3)
    elif kind=='cab':
        box((108,43,212,129),12);line((116,82,204,82))
        d.ellipse((137,91,183,137),outline=color,width=w);line((160,112,160,135),3)
    elif kind=='top':
        box((136,41,184,130),9);line((142,64,178,64));line((142,103,178,103),3)
        arrow(True,112,92);arrow(True,208,92)
    else:raise ValueError('Missing original icon: '+kind)
