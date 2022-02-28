#!/bin/python3
import json
import os
import re
import time


class Angel:
    '''Fetcher
    '''
    # From which get anime songs
    api_head = 'https://staging.animethemes.moe/api/'

    # Obey API rate limit
    last_fetch_time = time.time()

    def fetch_by_api(api):
        '''Help you write less to fetch things from animethemes.moe.'''
        if 1 > time.time() - Angel.last_fetch_time:
            time.sleep(1)
        pipe = os.popen(f"curl '{api}'")
        Angel.last_fetch_time = time.time()
        return json.loads(pipe.read())

    def fetch_by_api_body(api_body):
        '''Help you write less to fetch things from animethemes.moe.'''
        return Angel.fetch_by_api(Angel.api_head + api_body)


class StudioBook(dict):
    '''Look up its instance to get info about a company
    '''
    def __init__(self):
        '''Get a dict of companies who make animes
        '''
        fname = 'studio_book.json'
        try:
            with open(fname) as f:
                for k, v in json.load(f).items():
                    self[k] = v
        except:
            with open(fname, 'w') as f:
                # Save disk usage by sep
                api = Angel.api_head + 'studio?fields[studio]=id,slug'
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
        page = Angel.fetch_by_api(api)
        for studio in page['studios']:
            self[studio['id']] = {'slug': studio['slug']}
        if next := page['links']['next']:
            self.fetch(next)
        return self


if '__main__' == __name__:
    # Test script here
    StudioBook()
    #moe = Angel.fetch_by_api_body(f'animeyear/{year}{year_show_param}')
    #print(moe)
    # Use this to get animes on air in some year
    #year_show_param = '?' + '&'.join([
    #    'fields[anime]=id',
    #    'include=' + ','.join([
    #        'animethemes.animethemeentries.videos',
    #        'studios',
    #    ]),
    #])
