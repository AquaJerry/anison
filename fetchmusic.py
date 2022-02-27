#!/usr/bin/python3
import json
import os


# Cache anime years
years_filename = 'years.json'

# From which get anime songs
api_moe = 'https://staging.animethemes.moe/api/'

# Help you write less to fetch things from animethemes.moe.
fetch_moe = lambda moe: json.loads(os.popen(f'curl {api_moe}{moe}').read())


def get_all_years():
    '''Tell me which years animes are on air.
    '''
    try:
        with open(years_filename) as f: years = json.load(f)
    except:
        years = fetch_moe('animeyear')
        with open(years_filename, 'w') as f:
            json.dump(years, f, separators=(',',':'))  # Save disk usage by sep
    return years


if '__main__' == __name__:
    # Test script here
    years = get_all_years()
    print(years[0])