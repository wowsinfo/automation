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


class WoWsGenerate:

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

    def _read_lang(self, language: str) -> dict:
        return self._read_json('langs/{}_lang.json'.format(language))

    def _read_supported_langs(self) -> dict:
        """
        Read all language files and return a dict
        """
        lang_dict = {}
        for lang in self._list_dir('langs'):
            if '.git' in lang:
                continue

            lang = lang.replace('_lang.json', '')
            if not lang in ['en', 'ja', 'zh_sg', 'zh_tw']:
                continue
            print('Reading language {}...'.format(lang))
            lang_dict[lang] = self._read_lang(lang)
        return lang_dict

    def _read_json(self, filename: str) -> dict:
        with open(filename, 'r', encoding='utf8') as f:
            json_dict = json.load(f)
        return json_dict

    def _read_gameparams(self) -> dict:
        return self._read_json('GameParams-0.json')

    def _write_json(self, data: dict, filename: str):
        with open(filename, 'w', encoding='utf8') as f:
            json_str = json.dumps(data, ensure_ascii=False)
            f.write(json_str)

    def _sizeof_json(self, filename: str) -> float:
        """
        Get the size of a json file
        """
        return os.path.getsize(filename) / 1024 / 1024

    def _list_dir(self, dir: str) -> list:
        """
        List all files in a directory
        """
        return os.listdir(dir)

    def _roundUp(self, num: float, digits: int = 1) -> float:
        # TODO: in the future, we may need to keep more digits in case our calculation in app is not accurate
        return round(num, digits)

    def _match(self, text: str, patterns: List[str], method: Callable[[str, str], bool]) -> bool:
        """
        Match text with patterns
        """
        for pattern in patterns:
            if method(text, pattern):
                return True
        return False

    def _tree(self, data: any, depth: int = 2, tab: int = 0, show_value: bool = False):
        """
        Show the structure tree of a dict. This is useful when analysing the data.
        """
        if depth == 0:
            if show_value:
                if isinstance(data, dict):
                    print('{}- dict'.format('\t' * tab))
                else:
                    print('{}- {}'.format('\t' * tab, data))
            return
        if not isinstance(data, dict):
            # print empty string when it is empty
            if data == '':
                print('\t' * tab, '- empty string')
            else:
                print('{}- {}'.format('\t' * tab, data))
            return

        for level in data:
            print('\t' * tab + '- ' + level)
            self._tree(data[level], depth - 1, tab + 1, show_value=show_value)

    def _merge(self, weapons: dict) -> dict:
        # join same weapons together into one dict
        merged = []
        counter = []
        for w in weapons:
            if len(merged) == 0:
                merged.append(w)
                counter.append(1)
                continue

            found = False
            for m in merged:
                if w == m:
                    counter[merged.index(m)] += 1
                    found = True
                    break
            if not found:
                merged.append(w)
                counter.append(1)
        for m in merged:
            m['count'] = counter[merged.index(m)]
        return merged

    def _IDS(self, key: str) -> str:
        return 'IDS_' + key.upper()

    """
    Unpack helper functions
    """

    def _unpack_air_defense(self, module: dict, params: dict):
        """
        Unpack air defense info from module and return air_defense dict
        """
        air_defense = {}
        near = []
        medium = []
        far = []
        for aura_key in module:
            aura = module[aura_key]
            if not isinstance(aura, dict):
                continue
            if not 'type' in aura:
                continue
            if not aura['type'] in ['far', 'medium', 'near']:
                continue

            min_distance = aura['minDistance'] / 1000
            max_distance = aura['maxDistance'] / 1000

            damage = aura['areaDamage']
            # treat this as the bubble
            if damage == 0:
                bubbles = {}
                # handle black cloud (bubbles), this deals massive damage
                bubbles['inner'] = int(aura['innerBubbleCount'])
                bubbles['outer'] = int(aura['outerBubbleCount'])
                bubbles['rof'] = aura['shotDelay']
                bubbles['minRange'] = min_distance
                bubbles['maxRange'] = max_distance
                bubbles['hitChance'] = aura['hitChance']
                bubbles['spawnTime'] = aura['shotTravelTime']
                # value 7 is from WoWsFT, seems to be a fixed value
                bubbles['damage'] = aura['bubbleDamage'] * 7
                air_defense['bubbles'] = bubbles
                continue

            # not a bubble, treat this as a normal aa gun
            rate_of_fire = aura['areaDamagePeriod']
            if damage == 0:
                print(aura)
                raise ValueError(
                    'Damage should not be 0 if it is not a bubble!')
            dps = self._roundUp(damage / rate_of_fire)

            # get all AA guns
            aa_guns = aura['guns']
            aa_guns_info = []
            for aa_gun in aa_guns:
                gun_dict = {}
                gun = module[aa_gun]
                gun_dict['ammo'] = gun['name']
                gun_dict['each'] = int(gun['numBarrels'])
                gun_dict['reload'] = float(gun['shotDelay'])
                # don't forget about the lang key
                gun_dict['name'] = self._IDS(gun['name'])
                self._lang_keys.append(gun_dict['name'])
                aa_guns_info.append(gun_dict)

            air_defense_info = {}
            air_defense_info['minRange'] = min_distance
            air_defense_info['maxRange'] = max_distance
            air_defense_info['hitChance'] = aura['hitChance']
            air_defense_info['damage'] = damage
            air_defense_info['rof'] = self._roundUp(rate_of_fire, digits=2)
            air_defense_info['dps'] = dps
            air_defense_info['guns'] = self._merge(aa_guns_info)

            if 'Far' in aura_key:
                far.append(air_defense_info)
            elif 'Med' in aura_key:
                medium.append(air_defense_info)
            elif 'Near' in aura_key:
                near.append(air_defense_info)
            else:
                raise ValueError('Unknown air defense type: {}'.format(aura_key))

        if len(far) > 0:
            air_defense['far'] = far
        if len(medium) > 0:
            air_defense['medium'] = medium
        if len(near) > 0:
            air_defense['near'] = near
        return air_defense

    def _unpack_guns_torpedoes(self, module: dict) -> dict:
        """
        Unpack guns and torpedoes
        """
        weapons = []
        # check if
        for weapon_key in module:
            if not 'HP' in weapon_key:
                continue

            # check each gun / torpedo
            weapon_module = module[weapon_key]
            if not isinstance(weapon_module, dict):
                raise Exception('weapon_module is not a dict')

            current_weapon = {}
            current_weapon['reload'] = weapon_module['shotDelay']
            current_weapon['rotation'] = float(180.0 / weapon_module['rotationSpeed'][0])
            current_weapon['each'] = int(weapon_module['numBarrels'])
            current_weapon['ammo'] = weapon_module['ammoList']
            # this is used for ap penetration
            if 'vertSector' in weapon_module:
                current_weapon['vertSector'] = weapon_module['vertSector'][1]
            weapons.append(current_weapon)

        # join same weapons together into one dict
        return self._merge(weapons)

    def _unpack_ship_components(self, module_name: str, module_type: str, ship: dict, params: dict) -> dict:
        # TODO: how to air defense here??
        """
        Unpack the ship components
        """
        ship_components = {}

        module = ship[module_name]
        # TODO: break down into separate methods later
        if 'hull' in module_type:
            ship_components['health'] = module['health']
            # floodNode contains flood related info
            flood_nodes = module['floodNodes']
            flood_probablity = flood_nodes[0][0]
            torpedo_protecion = 100 - flood_probablity * 3 * 100
            # not all ships have a torpedo protection
            if torpedo_protecion >= 1:
                ship_components['protection'] = self._roundUp(
                    torpedo_protecion)

            concealment = {}
            visibility = module['visibilityFactor']
            visibility_plane = module['visibilityFactorByPlane']
            fire_coeff = module['visibilityCoefFire']
            fire_coeff_plane = module['visibilityCoefFireByPlane']
            # only need max value here, min is always 0
            # TODO: this value is always the same as visibilityPlane, can be removed
            visibility_submarine = module['visibilityFactorsBySubmarine']['PERISCOPE']
            concealment['sea'] = self._roundUp(visibility)
            concealment['plane'] = self._roundUp(visibility_plane)
            concealment['seaInSmoke'] = self._roundUp(
                module['visibilityCoefGKInSmoke']
            )
            concealment['planeInSmoke'] = self._roundUp(
                module['visibilityCoefGKByPlane']
            )
            concealment['submarine'] = self._roundUp(
                visibility_submarine
            )
            concealment['seaFireCoeff'] = fire_coeff
            concealment['planeFireCoeff'] = fire_coeff_plane
            # only for submodule, when it is under water
            if 'SubmarineBattery' in module:
                concealment['coeffSeaUnderwaterDepths'] = module['visibilityCoeffUnderwaterDepths']
                concealment['coeffPlanUnderwaterDepths'] = module['visibilityCoeffUnderwaterDepths']
            ship_components['visibility'] = concealment

            mobility = {}
            mobility['speed'] = module['maxSpeed']
            # speed underwater only for submarine
            if 'SubmarineBattery' in module:
                buoyancy_states = module['buoyancyStates']
                if 'DEEP_WATER_INVUL' in buoyancy_states:
                    speed_offset = buoyancy_states['DEEP_WATER_INVUL'][1]
                    mobility['speedUnderwater'] = self._roundUp(
                        mobility['speed'] * speed_offset)
            mobility['turningRadius'] = module['turningRadius']
            # got the value from WoWsFT
            mobility['rudderTime'] = self._roundUp(
                module['rudderTime'] / 1.305
            )
            ship_components['mobility'] = mobility

            # submarine battery, like capacity and regen rate
            if 'SubmarineBattery' in module:
                submarine_battery = {}
                submarine_battery['capacity'] = module['SubmarineBattery']['capacity']
                submarine_battery['regen'] = module['SubmarineBattery']['regenRate']
                ship_components['submarineBattery'] = submarine_battery
        elif 'artillery' in module_type:
            artillery = {}
            artillery['range'] = module['maxDist']
            artillery['sigma'] = module['sigmaCount']
            artillery['guns'] = self._unpack_guns_torpedoes(module)
            if 'BurstArtilleryModule' in module:
                # this is now available only for a few ships
                artillery['burst'] = module['BurstArtilleryModule']
            ship_components.update(artillery)

            # check air defense
            air_defense = self._unpack_air_defense(module, params)
            ship_components.update(air_defense)
        elif 'atba' in module_type:
            secondaries = {}
            secondaries['range'] = module['maxDist']
            secondaries['sigma'] = module['sigmaCount']
            secondaries['guns'] = self._unpack_guns_torpedoes(module)
            ship_components.update(secondaries)

            # check air defense
            air_defense = self._unpack_air_defense(module, params)
            ship_components.update(air_defense)
        elif 'torpedoes' in module_type:
            torpedo = {}
            torpedo['singleShot'] = module['useOneShot']
            torpedo['launchers'] = self._unpack_guns_torpedoes(module)
            ship_components.update(torpedo)
        elif 'airDefense' in module_type:
            air_defense = self._unpack_air_defense(module, params)
            ship_components.update(air_defense)
        elif 'airSupport' in module_type:
            air_support = {}
            plane_name = module['planeName']
            air_support['plane'] = plane_name
            plane_name_title = self._IDS(plane_name)
            air_support['name'] = plane_name_title
            self._lang_keys.append(plane_name_title)

            air_support['reload'] = module['reloadTime']
            air_support['range'] = self._roundUp(
                module['maxDist'] / 1000)
            air_support['chargesNum'] = module['chargesNum']
            ship_components.update(air_support)
        elif 'depthCharges' in module_type:
            depth_charge = {}
            depth_charge['reload'] = module['reloadTime']
            total_bombs = 0
            for launcher_key in module:
                launcher = module[launcher_key]
                if not isinstance(launcher, dict):
                    continue

                # TODO: just use the first launcher for now, this may change in the future
                if total_bombs == 0:
                    ammo_key = launcher['ammoList'][0]
                    depth_charge['ammo'] = ammo_key

                # accumulate the total number of bombs
                total_bombs += launcher['numBombs']
            total_bombs *= module['numShots']
            depth_charge['bombs'] = total_bombs
            depth_charge['groups'] = module['maxPacks']
            ship_components.update(depth_charge)
        elif 'fireControl' in module_type:
            # this may increase the range and also sigma
            ship_components = module
        elif 'flightControl' in module_type:
            pass
        elif module_type in ['torpedoBomber', 'diveBomber', 'fighter', 'skipBomber']:
            # just add planes in
            ship_components = module['planes']
        elif 'pinger' in module_type:
            # this seems to be the submarine pinger
            pinger = {}
            pinger['reload'] = module['waveReloadTime']
            pinger['range'] = module['waveDistance']
            sectors = module['sectorParams']
            if len(sectors) != 2:
                raise ValueError('pinger has more than 2 sectors')

            pinger['lifeTime1'] = sectors[0]['lifetime']
            pinger['lifeTime2'] = sectors[1]['lifetime']
            # TODO: taking the first value for now, this is metre per second
            pinger['speed'] = module['waveParams'][0]['waveSpeed'][0]
            ship_components.update(pinger)
        elif 'engine' in module_type:
            speedCoef = module['speedCoef']
            if speedCoef != 0:
                ship_components['speedCoef'] = speedCoef
        elif 'specials' in module_type:
            # For tier 11s, battleships have a special module. Also, for event ships
            if 'RageMode' in module:
                ship_components['rageMode'] = module['RageMode']
        elif 'airArmament' in module_type:
            # TODO: this could be the fighter, scoupter
            pass
        elif 'radars' in module_type:
            # TODO: this might be the radar on the ship, not the radar consumable
            pass
        elif 'chargeLasers' in module_type:
            # TODO: not sure what this does
            pass
        elif 'waves' in module_type:
            # TODO: not sure what this does
            pass
        elif 'axisLaser' in module_type:
            # TODO: not sure what this does
            pass
        elif 'abilities' in module_type:
            # TODO: not sure what this does
            pass
        elif 'directors' in module_type:
            # TODO: not sure what this does
            pass
        elif 'finders' in module_type:
            # TODO: not sure what this does
            pass
        elif 'wcs' in module_type:
            # TODO: not sure what this does
            pass
        else:
            raise Exception('Unknown module type: {}'.format(module_type))

        return {module_name: ship_components}

    def _unpack_consumables(self, abilities_dict: dict) -> list:
        """
        Unpack consumables
        """
        consumables = []
        for ability_key in abilities_dict:
            ability_slot = abilities_dict[ability_key]
            abilities = ability_slot['abils']
            if len(abilities) == 0:
                continue

            ability_list = []
            for a in abilities:
                ability_list.append({'name': a[0], 'type': a[1]})
            consumables.append(ability_list)
        return consumables

    def _unpack_ship_params(self, item: dict, params: dict) -> dict:
        # get the structure overall
        # self._tree(item, depth=2, show_value=True)
        ship_params = {}
        ship_index = item['index']
        ship_id = item['id']
        lang_key = self._IDS(ship_index)
        ship_params['name'] = lang_key
        ship_params['description'] = lang_key + '_DESCR'
        ship_params['year'] = lang_key + '_YEAR'
        self._lang_keys.append(lang_key)
        self._lang_keys.append(lang_key + '_DESCR')
        self._lang_keys.append(lang_key + '_YEAR')

        ship_params['paperShip'] = item['isPaperShip']
        ship_params['id'] = ship_id
        ship_params['index'] = ship_index
        ship_params['tier'] = item['level']

        # region and type + their lang key
        nation = item['typeinfo']['nation']
        species = item['typeinfo']['species']
        self._game_info['regions'][nation] = True
        self._game_info['types'][species] = True
        ship_params['region'] = nation
        ship_params['type'] = species
        nation_lang = self._IDS(nation.upper())
        species_lang = self._IDS(species.upper())
        ship_params['regionID'] = nation_lang
        ship_params['typeID'] = species_lang
        self._lang_keys.append(nation_lang)
        self._lang_keys.append(species_lang)

        if (len(item['permoflages']) > 0):
            ship_params['permoflages'] = item['permoflages']
        ship_params['group'] = item['group']
        # TODO: debug only, to be removed
        # ship_params['codeName'] = item['name']

        # consumables
        consumables = self._unpack_consumables(item['ShipAbilities'])
        ship_params['consumables'] = consumables

        # air defense can be the main battery, secondaries and dedicated air defense guns
        air_defense = {}

        # ShipUpgradeInfo is the key, simply relying on module_key is not reliable
        ship_upgrade_info = item['ShipUpgradeInfo']
        ship_params['costXP'] = ship_upgrade_info['costXP']
        ship_params['costGold'] = ship_upgrade_info['costGold']
        ship_params['costCR'] = ship_upgrade_info['costCR']

        # module and component are separated so we can take whichever we need from the app
        module_tree = {}
        component_tree = {}
        for module_key in ship_upgrade_info:
            current_module = ship_upgrade_info[module_key]
            if not isinstance(current_module, dict):
                continue

            if not module_key in params:
                raise Exception('{} is not in params'.format(module_key))

            # get the credit + xp needed for this module
            cost = {}
            module_cost = params[module_key]
            cost['costCR'] = module_cost['costCR']
            cost['costXP'] = module_cost['costXP']

            module_info = {}
            module_info['cost'] = cost

            module_type = current_module['ucType']

            # TODO: the dictionary seems to be sorted so this might not be necessary but just in case, we do this for now
            # find the index of the current module
            module_index = 0
            prev = current_module['prev']
            while prev != '':
                prev = ship_upgrade_info[prev]['prev']
                module_index += 1
            module_info['index'] = module_index

            # NOTE: all modules can have information about next ship, don't only check HULL
            if 'nextShips' in current_module:
                next_ship = current_module['nextShips']
                # there can be multiple next ships, write this to the root
                if len(next_ship) > 0:
                    if 'nextShips' not in ship_params:
                        ship_params['nextShips'] = []
                    # convert to ship id here
                    for s in next_ship:
                        # key PRSD309_Pr_48 is deleted, so for deleted ships, we need to allow invalid key
                        if s in params:
                            ship_params['nextShips'].append(params[s]['id'])

            # simply save it to the module tree
            components = current_module['components']
            module_info['components'] = components

            for component_key in components:
                # ignore empty components
                component_list = components[component_key]
                if len(component_list) == 0:
                    continue

                for component_name in component_list:
                    # there can be duplicates
                    if component_name in component_tree:
                        continue
                    component = self._unpack_ship_components(
                        component_name, component_key, item, params
                    )

                    first_value = next(iter(component.values()))
                    # remove empty values
                    if len(first_value) == 0:
                        continue
                    component_tree.update(component)

            # there can be multiple modules of the same type
            moduleName = self._IDS(module_key)
            module_info['name'] = moduleName
            self._lang_keys.append(moduleName)
            if module_type in module_tree:
                module_tree[module_type].append(module_info)
            else:
                module_tree[module_type] = [module_info]
        ship_params['modules'] = module_tree
        ship_params['components'] = component_tree

        if len(air_defense) > 0:
            ship_params['airDefense'] = air_defense
        return {ship_id: ship_params}

    def _unpack_achievements(self, item: dict, key: str) -> dict:
        """
        The app will handle icon, achievement name, and description
        """
        achievements = {}
        name = item['uiName'].upper()
        lang_name = 'IDS_ACHIEVEMENT_' + name
        description = 'IDS_ACHIEVEMENT_DESCRIPTION_' + name
        achievements['icon'] = name
        achievements['name'] = lang_name
        achievements['description'] = description
        self._lang_keys.append(lang_name)
        self._lang_keys.append(description)

        achievements['type'] = item['battleTypes']
        achievements['id'] = item['id']
        achievements['constants'] = item['constants']
        return {key: achievements}

    def _unpack_exteriors(self, item: dict, key: str) -> dict:
        """
        Unpack flags, camouflage and permoflages
        """
        exterior = {}
        exterior_type = item['typeinfo']['species']
        exterior['type'] = exterior_type
        # NOTE: ENSIGN should never be included in the app due to lots of issues
        if exterior_type == 'Ensign':
            return {}

        exterior['id'] = item['id']
        name = self._IDS(key)
        exterior['name'] = name
        self._lang_keys.append(name)
        exterior['icon'] = key

        costCR = item['costCR']
        if (costCR >= 0):
            exterior['costCR'] = costCR
        costGold = item['costGold']
        if (costGold >= 0):
            exterior['costGold'] = costGold
        # NOTE: this is gone after 0.11.6 update ONLY for camouflages
        if 'modifiers' in item and len(item['modifiers']) > 0:
            exterior['modifiers'] = item['modifiers']
            # save all the modifiers
            for modifierKey in exterior['modifiers']:
                self._modifiers[modifierKey] = exterior['modifiers'][modifierKey]

        if exterior_type == 'Flags':
            # add the description
            description = name + '_DESCRIPTION'
            exterior['description'] = description
            self._lang_keys.append(description)

        # exterior['name'] = item['name']
        # exterior['name'] = item['name']
        # exterior['name'] = item['name']
        # exterior['name'] = item['name']
        # exterior['name'] = item['name']
        return {key: exterior}

    def _unpack_modernization(self, item: dict, params: dict) -> dict:
        """
        Unpack ship upgrades
        """
        slot = item['slot']
        if (slot < 0):
            return

        name = item['name']
        lang_name = 'IDS_TITLE_' + name.upper()
        description = 'IDS_DESC_' + name.upper()
        self._lang_keys.append(lang_name)
        self._lang_keys.append(description)

        modernization = {}
        modernization['slot'] = slot
        modernization['id'] = item['id']
        modernization['name'] = lang_name
        modernization['icon'] = name
        modernization['description'] = description
        modernization['costCR'] = item['costCR']

        tag = item['tags']
        if len(tag) > 0:
            tag = tag[0]
            if tag == 'unique':
                modernization['unique'] = True
            elif tag == 'special':
                modernization['special'] = True
        modernization['costCR'] = item['costCR']
        if len(item['shiplevel']) > 0:
            modernization['level'] = item['shiplevel']
        if len(item['shiptype']) > 0:
            modernization['type'] = item['shiptype']
        if len(item['nation']) > 0:
            modernization['nation'] = item['nation']

        modifiers = item['modifiers']
        modernization['modifiers'] = modifiers
        # save all the modifiers
        for key in modifiers:
            self._modifiers[key] = modifiers[key]

        ships = item['ships']
        ships_id = []
        for ship in ships:
            if not ship in params:
                continue
            ships_id.append(params[ship]['id'])
        if len(ships_id) > 0:
            modernization['ships'] = ships_id

        excludes = item['excludes']
        excludes_id = []
        for exclude in excludes:
            if not exclude in params:
                continue
            excludes_id.append(params[exclude]['id'])
        if len(excludes_id) > 0:
            modernization['excludes'] = excludes_id
        return {name: modernization}

    def _unpack_weapons(self, item: dict, key: str) -> dict:
        """
        Unpack all weapons (anti-air, main battery, seondaries, torpedoes and more)
        """
        # TODO: to be removed because this is included in the ship, not sure if this is needed at all.
        # TODO: to be removed
        weapon = {}
        weapon_type = item['typeinfo']['species']
        weapon['type'] = weapon_type
        if 'ammoList' in item:
            weapon['ammo'] = item['ammoList']

        if weapon_type == 'DCharge':
            # depth charge
            pass
        elif weapon_type == 'Torpedo':
            # torpedoes
            pass
        elif weapon_type == 'AAircraft':
            # anti-aircraft
            pass
        elif weapon_type == 'Main':
            # main battery
            pass
        elif weapon_type == 'Secondary':
            # secondaries
            pass
        else:
            # unknown weapon type
            raise Exception('Unknown weapon type: {}'.format(weapon_type))
        return {key: weapon}

    def _unpack_shells(self, item: dict) -> dict:
        """
        Unpack shells, HE & AP shells, HE & AP bombs and more
        """
        projectile = {}
        ammo_type = item['ammoType']
        projectile['ammoType'] = ammo_type
        projectile['speed'] = item['bulletSpeed']
        projectile['weight'] = item['bulletMass']

        # HE & SAP penetration value
        pen_cs = item['alphaPiercingCS']
        if pen_cs > 0:
            projectile['penSAP'] = pen_cs
        pen_he = item['alphaPiercingHE']
        if pen_he > 0:
            projectile['penHE'] = pen_he

        projectile['damage'] = item['alphaDamage']
        burn_chance = item['burnProb']
        if burn_chance > 0:
            # AP and SAP cannot cause fires
            projectile['burnChance'] = burn_chance

        # ricochet angle
        ricochet_angle = item['bulletRicochetAt']
        if ricochet_angle <= 90:
            projectile['ricochetAngle'] = ricochet_angle
            projectile['ricochetAlways'] = item['bulletAlwaysRicochetAt']

        diameter = item['bulletDiametr']
        projectile['diameter'] = diameter
        if ammo_type == 'AP':
            ap_info = {}
            ap_info['diameter'] = diameter
            # get values needed to calculate the penetration of AP
            ap_info['weight'] = item['bulletMass']
            ap_info['drag'] = item['bulletAirDrag']
            ap_info['velocity'] = item['bulletSpeed']
            ap_info['krupp'] = item['bulletKrupp']
            projectile['ap'] = ap_info
            # caliber is not changing, and overmatch should ignore decimals & no rounding because 8.9 is the same as 8
            overmatch = int(diameter * 1000 / 14.3)
            projectile['overmatch'] = overmatch
            projectile['fuseTime'] = item['bulletDetonator']
        return projectile

    def _unpack_projectiles(self, item: dict, key: str) -> dict:
        """
        Unpack all projectiles, like shells, torpedoes, and more. This is launched, fired or emitted? from a weapon.
        """
        projectile = {}
        projectile_type = item['typeinfo']['species']
        projectile['type'] = projectile_type
        projectile_nation = item['typeinfo']['nation']
        projectile['nation'] = projectile_nation

        name = self._IDS(key)
        self._lang_keys.append(name)
        projectile['name'] = name

        if projectile_type == 'Torpedo':
            projectile['speed'] = item['speed']
            projectile['visibility'] = item['visibilityFactor']
            # TODO: divide by 33.3333 to become the real value here or in app?
            projectile['range'] = item['maxDist']
            projectile['floodChance'] = item['uwCritical'] * 100
            projectile['alphaDamage'] = item['alphaDamage']
            projectile['damage'] = item['damage']
            projectile['deepWater'] = item['isDeepWater']
            # deep water torpedoes cannot hit certain classes of ships
            ignore_classes = item['ignoreClasses']
            if len(ignore_classes) > 0:
                projectile['ignoreClasses'] = ignore_classes
        elif projectile_type == 'Artillery':
            projectile.update(self._unpack_shells(item))
        elif projectile_type == 'Bomb':
            # TODO: need to consider what we want from bomb
            projectile.update(self._unpack_shells(item))
        elif projectile_type == 'SkipBomb':
            # TODO: same as above
            projectile.update(self._unpack_shells(item))
        elif projectile_type == 'Rocket':
            # TODO: same as above
            projectile.update(self._unpack_shells(item))
        elif projectile_type == 'DepthCharge':
            projectile['damage'] = item['alphaDamage']
            projectile['burnChance'] = item['burnProb']
            projectile['floodChance'] = item['uwCritical'] * 100
            pass
        elif projectile_type == 'Mine':
            # TODO: we don't do this for now
            pass
        elif projectile_type == 'Laser':
            # TODO: we don't do this for now
            pass
        elif projectile_type == 'PlaneTracer':
            # TODO: we don't do this for now
            pass
        elif projectile_type == 'Wave':
            # TODO: we don't do this for now
            pass
        else:
            # unknown projectile type
            raise Exception(
                'Unknown projectile type: {}'.format(projectile_type))
        return {key: projectile}

    def _unpack_aircrafts(self, item: dict, key: str) -> dict:
        """
        Unpack aircraft, like fighter, bomber, and more.
        """
        aircraft = {}
        aircraft_type = item['typeinfo']['species']
        aircraft['type'] = aircraft_type
        aircraft['nation'] = item['typeinfo']['nation']
        name = self._IDS(key)
        self._lang_keys.append(name)
        aircraft['name'] = name

        if aircraft_type in ['Fighter', 'Bomber', 'Skip', 'Scout', 'Dive']:
            hangarSettings = item['hangarSettings']
            max_aircraft = hangarSettings['maxValue']
            aircraft['health'] = item['maxHealth']
            aircraft['totalPlanes'] = item['numPlanesInSquadron']
            aircraft['visibility'] = item['visibilityFactor']
            aircraft['speed'] = item['speedMoveWithBomb']
            if max_aircraft > 0:
                # get information for the CV rework
                aircraft_rework = {}
                aircraft_rework['restoreTime'] = hangarSettings['timeToRestore']
                aircraft_rework['maxAircraft'] = max_aircraft

                aircraft_rework['attacker'] = item['attackerSize']
                aircraft_rework['attackCount'] = item['attackCount']
                aircraft_rework['cooldown'] = item['attackCooldown']
                aircraft_rework['minSpeed'] = item['speedMin']
                aircraft_rework['maxSpeed'] = item['speedMax']

                # reference from WoWsFT
                boost_time = item['maxForsageAmount']
                aircraft_rework['boostTime'] = boost_time
                boost_regen = item['forsageRegeneration']
                # For super carriers, regeneration is 0
                if boost_regen != 0:
                    aircraft_rework['boostReload'] = boost_time / boost_regen
                aircraft_rework['bombName'] = item['bombName']

                # get consumables
                consumables = self._unpack_consumables(item['PlaneAbilities'])
                if len(consumables) > 0:
                    aircraft_rework['consumables'] = consumables
                aircraft['aircraft'] = aircraft_rework
        elif aircraft_type == 'Airship':
            # TODO: do this if needed
            pass
        elif aircraft_type == 'Auxiliary':
            # TODO: not doing this for now
            pass
        else:
            raise Exception('Unknown aircraft type: {}'.format(aircraft_type))
        return {key: aircraft}

    def _unpack_abilities(self, item: dict, key: str) -> dict:
        """
        Unpack abilities / consumables, like smoke screen, sonar, radar and more.
        """
        abilities = {}
        abilities['nation'] = item['typeinfo']['nation']
        # I think they are all free now, TODO: can be removed
        costCR = item['costCR']
        if costCR > 0:
            abilities['costCR'] = costCR
        costGold = item['costGold']
        if costGold > 0:
            abilities['costGold'] = costGold

        lang_key = key.upper()
        name = 'IDS_DOCK_CONSUME_TITLE_' + lang_key
        description = 'IDS_DOCK_CONSUME_DESCRIPTION_' + lang_key
        abilities['name'] = name
        abilities['id'] = item['id']
        abilities['description'] = description
        abilities['icon'] = key
        # prepare for any potential alternative name & description
        abilities['alter'] = {}
        self._lang_keys.append(name)
        self._lang_keys.append(description)

        ability_dict = {}
        for item_key in item:
            ability = item[item_key]
            if not isinstance(ability, dict):
                continue
            # typeinfo is not needed
            if item_key == 'typeinfo':
                continue

            current_ability = {}
            # remove empty values
            for ability_key in ability:
                value = ability[ability_key]
                if value is None or value == '':
                    continue
                if ability_key in ['SpecialSoundID', 'group'] or 'Effect' in ability_key:
                    continue

                if ability_key == 'preparationTime':
                    continue

                # https://github.com/WoWs-Info/WoWs-Game-Data/issues/17
                if ability_key in ['descIDs', 'titleIDs']:
                    continue
                if ability_key == 'iconIDs':
                    # save this to alter
                    icon_name = 'IDS_DOCK_CONSUME_TITLE_' + value.upper()
                    icon_description = 'IDS_DOCK_CONSUME_DESCRIPTION_' + value.upper()
                    abilities['alter'][value] = {
                        'name': icon_name,
                        'description': icon_description
                    }
                    self._lang_keys.append(icon_name)
                    self._lang_keys.append(icon_description)

                # save all the modifiers
                self._modifiers[ability_key] = value

                # write consumable type only once
                if ability_key == 'consumableType':
                    if not 'type' in abilities:
                        ability_type = value.upper()
                        abilities['filter'] = ability_type
                        type_lang = 'IDS_BATTLEHINT_TYPE_CONSUMABLE_' + ability_type
                        abilities['type'] = type_lang
                        self._lang_keys.append(type_lang)
                    continue

                if ability_key == 'fightersName':
                    current_ability[ability_key] = self._IDS(value)
                    continue

                # fix the name for the main battery reload boost, it is using `boostCoeff` but it should be `gmShotDelay`
                if '_ArtilleryBooster' in key and ability_key == 'boostCoeff':
                    ability_key = 'gmShotDelay'

                current_ability[ability_key] = value

            # ignore empty abilities
            if len(current_ability) > 0:
                ability_dict[item_key] = current_ability

        # remove alter if it is empty
        if len(abilities['alter']) == 0:
            del abilities['alter']

        abilities['abilities'] = ability_dict
        return {key: abilities}

    def _unpack_game_map(self) -> dict:
        """
        Unpack the game map
        """
        game_map = {}
        for f in self._list_dir('spaces'):
            if os.path.exists('spaces/{}/minimap_water.png'.format(f)):
                # valid map
                curr_map = {}
                map_name = f.upper()
                lang_name = 'IDS_SPACES/{}'.format(map_name)
                curr_map['name'] = lang_name
                curr_map['description'] = lang_name + '_DESCR'
                game_map[map_name] = curr_map
        return game_map

    def _unpack_commander_skills(self, item: dict) -> dict:
        """
        Unpack the commander skills
        """
        skills = {}
        for key in item:
            skills[key] = item[key]
        return skills

    def _unpack_japanese_alias(self, item: dict, lang: dict) -> dict:
        """
        Unpack the japanese ship alias
        """
        ship_id = item['id']
        ship_index = item['index']
        return {ship_id: {'alias': lang[self._IDS(ship_index)]}}

    def _unpack_language(self) -> list:
        """
        Get extra strings we need for the app
        """
        return ['IDS_SPECTATE_SWITCH_SHIP', 'IDS_MODERNIZATIONS', 'IDS_MODULE_TYPE_ABILITIES',
                # units
                'IDS_SECOND', 'IDS_KILOMETER', 'IDS_KILOGRAMM', 'IDS_KNOT', 'IDS_METER_SECOND', 'IDS_MILLIMETER', 'IDS_METER',
                'IDS_UNITS', 'IDS_UNITS_SECOND',
                # generic strings
                'IDS_SHIPS', 'IDS_BATTLES']

    def _convert_game_info(self):
        """
        Convert game_info from dicts to lists
        """
        regions = self._game_info['regions']
        types = self._game_info['types']

        self._game_info['regions'] = list(regions.keys())
        self._game_info['types'] = list(types.keys())

    # %%

    def generate(self):
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

        # TODO: to be added to app/data/
        self._write_json(wowsinfo, 'wowsinfo.json')
        print("Done")


# %%
if __name__ == '__main__':
    generate = WoWsGenerate()
    generate.read().generate()
