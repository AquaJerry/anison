#!/bin/python3
from time import sleep, time
import json
import os


# Obey API rate limit
last_fetch_time = time()

# Cache info about anime companies
studio_dict_fname = 'studio_dict.json'

# From which get anime songs
api_head = 'https://staging.animethemes.moe/api/'

# Use this to get animes on air in some year
year_show_param = '?' + '&'.join([
    'fields[anime]=id',
    'include=' + ','.join([
        'animethemes.animethemeentries.videos',
        'studios',
    ]),
])


def fetch_by_api(api):
    '''Help you write less to fetch things from animethemes.moe.'''
    global last_fetch_time
    if 1 > time() - last_fetch_time:
        sleep(1)
    pipe = os.popen(f"curl '{api}'")
    last_fetch_time = time()
    return json.loads(pipe.read())


def fetch_by_api_body(api_body):
    '''Help you write less to fetch things from animethemes.moe.'''
    return fetch_by_api(api_head + api_body)


def fetch_studios(api, dict):
    '''Fetch info about anime companies page by page.
    This will fetch all companies online.
    '''
    page = fetch_by_api(api)
    dict = {**dict, **{s['id']: {'slug': s['slug']} for s in page['studios']}}
    if next := page['links']['next']:
        dict = fetch_studios(next, dict)
    return dict


def get_studio_dict():
    '''Get a dict of companies who make animes
    '''
    try:
        with open(studio_dict_fname) as f:
            dict = json.load(f)
    except:
        with open(studio_dict_fname, 'w') as f:
            # Save disk usage by sep
            api = api_head + 'studio?fields[studio]=id,slug'
            json.dump(dict := fetch_studios(api, {}), f)
    return dict


if '__main__' == __name__:
    # Test script here
    get_studio_dict()
    #moe = fetch_moe(f'animeyear/{year}{year_show_param}')
    # print(moe)
