"""
Compare wowsinfo.json with wowsinfo.json.bak and check if there are new items.
Set `new` to true if it is a new item. Remove `new` if it is not a new item.
"""

import json
import os


def compare_new():
    # make sure both wowsinfo.json and wowsinfo.json.bak exist
    if not os.path.isfile('wowsinfo.json') or not os.path.isfile('wowsinfo.json.bak'):
        raise Exception('wowsinfo.json or wowsinfo.json.bak does not exist. place the last version of it in the same directory as this script.')

    # read wowsinfo.json and wowsinfo.json.bak
    with open('wowsinfo.json', 'r', encoding='utf8') as info:
        wowsinfo = json.load(info)
    with open('wowsinfo.json.bak', 'r', encoding='utf8') as info_old:
        wowsinfo_bak = json.load(info_old)

    # compare wowsinfo.json and wowsinfo.json.bak
    for item in wowsinfo:
        # not all data needs to be compared
        if item in ['number', 'alias', 'projectiles']:
            continue
        for data in wowsinfo[item]:
            if data not in wowsinfo_bak[item]:
                wowsinfo[item][data]['added'] = 1
                print(item, data, 'added')
            else:
                if 'added' in wowsinfo[item][data]:
                    print(item, data, 'removed')
                    del wowsinfo[item][data]['added']

    # write wowsinfo.json
    with open('wowsinfo.json', 'w', encoding='utf8') as info:
        json.dump(wowsinfo, info, ensure_ascii=False)


if __name__ == '__main__':
    compare_new()
