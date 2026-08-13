"""Ship domains: air defense, guns/torpedoes, components, consumables, ship params.

Moved from generate.py; survivability and armor come from the dedicated
domains.survivability and domains.armor modules.
"""
from domains.armor import unpack_armor, unpack_turret_armor
from domains.anti_air import unpack_anti_air
from domains.airstrike import unpack_airstrike
from domains.concealment import unpack_concealment
from domains.depth_charges import unpack_depth_charges
from domains.main_battery import unpack_main_battery
from domains.maneuverability import unpack_maneuverability
from domains.special_abilities import unpack_special_ability
from domains.survivability import unpack_survivability


class ShipMixin:
    # region Air Defense
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
    #endregion

    #region Guns & Torpedoes
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
    #endregion

    #region Ship Components
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

            # survivability and armor are separate domains under domains/
            ship_components['survivability'] = unpack_survivability(
                module, ship_components['health'])
            ship_components['armor'] = unpack_armor(module)

            # maneuverability and concealment are separate domains under domains/
            ship_components['maneuverability'] = unpack_maneuverability(module)
            ship_components['concealment'] = unpack_concealment(module)
        elif 'artillery' in module_type:
            artillery = {}
            artillery['range'] = module['maxDist']
            artillery['sigma'] = module['sigmaCount']
            artillery['guns'] = self._unpack_guns_torpedoes(module)
            if 'BurstArtilleryModule' in module:
                # this is now available only for a few ships
                artillery['burst'] = module['BurstArtilleryModule']
            ship_components.update(artillery)

            # turret armor belongs to the armor domain
            turrets = unpack_turret_armor(module)
            if len(turrets) > 0:
                ship_components['turrets'] = turrets

            # main battery domain: dispersion, firing arcs and turret stats
            ship_components['battery'] = unpack_main_battery(module)

            # check air defense
            air_defense = self._unpack_air_defense(module, params)
            ship_components.update(air_defense)
        elif 'atba' in module_type:
            secondaries = {}
            secondaries['range'] = module['maxDist']
            secondaries['sigma'] = module['sigmaCount']
            secondaries['guns'] = self._unpack_guns_torpedoes(module)
            ship_components.update(secondaries)

            # turret armor belongs to the armor domain
            turrets = unpack_turret_armor(module)
            if len(turrets) > 0:
                ship_components['turrets'] = turrets

            # main battery domain applies to secondary batteries as well
            ship_components['battery'] = unpack_main_battery(module)

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

            # anti-air domain: full aura and flak cloud details
            ship_components['antiAir'] = unpack_anti_air(module)
        elif 'airSupport' in module_type:
            air_support = {}
            # Since June 2025, planeName could be missing somehow...
            if 'planeName' in module:
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

            # airstrike domain: ASW strike details and the aircraft used
            ship_components['airstrike'] = unpack_airstrike(module, params)
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

            # depth charge domain: launcher and projectile details
            ship_components['depthCharge'] = unpack_depth_charges(
                module, params)
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

            # special abilities domain: structured rage / burst mode
            ship_components['specialAbility'] = unpack_special_ability(module)
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
        elif 'shield' in module_type:
            # TODO: not sure what this does
            pass
        elif 'phaserLasers' in module_type:
            # TODO: not sure what this does
            pass
        elif 'photonTorpedoes' in module_type:
            # TODO: not sure what this does
            pass
        elif 'innateSkills' in module_type:
            pass
        elif 'missiles' in module_type:
            # what???
            pass
        elif 'visualCustomizations':
            # ???
            pass
        else:
            raise Exception('Unknown module type: {}'.format(module_type))

        return {module_name: ship_components}
    #endregion

    #region Consumables
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
    #endregion

    #region Ship Params
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

        # !region and type + their lang key
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
    #endregion
