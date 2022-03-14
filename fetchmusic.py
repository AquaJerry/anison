#!/bin/python3
import datetime
import hashlib
import json
import os
import pathlib
import re
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
        tmp_out_path = f'{name}z{suffix}'
        self.ready()
        os.system(f'curl -k {link} -o a.webm;'
                  f'ffmpeg -i a.webm -af loudnorm -b:a 64k'
                  f' -map_chapters -1 -map_metadata -1 -y {tmp_out_path};'
                  f'rm a.webm;')
        if 1 < (slen := len(sames := [*pathlib.Path().glob(f'{name}*')])):
            # solve name conflicts
            mds = [hashlib.md5(s.read_bytes()).hexdigest() for s in sames]
            for i in range(2):  # conflict rate: 1/256
                if len({m[:1+i] for m in mds}) == slen:
                    for i, s in enumerate(sames):
                        s.rename(f'{name}{mds[i]}{suffix}')
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

    def __init__(self, year = 1963, quarter = 0):
        '''The first anime is on air in 1963'''
        self.quarter = quarter
        self.season = AnimeSeason.Season[quarter]
        self.year = year
    
    def __iter__(self):
        return self

    def __repr__(self):
        return f'{str(self.year)[-2:]}{1 + self.quarter}'
    
    def __next__(self):
        self.quarter += 1
        if len(AnimeSeason.Season) == self.quarter:
            self.quarter = 0
            self.year += 1
            if datetime.date.today().year < self.year:
                raise StopIteration
        return self


class AnimeAngel:
    def __init__(self):
        self.angel = Angel('https://staging.animethemes.moe/api/')
        self.book = StudioBook(self.angel)

    def clone_songs(self, since = AnimeSeason()):
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
    AnimeAngel().clone_songs()
