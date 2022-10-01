"""
Compare wowsinfo.json with wowsinfo.json.bak and check if there are new items.
Set `new` to true if it is a new item. Remove `new` if it is not a new item.
"""

import json
import os


def compare_new(public_test: bool) -> None:
    # make sure both wowsinfo.json and wowsinfo.json.bak exist
    if not os.path.isfile('wowsinfo.json'):
        raise Exception('wowsinfo.json not found')

    backup_file = 'wowsinfo.json.pt' if public_test else 'wowsinfo.json.live'
    if not os.path.isfile(backup_file):
        raise Exception(backup_file + ' not found')

    # read wowsinfo.json and wowsinfo.json.bak
    with open('wowsinfo.json', 'r', encoding='utf8') as info:
        wowsinfo = json.load(info)
    with open(backup_file, 'r', encoding='utf8') as info_old:
        wowsinfo_bak = json.load(info_old)
    with open('lang.json', 'r', encoding='utf8') as lang:
        english_lang = json.load(lang)['en']

    with open('changes.log', 'w', encoding='utf8') as changes:
        has_changes = False
        # compare wowsinfo.json and wowsinfo.json.bak
        for item in wowsinfo:
            # not all data needs to be compared
            if item in ['number', 'alias', 'projectiles', 'version']:
                continue
            # check added items
            for data in wowsinfo[item]:
                if data not in wowsinfo_bak[item]:
                    wowsinfo[item][data]['added'] = 1
                    try:
                        # get ids_name from data
                        ids_name = wowsinfo[item][data]['name']
                        name = english_lang[ids_name]
                    except KeyError:
                        name = data
                    print('- added', item, name, '({})'.format(data))
                    changes.write('- added {} {} ({})'.format(item, name, data))
                    has_changes = True
                else:
                    # remove the added key
                    if 'added' in wowsinfo[item][data]:
                        del wowsinfo[item][data]['added']
            # also check removed
            for data in wowsinfo_bak[item]:
                if data not in wowsinfo[item]:
                    try:
                        # get ids_name from data
                        ids_name = wowsinfo_bak[item][data]['name']
                        name = english_lang[ids_name]
                    except KeyError:
                        name = data
                    print('- removed', item, name, '({})'.format(data))
                    changes.write('- removed {} {} ({})\n'.format(item, name, data))
                    has_changes = True
        
        if not has_changes:
            print('No changes found')
            changes.write('No Changes')

    # write wowsinfo.json
    with open('wowsinfo.json', 'w', encoding='utf8') as info:
        json.dump(wowsinfo, info, ensure_ascii=False)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        raise Exception('Usage: %s <0 (pt) or 1 (live)>' % sys.argv[0])

    public_test = int(sys.argv[1]) == 0
    compare_new(public_test)
