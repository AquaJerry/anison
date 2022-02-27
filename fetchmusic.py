#!/bin/python3
import json
import os
import time


# Cache info about anime companies
studios_filename = 'studios.json'

# From which get anime songs
api_moe = 'https://staging.animethemes.moe/api/'

# Use this to get list of anime companies
studio_moe = api_moe + 'studio?fields[studio]=id,name,slug'


year_show_param = '?' + '&'.join([
    'fields[anime]=id',
    'include=' + ','.join([
        'animethemes.animethemeentries.videos',
        'studios',
    ]),
])


def fetch_fullmoe(fullmoe):
    '''Help you write less to fetch things from animethemes.moe.'''
    return json.loads(os.popen(f"curl '{fullmoe}'").read())


def fetch_moe(moe):
    '''Help you write less to fetch things from animethemes.moe.'''
    return fetch_fullmoe(api_moe + moe)


def get_studios_per_page(moe, old_studios):
    '''Fetch info about anime companies once a page.
    This will fetch all companies online.
    '''
    studio_index = fetch_fullmoe(moe)
    print(f"Studio page {studio_index['meta']['current_page']} fetch")
    new_studios = studio_index['studios']
    studios = [*old_studios, *new_studios]
    if next := studio_index['links']['next']:
        time.sleep(1)  # Obey API rate limit
        studios = get_studios_per_page(next, studios)
    return studios


def get_all_studios():
    '''Tell me companies who make animes
    '''
    try:
        with open(studios_filename) as f:
            studios = json.load(f)
    except:
        studios = get_studios_per_page(studio_moe, [])
        with open(studios_filename, 'w') as f:
            # Save disk usage by sep
            json.dump(studios, f, separators=(',', ':'))
    return studios


if '__main__' == __name__:
    # Test script here
    get_all_studios()
    #moe = fetch_moe(f'animeyear/{year}{year_show_param}')
    # print(moe)
