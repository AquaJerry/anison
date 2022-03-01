#!/bin/python3
from pathlib import Path
import json
import os
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
        return json.loads(os.popen(f"curl -g '{api}'").read())

    def fetch(self, api_body):
        '''Help you write less to fetch things from animethemes.moe'''
        return self.rawfetch(self.api_head + api_body)

    def pull(self, link, name):
        '''Download link as name.mp3'''
        self.ready()
        os.system(f'ffmpeg -i {link} -af loudnorm -b:a 64k'
                  f' -map_chapters -1 -map_metadata -1 {name}.mp3')

    def ready(self):
        '''Most websites keep a rate limit of 60 per minute'''
        if 1 > time.time() - self.last_fetch_time:
            time.sleep(1)
        self.last_fetch_time = time.time()


class DAngel(Angel):
    '''Fetcher: what is fetch has a 'data' field'''

    def fetch(self, api):
        return super().fetch(api)['data']


class StudioBook(dict):
    '''Look up its instance to get info about a company
    '''

    def __init__(self, angel):
        '''Get a dict of companies who make animes
        '''
        self.angel = angel
        book = Path('studio_book.json')
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


class StudioAngel:
    angel = Angel('https://staging.animethemes.moe/api/')
    book = StudioBook(angel)


def test_animethemes():
    '''animethemes.moe stream is disabled, so audios will be pull elsewhere'''
    year = 1963   # when first anime is on air
    # Use this to get animes on air in some year
    year_show_param = '?' + '&'.join([
        'fields[anime]=name',  # See TODO_1
        'fields[animetheme]=slug',  # sluglikeOP1
        'fields[song]=title',  # See TODO_1
        'fields[studio]=id',  # For lookup abbr of companies
        'include=animethemes.song,studios',  # See TODO_1
    ])
    animeyear_api_body = f'animeyear/{year}{year_show_param}'
    moe = StudioAngel.angel.fetch(animeyear_api_body)
    for season, animes in moe.items():
        quarter = {'winter': 1, 'spring': 2, 'summer': 3, 'fall': 4}[season]
        for anime in animes:
            for animetheme in anime['animethemes']:
                studios = [StudioAngel.book[str(s['id'])]['abbr']
                           for s in anime['studios']]
                slug = animetheme['slug']
                # TODO TODO_1: pull audio from other sites


class SongAngel:
    '''Yes, I can download anime songs'''

    def __init__(self):
        self.angle = DAngel('https://api.aniapi.com/v1/')

    def pull_songs(self, year, page=1):

        # Step 1: fetch all songs
        api_body = f'song?year={year}'
        if 1 - page:
            api_body += '&page={page}'
        print(api_body)  # FIXME
        songbook = self.angle.fetch(api_body)

        # Step 2: get song list
        try:
            songs = songbook['documents']
        except:  # no songs this year
            return

        # Step 3: download each song
        for song in songs:

            # Step 3-1: get download link
            try:
                link = song['preview_url']
            except:  # some songs have no preview
                continue

            # Step 3-2: OP? ED?
            if song['type'] not in (0, 1):   # if the song is neither OP or ED
                continue
            # FIXME: this sluglikeOP1 do not like OP1 but OP#999
            sluglikeOP1 = ('OP', 'ED')[song['type']] + '#' + str(song['id'])

            # Step 3-3: season
            # {WINTER: 0, SPRING: 1, SUMMER: 2, FALL: 3}
            quar = f"Q{1 + s}" if (s := song['season']) in (0, 1, 2, 3) else ''

            # Step 3-4: studios
            studios = song['anime_id']  # TODO: replace anime_id with studios

            # Step 3-5: name of file to download?
            name = f"{year}{quar},{studios},{sluglikeOP1}"
            # sluglikeOP1 like OP but not OP1, so
            samename_paths = [*Path().glob(f'{name}*')]
            if num_samename := len(samename_paths):  # FIXME
                # product code:
                #name += 1 + num_samename
                # if 1 == num_samename:
                #    muji_path = samename_paths[0]
                #    muji_path.rename(muji_path.stem + '1' + muji_path.suffix)
                continue

            # Step 3-6: download
            self.angle.pull(link, name)

        # Step 4: turn to next page if any
        if page - songbook['last_page']:
            self.pull_songs(year, 1 + page)


if '__main__' == __name__:
    song_angle = SongAngel()
    for year in range(1963, 2022):
        song_angle.pull_songs(year)
