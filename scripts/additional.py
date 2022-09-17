"""
Get additional data from WoWs-Numbers
"""
import re
import requests
import json
import time
import sys


def get_ship_battles_raw():
    """
    Downloads the ship battles from WoWs-Numbers
    """

    # we need to get all regions to get the total number of battles
    regions = ['ru.', 'na.', 'asia.', '']
    battles_dict = {}
    for region in regions:
        url = 'https://{}wows-numbers.com/ships/'.format(region)
        print(url)
        r = requests.get(url).text
        # parse html with regex
        regex_str = 'dataProvider.ships = (.*);'
        regex = re.compile(regex_str)
        ship_battles_raw = regex.findall(r)[0]

        # read as json string
        raw = json.loads(ship_battles_raw)
        final_dict = {}
        # adjust the format
        for ship in raw:
            if len(ship) == 0:
                continue

            ship_info = {}
            ship_id = ship['ship_id']
            battles = ship['battles']
            if ship_id in battles_dict:
                battles_dict[ship_id] += battles
            else:
                battles_dict[ship_id] = battles
        time.sleep(0.5)

    with open('ship_battles_raw.json', 'w') as f:
        # write as json string
        f.write(json.dumps(battles_dict))


def get_personal_rating():
    """
    Downloads the personal rating from WoWs-Numbers
    """
    url = 'https://wows-numbers.com/personal/rating/expected/json/'
    r = requests.get(url).text

    with open('personal_rating_raw.json', 'w') as f:
        f.write(r)


def make_additional():
    """
    Merges all the data into one file
    """
    with open('ship_battles_raw.json', 'r') as f:
        ship_battles_raw = json.load(f)
    with open('personal_rating_raw.json', 'r') as f:
        personal_rating_raw = json.load(f)

    ship_data = personal_rating_raw['data']
    additional_dict = {}
    for ship in ship_data:
        ship_info = ship_data[ship]
        if len(ship_info) == 0:
            print('No data for ship {}'.format(ship))
            continue

        damage = ship_info['average_damage_dealt']
        frags = ship_info['average_frags']
        winrate = ship_info['win_rate']

        formatted = {}
        formatted['damage'] = round(damage)
        formatted['frags'] = round(frags, ndigits=2)
        formatted['winrate'] = round(winrate, ndigits=2)
        if ship in ship_battles_raw:
            formatted['battles'] = int(ship_battles_raw[ship])
        additional_dict[ship] = formatted

    with open('additional.json', 'w') as f:
        f.write(json.dumps(additional_dict))


def merge_additional():
    """
    Merges additional into wowsinfo.json
    """
    with open('additional.json', 'r') as f:
        additional_dict = json.load(f)
    with open('wowsinfo.json', 'r', encoding='utf8') as f:
        wowsinfo_dict = json.load(f)

    wowsinfo_dict['number'] = additional_dict
    with open('wowsinfo.json', 'w', encoding='utf8') as f:
        json_str = json.dumps(wowsinfo_dict, ensure_ascii=False)
        f.write(json_str)

    print('Done.')

def runAll():
    get_ship_battles_raw()
    get_personal_rating()
    make_additional()
    merge_additional()

if __name__ == '__main__':
    # check if --all is passed in 
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        runAll()
    else:
        make_additional()
        merge_additional()
