"""Misc item domains: achievements, exteriors, upgrades, projectiles, aircraft,
abilities, game map, commander skills, aliases, language (moved from generate.py).
"""
from domains.aircraft import unpack_aircraft
from domains.depth_charges import unpack_depth_charge
from domains.shells import unpack_shell
from domains.torpedoes import unpack_torpedo

class ItemsMixin:
    #region Achievements
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
    # endregion

    #region Exterior
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
    #endregion

    #region Modernization
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
    #endregion

    #region Weapons
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
    #endregion

    #region Shells
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
            # torpedo domain: arming, homing and splash parameters
            projectile.update(unpack_torpedo(item))
        elif projectile_type == 'Artillery':
            projectile.update(self._unpack_shells(item))
            # shells domain: full ballistic and splash parameters
            projectile.update(unpack_shell(item))
        elif projectile_type == 'Bomb':
            # TODO: need to consider what we want from bomb
            projectile.update(self._unpack_shells(item))
            projectile.update(unpack_shell(item))
        elif projectile_type == 'SkipBomb':
            # TODO: same as above
            projectile.update(self._unpack_shells(item))
            projectile.update(unpack_shell(item))
        elif projectile_type == 'Rocket':
            # TODO: same as above
            projectile.update(self._unpack_shells(item))
            projectile.update(unpack_shell(item))
        elif projectile_type == 'PlaneDrop':
            # new in 15.7: shell-like plane drop payload
            projectile.update(self._unpack_shells(item))
            projectile.update(unpack_shell(item))
        elif projectile_type == 'DepthCharge':
            projectile['damage'] = item['alphaDamage']
            projectile['burnChance'] = item['burnProb']
            projectile['floodChance'] = item['uwCritical'] * 100
            # depth charge domain: detonation and splash parameters
            projectile.update(unpack_depth_charge(item))
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
        elif projectile_type == 'PlaneSeaMine':
            # TODO: we don't do this for now
            pass
        elif projectile_type == 'PhotonTorpedo':
            # TODO: we don't do this for now
            # what is this??
            pass
        elif projectile_type == 'Missile':
            # finally??
            pass
        else:
            # unknown projectile type
            raise Exception(
                'Unknown projectile type: {}'.format(projectile_type))
        return {key: projectile}
    #endregion

    #region Aircraft
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

        if aircraft_type in ['Fighter', 'Bomber', 'Skip', 'Scout', 'Dive', 'Smoke']:
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
        # aircraft domain: full squadron and attack parameters
        aircraft.update(unpack_aircraft(item))
        return {key: aircraft}
    #endregion

    #region Ability
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
    #endregion

    #region Game Map
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
    #endregion

    #region Commander Skills
    def _unpack_commander_skills(self, item: dict) -> dict:
        """
        Unpack the commander skills
        """
        skills = {}
        for key in item:
            skills[key] = item[key]
        return skills
    #endregion

    #region Alias IJN
    def _unpack_japanese_alias(self, item: dict, lang: dict) -> dict:
        """
        Unpack the japanese ship alias
        """
        ship_id = item['id']
        ship_index = item['index']
        return {ship_id: {'alias': lang[self._IDS(ship_index)]}}
    #endregion

    #region Lang
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
    #endregion

    #region Convert Game Info
    def _convert_game_info(self):
        """
        Convert game_info from dicts to lists
        """
        regions = self._game_info['regions']
        types = self._game_info['types']

        self._game_info['regions'] = list(regions.keys())
        self._game_info['types'] = list(types.keys())
    #endregion
