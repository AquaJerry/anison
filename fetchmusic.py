#!/bin/python3
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
        self.ready()
        os.system(f'curl {link} -o a.webm;'
                  f'ffmpeg -i a.webm -af loudnorm -b:a 64k'
                  f' -map_chapters -1 -map_metadata -1 {name}.mp3'
                  f';rm a.webm')

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


class AnimeAngel:
    def __init__(self):
        self.angel = Angel('https://staging.animethemes.moe/api/')
        self.book = StudioBook(self.angel)

    def clone_songs(self):
        # The first anime is on air in 1963
        for year in range(1963, 2022):
            for quarter in range(4):
                self.pull_songs_in(quarter=quarter, year=year)

    def pull_songs_in(self, quarter, year):
        '''pull anime songs from animethemes.moe'''
        # Use this to get animes on air in some year
        param = '&'.join([
            'fields[anime]=id',  # useless
            'fields[animetheme]=slug',  # sluglikeOP1
            'fields[animethemeentry]=id',  # useless
            'fields[studio]=id',  # For lookup abbr of companies
            'fields[video]=filename,size',
            f"filter[season]={('Winter', 'Spring', 'Summer', 'Fall')[quarter]}",
            f'filter[year]={year}',
            'include=animethemes.animethemeentries.videos,studios',
        ])
        self.when = f'{str(year)[-2:]}{1 + quarter}'
        self.rawpull(self.angel.api_head + f'anime?{param}')

    def rawpull(self, api):
        moe = self.angel.rawfetch(api)
        for anime in moe['anime']:
            studiostr = ''.join(self.book[str(s['id'])]['abbr']
                                for s in anime['studios'])
            for animetheme in anime['animethemes']:
                slug = animetheme['slug']
                slug = slug[0] + slug[2:]
                videos = animetheme['animethemeentries'][0]['videos']
                key = lambda video: video['size']
                filename = sorted(videos, key=key)[0]['filename']
                link = f'https://animethemes.moe/video/{filename}.webm'
                name = f'{self.when}{studiostr}{slug}'
                to_rename = 0
                if [*pathlib.Path().glob(f'{name}*')]:
                    to_rename = 1
                    if pathlib.Path(name).exists():
                        self.rename(name)
                self.angel.pull(link, name)
                if to_rename:
                    self.rename(name)
            pass
        if next := moe['links']['next']:
            self.rawpull(next)

    def rename(self, name):
        path = pathlib.Path(name)
        md = hashlib.md5(path.read_bytes()).hexdigest()
        for i in range(32):
            newname = f'{name}{md[:1+i]}'
            if not [*pathlib.Path().glob(f'{newname}*')]:
                path.rename(newname)
                break


if '__main__' == __name__:
    AnimeAngel().clone_songs()