#!/bin/python3
import datetime
import hashlib
import json
import os
import pathlib
import re
import sys
import time


class Angel:
    '''Fetcher'''

    def __init__(self, api_head):
        self.api_head = api_head
        self.last_fetch_time = time.time()  # Obey API rate limit

    def rawfetch(self, api):
        '''Help you write less to fetch things from animethemes.moe'''
        self.ready()
        try:
            return json.loads(os.popen(f"curl -g '{api}'").read())
        except:
            return self.rawfetch(api)

    def fetch(self, api_body):
        '''Help you write less to fetch things from animethemes.moe'''
        return self.rawfetch(self.api_head + api_body)

    def pull(self, link, name):
        '''Download link as name.mp3'''
        suffix = '.mp3'
        tmp_in_path = 'a.webm'
        tmp_out_path = f'{name}z{suffix}'
        self.ready()
        incomplete = os.system(
            f'curl {link} -o {tmp_in_path} &&'
            f'ffmpeg -i {tmp_in_path} -af loudnorm -b:a 64k'
            f' -map_chapters -1 -map_metadata -1 {tmp_out_path}'
        )
        os.system(f'rm {tmp_in_path}')
        if incomplete:
            os.system(f'rm {tmp_out_path}')
            return
        if 1 < (slen := len(sames := [*pathlib.Path().glob(f'{name}*')])):
            # solve name conflicts
            mds = [hashlib.md5(s.read_bytes()).hexdigest() for s in sames]
            for i in range(2):  # conflict rate: 1/256
                if len({m[:1+i] for m in mds}) == slen:
                    for j, s in enumerate(sames):
                        s.rename(f'{name}{mds[j][:1+i]}{suffix}')
                    break
            else:
                pathlib.Path(tmp_out_path).unlink()  # remove
        else:
            pathlib.Path(tmp_out_path).rename(f'{name}{suffix}')  # save

    def ready(self):
        '''Most websites keep a rate limit of 60 per minute'''
        if 1 > time.time() - self.last_fetch_time:
            time.sleep(1)
        self.last_fetch_time = time.time()


class StudioBook(dict):
    '''Look up its instance to get info about a company
    '''

    def __init__(self, angel):
        '''Get a dict of companies who make animes
        '''
        self.angel = angel
        book = pathlib.Path('studio_book.json')
        if book.exists():
            with book.open() as f:
                for k, v in json.load(f).items():
                    self[k] = v
        else:
            newbook = self.fetch('studio?fields[studio]=id,slug').abbr()
            with book.open('w') as f:
                json.dump(newbook, f)

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

    def rawfetch(self, api):
        '''Fetch info about anime companies page by page.
        This will fetch all companies online.
        '''
        page = self.angel.rawfetch(api)
        for studio in page['studios']:
            self[studio['id']] = {'slug': studio['slug']}
        if next := page['links']['next']:
            self.rawfetch(next)
        return self

    def fetch(self, api_body):
        return self.rawfetch(self.angel.api_head + api_body)


class AnimeSeason:
    Season = 'Winter', 'Spring', 'Summer', 'Fall'

    def __getattr__(self, name):
        if 'season' == name:
            return self.Season[self.quarter]

    def __init__(self, season = 0):
        '''The first anime is on air in 1st quarter in 1963'''
        if not re.compile(r'\d\d[1-4]').match(season or ''):
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
                if datetime.date.today().year < self.year:
                    break

    def __repr__(self):
        return f'{str(self.year)[-2:]}{1 + self.quarter}'


class AnimeAngel:
    def __init__(self):
        self.angel = Angel('https://staging.animethemes.moe/api/')
        self.book = StudioBook(self.angel)

    def clone_songs(self, since=0):
        if type(since) is not AnimeSeason:
            since = AnimeSeason(since)
        for season in since:
            self.pull_songs_in(season)

    def pull(self, endpoint, config={}):
        params = []
        for k, v in config.items():
            if type(v) is str:
                params += [f'{k}={v}']
            else:
                params += [f'{k}[{s}]={w}' for s, w in v.items()]
        self.rawpull(f'{self.angel.api_head}{endpoint}'
                     f"{'?' if params else ''}{'&'.join(params)}")

    def pull_songs_in(self, when):
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
            'filter': {
                'has': 'studios',
                'season': when.season,
                'year': when.year,
            },
            'include': 'animethemes.animethemeentries.videos,studios',
        })

    def rawpull(self, api):
        moe = self.angel.rawfetch(api)
        for anime in moe['anime']:
            studiostr = ''.join(self.book[str(s['id'])]['abbr']
                                for s in anime['studios'])
            for animetheme in anime['animethemes']:
                slug = animetheme['slug']
                slug = slug[0] + slug[2:]
                videos = animetheme['animethemeentries'][0]['videos']
                def key(video): return video['size']
                filename = sorted(videos, key=key)[0]['filename']
                link = f'https://animethemes.moe/video/{filename}.webm'
                name = f'{self.when}{studiostr}{slug}'
                self.angel.pull(link, name)
        if next := moe['links']['next']:
            self.rawpull(next)


if '__main__' == __name__:
    AnimeAngel().clone_songs(sys.argv[1] if 1 - len(sys.argv) else 0)
