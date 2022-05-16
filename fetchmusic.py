#!/bin/python3
import argparse
import json
import os
import re
import time


class Angel:
    '''Fetcher'''
    api_head = 'https://staging.animethemes.moe/api/'
    last_fetch_time = time.time()  # Obey API rate limit

    def fetch(api):
        '''Help you write less to fetch things from animethemes.moe'''
        Angel.ready()
        return json.loads(os.popen(f"curl -g '{api}'").read())

    def pull(link, name, skip):
        '''Download link as name.mp3'''
        # If skip, list local songs to try reduce download times
        # > name = '631MUSO'
        # > ls $name[.a-z]*
        # 631MUSO.mp3
        # 631MUSOa.mp3
        #        ^ The dot(.) and lowercase means no need to download
        if (sames := os.popen(f'ls {name}[.a-z]*').read().split()) and skip:
            return
        Angel.ready()
        if os.system(f'curl {link}|ffmpeg -i - -af loudnorm -b:a 64k'
                     f' -map_chapters -1 -map_metadata -1 -f mp3 /tmp/{name}'):
            return  # download incomplete
        if sames:
            # solve name conflicts
            sames += [f'/tmp/{name}']
            mds = [''.join(chr(55+ord(c)) if c.isdigit() else c for c in
                           os.popen(f'md5sum {s}').read()) for s in sames]
            for i in range(2):  # conflict rate: 1/256
                if len(sames) == len({m[:1+i] for m in mds}):
                    for j, s in enumerate(sames):
                        os.system(f'mv {s} {name}{mds[j][:1+i]}.mp3')
                    break
        else:
            os.system(f'mv /tmp/{name} {name}.mp3')  # save

    def ready():
        '''Most websites keep a rate limit of 60 per minute'''
        if 1 > time.time() - Angel.last_fetch_time:
            time.sleep(1)
        Angel.last_fetch_time = time.time()


class StudioBook(dict):
    '''Look up its instance to get info about a company'''

    def __init__(self):
        '''Get a dict of companies who make animes
        '''
        if os.system('[ -s studio_book.json ]'):  # if the book does not exist
            api = 'studio?fields[studio]=id,slug'
            with open('studio_book.json', 'w') as f:
                json.dump(self.pull(Angel.api_head + api).abbr(), f)
        else:
            with open('studio_book.json') as f:
                for k, v in json.load(f).items():
                    self[k] = v

    def abbr(self):
        '''Short names are better on wearables
        '''
        pres = 'animation', 'production', 'project', 'studio', 'team', 'tokyo'
        for studio in self.values():
            full = studio['slug'].replace('_', '')  # abbr is alnum
            abbr = full[:3]
            if full.startswith(pres):
                pattern = f'({"|".join(pres)})' r'(?P<abbr>\w{,3})'
                abbr = re.compile(pattern).match(full).group('abbr')
            if 3 > (l := len(abbr)):
                abbr = f'{full[:3-l]}{abbr}'  # each abbr lens 3
            studio['abbr'] = abbr.upper()   # upper is more readable
        return self

    def pull(self, api):
        '''Fetch info about anime companies page by page.
        This will fetch all companies online.
        '''
        page = Angel.fetch(api)
        for studio in page['studios']:
            self[str(studio['id'])] = {'slug': studio['slug']}
        if next := page['links']['next']:
            self.pull(next)
        return self


class AnimeSeason:
    Season = 'Winter', 'Spring', 'Summer', 'Fall'

    def __getattr__(self, name):
        if 'season' == name:
            return self.Season[self.quarter]

    def __init__(self, season=''):
        '''The first anime is on air in 1st quarter in 1963'''
        if not re.compile(r'\d\d[1-4]').match(season):
            season = '631'
        self.quarter = int(season[2]) - 1
        self.year = (y := int(season[:2])) + (1900, 2000)[63 > y]

    def __iter__(self):
        while 1:
            yield self
            self.quarter += 1
            if len(self.Season) == self.quarter:
                self.quarter = 0
                self.year += 1

    def __repr__(self):
        return f'{str(self.year)[-2:]}{1 + self.quarter}'


class AnimeAngel:
    book = StudioBook()

    def clone_songs(self, since='', skip=0):
        self.skip = skip
        for when in AnimeSeason(since):
            '''pull anime songs from animethemes.moe'''
            # Use this to get animes on air in some year
            self.when = when
            self.pull('anime', {
                'fields': {
                    'anime': 'id',  # useless
                    'animetheme': 'slug',  # sluglikeOP1
                    'animethemeentry': 'id',  # useless
                    'studio': 'id',  # for looking up abbrs of company
                    'video': 'filename,size',
                },
                'include': (i := 'animethemes.animethemeentries.videos,studios'),
                'filter': {
                    'has-and': i,
                    'season': when.season,
                    'year': when.year,
                },
            })

    def pull(self, endpoint, config={}):
        params = []
        for k, v in config.items():
            if type(v) is str:
                params += [f'{k}={v}']
            else:
                params += [f'{k}[{s}]={w}' for s, w in v.items()]
        self.rawpull(f'{Angel.api_head}{endpoint}'
                     f"{'?' if params else ''}{'&'.join(params)}")

    def rawpull(self, api):
        moe = Angel.fetch(api)
        for a in moe['anime']:
            s = ''.join(self.book[str(s['id'])]['abbr'] for s in a['studios'])
            for t in a['animethemes']:
                e = ''.join(re.compile('(.).(\d*)').match(t['slug']).groups())
                v = t['animethemeentries'][0]['videos']
                f = sorted(v, key=lambda v: v['size'])[0]['filename']
                link = f'https://animethemes.moe/video/{f}.webm'
                Angel.pull(link, f'{self.when}{s}{e}', self.skip)
        if next := moe['links']['next']:
            self.rawpull(next)


if '__main__' == __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', action='store_true')
    parser.add_argument('since', default='', nargs='?')
    arg = parser.parse_args()
    AnimeAngel().clone_songs(arg.since, arg.n)
