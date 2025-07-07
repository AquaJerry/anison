#!/bin/python3
import argparse, json, os, re
def abbr(s):
    '''e.g. mushi_production -> MUS, studio_ghibli -> GHI, production_ig -> PIG'''
    abbr = re.match('(production|studio|)(.{,3})', full := re.sub('\W|_', '', s))[2]  # abbr is alnum
    if 3 > (l := len(abbr)): abbr = f'{full[:3-l]}{abbr}'  # each abbr lens 3
    return abbr.upper()   # upper is more readable, lower solves name confilict
# Cmd to cache theme as /tmp/$name(mp3)
mp3 = lambda name, theme: ('sleep 1;curl https://a.animethemes.moe/'  # sleep to obey a rate limit of 60 per minute
        f"{sorted([v['audio']for e in theme['animethemeentries']for v in e['videos']],key=lambda a:a['size'])[0]['filename']}"
        f'.ogg|ffmpeg -i - -af loudnorm -b:a 64k -map_chapters -1 -map_metadata -1 -f mp3 /tmp/{name}')
# > ls 631MUSO[.a-z]*
# 631MUSO.mp3
# 631MUSOa.mp3
#        ^ The dot(.) and lowercase means name confilict, but digit or upper is part of name
same = lambda name: os.popen(f'ls {name}[.a-z]*').read().split()
p = argparse.ArgumentParser()
p.add_argument('since', default='631', nargs='?')  # what season to begin
a = p.parse_args()
season_arg, year = int(a.since[2]) - 1, (y := int(a.since[:2])) + (1899, 1999)[63 > y]  # season 0: winter, 1: spring, 2: summer, 3: fall
newest_date = os.popen('date').read()  # see: if themes updated remote
while moe := json.load(os.popen("sleep 1;curl -g 'https://api.animethemes.moe/"  # sleep to obey rate limit
        f'animeyear/{str(year := 1 + year)}'
        '?fields[anime]=id'  # useless
        '&fields[animetheme]=sequence,type'  # like'1,OP'
        '&fields[animethemeentry]=id'  # useless
        '&fields[audio]=filename,size'
        '&fields[studio]=slug'  # like'studio_ghibli'
        '&fields[video]=id'  # useless
        '&include=animethemes.animethemeentries.videos.audio,studios'
        "'")):  # Use this to get anison on air in some year
    for season in range(season_arg, 4):
        girl = {}
        for a in moe.get(('winter', 'spring', 'summer', 'fall')[season], ()):
            s = ''.join(abbr(s['slug']) for s in a['studios'])
            for t in a['animethemes']:
                if sames := same(name := f"{str(year)[-2:]}{1+season}{s}{t['type'][0]}{t['sequence']or''}"):
                    girl.setdefault(name, []).append(t)  # do later
                else: os.system(f'{mp3(name, t)}&&mv /tmp/{name} {name}.mp3')  # save if complete
        for name, themes in girl.items():
            if len(themes) > int(os.popen(f"find ! -newerat '{newest_date}' -name {name}[.a-z]*|wc -l").read()):  # if themes updated remote
                for theme in themes:  # tell from mds, like'631MUSEa.mp3,631MUSEb.mp3'
                    os.system(mp3(name, theme))  # cache /tmp/$name
                    sames = *same(name), f'/tmp/{name}'  # must re-eval sames each time
                    mds = [''.join(chr(55+ord(c))if c.isdigit()else c for c in os.popen(f'md5sum {s}').read())for s in sames]
                    for i in range(2):  # conflict rate: 1/256
                        if len(sames) == len({m[:1+i] for m in mds}):  # mds='a,b'or'aa,ab'
                            for j, s in enumerate(sames): os.system(f'mv {s} {name}{mds[j][:1+i]}.mp3')
                            break
    season_arg = 0  # next year
