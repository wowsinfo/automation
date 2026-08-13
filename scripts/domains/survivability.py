"""Survivability domain: ship HP sections, fire/flood stats and dive battery.

Raw GameParams hull data:
- HP sections: ``Bow``, ``Cas`` (casemate), ``Cit`` (citadel), ``Hull``,
  ``SG`` (steering gear / auxiliary rooms), ``SS`` + ``SSC`` (superstructure),
  ``St`` (stern) and ``Ammo_*`` (magazines). Each section has ``maxHP``,
  ``regeneratedHPPart`` (regen ratio) and ``autoRepairTime``.
- ``burnNodes``: ``[[chance, tickDamagePct, duration], ...]`` (the first
  element is the raw chance value, the last two are % max HP damage per
  second and the duration in seconds)
- ``floodNodes``: ``[[chance, tickDamagePct, duration], ...]`` (same shape;
  the chance is also used to derive torpedo protection)
- ``SubmarineBattery``: ``capacity`` and ``regenRate`` (submarines only).

The output mirrors what ShipBuilder exposes in its SurvivabilityDataContainer
(section HP + regen ratio, fire/flood spots/duration/DPS/total damage,
torpedo protection, dive capacity/recharge).
"""

# Friendly section name -> raw GameParams hit location key(s).
# SS + SSC and SG + Ammo_* are combined because they are the same section
# type split across several raw hit locations.
SECTION_MAP = {
    'citadel': 'Cit',
    'casemate': 'Cas',
    'bow': 'Bow',
    'stern': 'St',
    'superstructure': ['SS', 'SSC'],
    'auxiliaryRooms': ['SG', 'Ammo_1', 'Ammo_2'],
    'hull': 'Hull',
}


def _round_up(num: float, digits: int = 1) -> float:
    """Round a number away from zero, keeping `digits` decimals."""
    factor = 10 ** digits
    return round(num * factor) / factor


def _unpack_section(raw_keys, hull: dict) -> dict:
    """Unpack one or more raw hit locations into a single section."""
    if isinstance(raw_keys, str):
        raw_keys = [raw_keys]

    hp = 0.0
    regen_ratio = None
    auto_repair_time = None
    for key in raw_keys:
        section = hull.get(key)
        if not isinstance(section, dict):
            continue
        hp += section.get('maxHP', 0.0)
        if regen_ratio is None:
            regen_ratio = section.get('regeneratedHPPart')
        if auto_repair_time is None:
            auto_repair_time = section.get('autoRepairTime')

    if hp == 0.0:
        return None

    section_info = {'hp': hp}
    if regen_ratio is not None:
        section_info['regenRatio'] = regen_ratio
    if auto_repair_time is not None:
        section_info['autoRepairTime'] = auto_repair_time
    return section_info


def _unpack_status(nodes: list, health: float) -> dict:
    """Unpack burn/flood node arrays into a status dict."""
    if not nodes or not isinstance(nodes[0], list) or len(nodes[0]) < 3:
        return {}

    first = nodes[0]
    chance = first[0]
    tick_damage_pct = first[1]
    duration = first[2]

    status = {
        'spots': len(nodes),
        'chance': chance,
        'duration': duration,
        'tickDamagePct': tick_damage_pct,
        'dps': round(health * tick_damage_pct / 100),
        'totalDamage': round(health * tick_damage_pct / 100 * duration),
    }
    return status


def unpack_survivability(hull: dict, health: float) -> dict:
    """Extract survivability data from a raw hull module."""
    survivability = {}

    sections = {}
    for name, raw_keys in SECTION_MAP.items():
        section = _unpack_section(raw_keys, hull)
        if section is not None:
            sections[name] = section
    if len(sections) > 0:
        survivability['sections'] = sections

    fire = _unpack_status(hull.get('burnNodes', []), health)
    if len(fire) > 0:
        survivability['fire'] = fire

    flood = _unpack_status(hull.get('floodNodes', []), health)
    if len(flood) > 0:
        # torpedo protection is derived from the flood chance, same formula
        # as the existing hull protection value in generate.py
        flood['torpedoProtection'] = _round_up(
            100 - flood['chance'] * 3 * 100)
        survivability['flood'] = flood

    battery = hull.get('SubmarineBattery')
    if isinstance(battery, dict):
        dive_battery = {}
        if 'capacity' in battery:
            dive_battery['capacity'] = battery['capacity']
        if 'regenRate' in battery:
            dive_battery['regen'] = battery['regenRate']
        if len(dive_battery) > 0:
            survivability['diveBattery'] = dive_battery

    return survivability
