# %%
"""
import required modules and helper methods
"""
import glob
import json
import os
import re
from typing import List, Callable
from additional import merge_additional


from domains.common import HelpersMixin
from domains.items import ItemsMixin
from domains.ship import ShipMixin
class WoWsGenerate(HelpersMixin, ShipMixin, ItemsMixin):

    # store all language keys we use
    _lang_keys: List[str] = []
    _modifiers: dict = {}
    # store all regions, ship types and all other data we need
    _game_info: dict = {}

    def __init__(self):
        self._game_info['regions'] = {}
        self._game_info['types'] = {}

    def read(self):
        """
        Read game params and language files
        """
        print('Reading game params...')
        self._params = self._read_gameparams()
        print('Loaded game params!')
        self._params_keys = list(self._params.keys())
        self._lang = self._read_lang('en')
        # get all Japanese ship names
        self._lang_sg = self._read_lang('zh_sg')
        return self

    """
    Helper functions
    """

    # %%

    #region Core Generation
    def generate(self, game_path: str):
        if self._params is None:
            raise Exception('Call read() first')

        # TODO: make this a function when everything is done
        ships = {}
        achievements = {}
        exteriors = {}
        modernizations = {}
        skills = {}
        weapons = {}
        projectiles = {}
        aircrafts = {}
        abilitites = {}
        alias = {}
        ship_index = {}
        camoboost = {}
        dog_tag = {}
        for key in self._params_keys:
            item = self._params[key]
            item_type = item['typeinfo']['type']
            item_nation = item['typeinfo']['nation']
            item_species = item['typeinfo']['species']

            # key_name = 'PJSB018'
            # if not key_name in key:
            #     continue
            # if key_name in key:
            #     self._write_json(item, '{}.json'.format(key_name))
            #     # print(self._unpack_ship_params(item, params))
            #     exit(1)

            if item_species == 'Camoboost':
                camoboost[item['id']] = item

            if item_type == 'DogTag':
                dog_tag_index = item['index']
                dog_tag_id = item['id']
                dog_tag[dog_tag_id] = {
                    'index': dog_tag_index,
                }

            if item_type == 'Ship':
                ships.update(self._unpack_ship_params(item, self._params))
                ship_index[item['id']] = {
                    'index': item['index'],
                    'tier': item['level']
                }

                # get Japanese ship names
                if item['typeinfo']['nation'] == 'Japan':
                    alias.update(self._unpack_japanese_alias(
                        item, self._lang_sg))
            elif item_type == 'Achievement':
                achievements.update(self._unpack_achievements(item, key))
            elif item_type == 'Exterior':
                exteriors.update(self._unpack_exteriors(item, key))
            elif item_type == 'Modernization':
                modernization = self._unpack_modernization(item, self._params)
                if modernization != None:
                    modernizations.update(modernization)
            elif item_type == 'Crew':
                if key == 'PAW001_DefaultCrew':
                    # save the shared one
                    skills[key] = item
                    continue

                # TODO: move to unpack_crews
                if item['CrewPersonality']['isUnique'] == True:
                    skills[key] = item

                for s in item['Skills']:
                    modifiers = item['Skills'][s]['modifiers']
                    for m in modifiers:
                        self._modifiers[m] = modifiers[m]
            elif item_type == 'Gun':
                # weapons.update(self._unpack_weapons(item, key))
                continue
            elif item_type == 'Projectile':
                projectiles.update(self._unpack_projectiles(item, key))
            elif item_type == 'Aircraft':
                aircrafts.update(self._unpack_aircrafts(item, key))
            elif item_type == 'Ability':
                abilitites.update(self._unpack_abilities(item, key))

        # save everything
        if len(ships) == 0:
            raise Exception('No ships found. Data is not valid')

        # add the name in Chinese as title
        for camo in camoboost:
            curr = camoboost[camo]
            curr['title'] = self._lang_sg[self._IDS(curr['name'])]
        print("There are {} camoboosts in the game".format(len(camoboost)))
        self._write_json(camoboost, 'camoboost.json')
        print("There are {} dog tags in the game".format(len(dog_tag)))
        self._write_json(dog_tag, 'dog_tag.json')

        print("There are {} ships in the game".format(len(ships)))
        self._write_json(ships, 'ships.json')
        print("There are {} achievements in the game".format(len(achievements)))
        self._write_json(achievements, 'achievements.json')
        print("There are {} exteriors in the game".format(len(exteriors)))
        self._write_json(exteriors, 'exteriors.json')
        print("There are {} modernizations in the game".format(len(modernizations)))
        self._write_json(modernizations, 'modernizations.json')
        print("There are {} weapons in the game".format(len(weapons)))
        self._write_json(weapons, 'weapons.json')
        print("There are {} projectiles in the game".format(len(projectiles)))
        self._write_json(projectiles, 'projectiles.json')
        print("There are {} aircrafts in the game".format(len(aircrafts)))
        self._write_json(aircrafts, 'aircrafts.json')
        print("There are {} abilities in the game".format(len(abilitites)))
        self._write_json(abilitites, 'abilities.json')
        print("There are {} Japanese alias in the game".format(len(alias)))
        self._write_json(alias, 'alias.json')
        print("There are {} ship index in the game".format(len(ship_index)))
        self._write_json(ship_index, 'ship_index.json')
        print("We need {} language keys".format(len(self._lang_keys)))
        print("There are {} modifieris in the game".format(len(self._modifiers)))
        # get all modifier names
        modifiers_copy = self._modifiers.copy()
        for m in modifiers_copy:
            modifier_name = 'IDS_PARAMS_MODIFIER_' + m.upper()
            if not modifier_name in self._lang_sg:
                modifier_name = modifier_name + '_DESTROYER'
            if not modifier_name in self._lang_sg:
                modifier_name = 'IDS_' + m.upper()
            if not modifier_name in self._lang_sg:
                self._modifiers[m + '_name'] = 'UNKNOWN!!!'
                continue
            self._modifiers[m + '_name'] = self._lang[modifier_name]
        sorted_modifiers = dict(sorted(self._modifiers.items()))
        self._write_json(sorted_modifiers, 'modifiers.json')
        print("Save game info")
        self._convert_game_info()
        self._write_json(self._game_info, 'game_info.json')

        for key in self._lang.keys():
            # get all modifiers
            if self._match(key, ['IDS_PARAMS_MODIFIER_', 'IDS_MODULE_TYPE_', 'IDS_CAROUSEL_APPLIED_', 'IDS_SHIP_PARAM_', 'IDS_SKILL_', 'IDS_DOCK_RAGE_MODE_'], lambda x, y: x.startswith(y)):
                self._lang_keys.append(key)
            self._lang_keys += self._unpack_language()

        lang_file = {}
        # prepare for all languages
        all_langs = self._read_supported_langs()
        all_langs_keys = list(all_langs.keys())
        for key in all_langs_keys:
            lang_file[key] = {}

        for key in self._lang_keys:
            try:
                for lang in all_langs_keys:
                    lang_file[lang][key] = all_langs[lang][key]
            except KeyError:
                # TODO: there are too many missing keys, there are seems to be lots of missing data
                # TODO: maybe, we need to validate language key everytime we generate it, we should allow missing data
                print('Missing {}'.format(key))
        self._write_json(lang_file, 'lang.json')

        # game_maps = self._unpack_game_map()
        # print("There are {} game maps in the game".format(len(game_maps)))
        # self._write_json(game_maps, 'game_maps.json')

        commander_skills = self._unpack_commander_skills(skills)
        print("There are {} commander skills in the game".format(
            len(commander_skills)))
        self._write_json(commander_skills, 'commander_skills.json')
        skills = commander_skills['PAW001_DefaultCrew']['Skills']
        for skill in skills:
            # split when there is a capital letter with regex
            name = re.split(r'(?=[A-Z])', skill)[1:]
            name = '_'.join(name).upper()
            skills[skill]['name'] = 'IDS_SKILL_' + name
            skills[skill]['description'] = 'IDS_SKILL_DESC_' + name
        print("There are {} skills in the game".format(len(skills)))
        self._write_json(skills, 'skills.json')

        total_size = 0
        for json_name in glob.glob('*.json'):
            if 'GameParams' in json_name or 'wowsinfo' in json_name:
                continue
            total_size += self._sizeof_json(json_name)
        # total size in MB
        print("Total size: {:.2f} MB".format(total_size))

        # merge everything into one file
        wowsinfo = {}
        wowsinfo['ships'] = ships
        wowsinfo['achievements'] = achievements
        wowsinfo['exteriors'] = exteriors
        wowsinfo['modernizations'] = modernizations
        # wowsinfo['weapons'] = weapons
        wowsinfo['projectiles'] = projectiles
        wowsinfo['aircrafts'] = aircrafts
        wowsinfo['abilities'] = abilitites
        wowsinfo['alias'] = alias
        # wowsinfo['commander_skills'] = commander_skills
        wowsinfo['skills'] = skills
        wowsinfo['game'] = self._game_info
        # wowsinfo['game_maps'] = game_maps

        # read game_path to get the game version and if it is public test
        game_info_path = os.path.join(game_path, "game_info.xml")
        with open(game_info_path, 'r') as f:
            game_info = f.read()
            game_version = game_info.split('installed="')[1].split('"')[0]
            public_test = '<id>WOWS.PT.PRODUCTION</id>' in game_info
        wowsinfo['version'] = game_version + ('PT' if public_test else '')

        # TODO: to be added to app/data/
        self._write_json(wowsinfo, 'wowsinfo.json')
        print("Done")
    #endregion

#region Main
# %%
if __name__ == '__main__':
    import sys
    path = sys.argv[1]
    generate = WoWsGenerate()
    generate.read().generate(path)
#endregion
