#!/bin/python3
import json
import os
import re
import time


class Angel:
    '''Fetcher
    '''

    def __init__(self, api_head):
        self.api_head = api_head
        self.last_fetch_time = time.time()  # Obey API rate limit

    def fetch_by_api(self, api):
        '''Help you write less to fetch things from animethemes.moe.'''
        self.ready()
        return json.loads(os.popen(f"curl -g '{api}'").read())

    def fetch_by_api_body(self, api_body):
        '''Help you write less to fetch things from animethemes.moe.'''
        return self.fetch_by_api(self.api_head + api_body)

    def pull(self, link, name):
        self.ready()
        os.system(f'ffmpeg -i {link} -af loudnorm -b:a 64k'
                  f' -map_chapters -1 -map_metadata -1 {name}.mp3')

    def ready(self):
        if 1 > time.time() - self.last_fetch_time:
            time.sleep(1)
        self.last_fetch_time = time.time()


class DAngel(Angel):
    def fetch_by_api(self, api):
        return super().fetch_by_api(api)['data']


class StudioBook(dict):
    '''Look up its instance to get info about a company
    '''

    def __init__(self, angel):
        '''Get a dict of companies who make animes
        '''
        self.angel = angel
        fname = 'studio_book.json'
        try:
            with open(fname) as f:
                for k, v in json.load(f).items():
                    self[k] = v
        except:
            with open(fname, 'w') as f:
                # Save disk usage by sep
                api = angel.api_head + 'studio?fields[studio]=id,slug'
                json.dump(self.fetch(api).abbreviate(), f)

    def abbreviate(self):
        '''Short names are better on wearables
        '''
        pres = 'animation', 'production', 'project', 'studio', 'team', 'tokyo'
        for studio in self.values():
            full = studio['slug'].replace('_', '')
            abbr = full[:3]
            if full.startswith(pres):
                pattern = f'({"|".join(pres)})' r'(?P<abbr>\w{,3})'
                abbr = re.compile(pattern).match(full).group('abbr')
            studio['abbr'] = abbr.upper()
        return self

    def fetch(self, api):
        '''Fetch info about anime companies page by page.
        This will fetch all companies online.
        '''
        page = self.angel.fetch_by_api(api)
        for studio in page['studios']:
            self[studio['id']] = {'slug': studio['slug']}
        if next := page['links']['next']:
            self.fetch(next)
        return self


class StudioAngel:
    angel = Angel('https://staging.animethemes.moe/api/')
    book = StudioBook(angel)


def test_animethemes():
    # Test script here
    # From which get anime songs
    year = 1963
    # Use this to get animes on air in some year
    year_show_param = '?' + '&'.join([
        'fields[anime]=name',  # See TODO_1
        'fields[animetheme]=slug',  # sluglikeOP1
        'fields[song]=title',  # See TODO_1
        'fields[studio]=id',  # For lookup abbr of companies
        'include=animethemes.song,studios',  # See TODO_1
    ])
    animeyear_api_body = f'animeyear/{year}{year_show_param}'
    moe = StudioAngel.angel.fetch_by_api_body(animeyear_api_body)
    for season, animes in moe.items():
        quarter = {'winter': 1, 'spring': 2, 'summer': 3, 'fall': 4}[season]
        for anime in animes:
            for animetheme in anime['animethemes']:
                studios = [StudioAngel.book[str(s['id'])]['abbr']
                           for s in anime['studios']]
                slug = animetheme['slug']
                # TODO TODO_1: pull audio from other sites


if '__main__' == __name__:
    # TODO: studio
    a_angle = DAngel('https://api.aniapi.com/v1/')
    year = 1968
    allsongs = a_angle.fetch_by_api_body(f'song?year={year}')
    # Get songs which type is OP(0) or ED(1) and season is known
    songs = [s for s in allsongs['documents']
             if s['type'] in (0, 1) and s['season'] in (0, 1, 2, 3)]
    for song in songs:
        # Season {WINTER: 0, SPRING: 1, SUMMER: 2, FALL: 3} to quarter
        quarter = f"Q{1 + song['season']}"
        sluglikeOP1 = ('OP', 'ED')[song['type']]
        name = f"{year}{quarter},{song['anime_id']},{sluglikeOP1}"
        a_angle.pull(song['preview_url'], name)
    pass
