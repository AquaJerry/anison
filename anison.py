#!/bin/python3
import argparse, json, os, re, time
def abbr(slug):
    '''Short names are better on wearables'''
    abbr = re.match('(production|studio|)(.{,3})', full := re.sub('\W|_', '', slug))[2]  # abbr is alnum
    if 3 > (l := len(abbr)): abbr = f'{full[:3-l]}{abbr}'  # each abbr lens 3
    return abbr.upper()   # upper is more readable
class Season:
    def __getattr__(self, name):
        match name:
            case 'season': return ('Winter', 'Spring', 'Summer', 'Fall')[self.quarter]
    def __init__(self, season=''):
        '''The first anime is on air in 1st quarter in 1963'''
        if not re.match('\d\d[1-4]', season): season = '631'
        self.quarter = int(season[2]) - 1
        self.year = (y := int(season[:2])) + (1900, 2000)[63 > y]
    def __iter__(self):
        while 1:
            yield self
            self.quarter += 1
            if 4 == self.quarter:
                self.quarter = 0
                self.year += 1
    def __repr__(self):
        return f'{str(self.year)[-2:]}{1 + self.quarter}'
class Song:
    def __init__(self, since='', skip=0):
        self.skip = skip
        self.last_curl_time = time.time()  # Obey API rate limit
        for when in Season(since):
            '''pull anime songs from animethemes.moe'''
            # Use this to get animes on air in some year
            self.when = when
            include = 'animethemes.animethemeentries.videos.audio,studios'
            self.pgdn('https://api.animethemes.moe/anime'
                '?fields[anime]=id'  # useless
                '&fields[animetheme]=sequence,type'  # like'1,OP'
                '&fields[animethemeentry]=id'  # useless
                '&fields[audio]=filename,size'
                '&fields[studio]=slug'
                '&fields[video]=id'  # useless
                f"&filter[has-and]={include}"
                f'&filter[season]={when.season}'
                f'&filter[year]={when.year}'
                f'&include={include}'
                )
    def curl(self, cb):
        '''Most websites keep a rate limit of 60 per minute'''
        if 1 > time.time() - self.last_curl_time: time.sleep(1)
        moe = cb()
        self.last_curl_time = time.time()
        return moe
    def pgdn(self, pg):
        moe = json.load(self.curl(lambda: os.popen(f"curl -g '{pg}'")))
        for a in moe['anime']:
            s = ''.join(abbr(s['slug']) for s in a['studios'])
            for t in a['animethemes']:
                name = f"{self.when}{s}{t['type'][0]}{t['sequence']or''}"
                a = [v['audio'] for e in t['animethemeentries'] for v in e['videos']]
                f = sorted(a, key=lambda a: a['size'])[0]['filename']
                # Download link as name.mp3
                # If skip, list local songs to try reduce download times
                # > name = '631MUSO'
                # > ls $name[.a-z]*
                # 631MUSO.mp3
                # 631MUSOa.mp3
                #        ^ The dot(.) and lowercase means no need to download
                if (sames := os.popen(f'ls {name}[.a-z]*').read().split()) and self.skip:
                    break
                if self.curl(lambda: os.system(f'curl https://a.animethemes.moe/{f}.ogg|ffmpeg -i - -af loudnorm -b:a 64k -map_chapters -1 -map_metadata -1 -f mp3 /tmp/{name}')):
                    break  # download incomplete
                if sames:
                    # solve name conflicts
                    sames += f'/tmp/{name}',
                    mds = [''.join(chr(55+ord(c)) if c.isdigit() else c for c in
                                os.popen(f'md5sum {s}').read()) for s in sames]
                    for i in range(2):  # conflict rate: 1/256
                        if len(sames) == len({m[:1+i] for m in mds}):
                            for j, s in enumerate(sames):
                                os.system(f'mv {s} {name}{mds[j][:1+i]}.mp3')
                            break
                else:
                    os.system(f'mv /tmp/{name} {name}.mp3')  # save
        if next := moe['links']['next']: self.pgdn(next)
if '__main__' == __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', action='store_true')
    parser.add_argument('since', default='', nargs='?')
    arg = parser.parse_args()
    Song(arg.since, arg.n)