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
if '__main__' == __name__:
    p = argparse.ArgumentParser()
    p.add_argument('since', default='631', nargs='?')  # what season to begin
    a = p.parse_args()
    when = int(a.since[2]) - 1 + 4 * (int(a.since[:2]) + (-63, 37)[63 > int(a.since[:2])])  # what season now
    while 1:
        girl, moe = {}, {'links': {'next': 'https://api.animethemes.moe/anime'
            '?fields[anime]=id'  # useless
            '&fields[animetheme]=sequence,type'  # like'1,OP'
            '&fields[animethemeentry]=id'  # useless
            '&fields[audio]=filename,size'
            '&fields[studio]=slug'  # like'studio_ghibli'
            '&fields[video]=id'  # useless
            '&filter[has-and]=animethemes.animethemeentries.videos.audio,studios'
            f"&filter[season]={('winter', 'spring', 'summer', 'fall')[when % 4]}"
            f'&filter[year]={1963 + when // 4}'
            '&include=animethemes.animethemeentries.videos.audio,studios'
            }}  # Use this to get anison on air in some season
        while pg := moe['links']['next']:
            for a in (moe := json.load(os.popen(f"sleep 1;curl -g '{pg}'")))['anime']:  # sleep to obey rate limit
                s = ''.join(abbr(s['slug']) for s in a['studios'])
                for t in a['animethemes']:
                    if sames := same(name := f"{str(1963+when//4)[-2:]}{1+when%4}{s}{t['type'][0]}{t['sequence']or''}"):
                        girl.setdefault(name, [len(sames)]).append(t)  # do later
                    else: os.system(f'{mp3(name, t)}&&mv /tmp/{name} {name}.mp3')  # save if complete
        for name, (len_sames, *themes) in girl.items():
            if len_sames < len(themes):  # if named themes updated remote
                for theme in themes:  # tell from mds, like'631MUSEa.mp3,631MUSEb.mp3'
                    os.system(mp3(name, theme))  # cache /tmp/$name
                    sames = *same(name), f'/tmp/{name}'  # must re-eval sames each time
                    mds = [''.join(chr(55+ord(c))if c.isdigit()else c for c in os.popen(f'md5sum {s}').read())for s in sames]
                    for i in range(2):  # conflict rate: 1/256
                        if len(sames) == len({m[:1+i] for m in mds}):  # mds='a,b'or'aa,ab'
                            for j, s in enumerate(sames): os.system(f'mv {s} {name}{mds[j][:1+i]}.mp3')
                            break
        when += 1  # next season
