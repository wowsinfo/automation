"""Armor domain: hull armor zones, named armor values, barbettes and turrets.

Raw GameParams data:
- hull ``armor``: zone id -> armor thickness (mm) overlay on the 3D model.
- hull ``armourCit`` / ``armourCas`` / ``armourDeck`` / ``armourExtremities``:
  named aggregate values; usually ``[-1, -1]`` (not set) because the real
  layout lives in the ``armor`` zone dict.
- hull ``barbettes``: turret key -> list of barbette zone ids. The barbette
  zone ids are not resolved in GameParams, so they are kept raw (the
  thickness table lives in the model/geometry data, see wows-toolkit).
- turret modules (main battery / secondaries): each gun entry carries its own
  ``armor`` zone dict plus ``barrelDiameter`` and ``numBarrels``.
"""


def unpack_armor(hull: dict) -> dict:
    """Extract hull armor data from a raw hull module."""
    armor = {}

    zones = hull.get('armor')
    if isinstance(zones, dict) and len(zones) > 0:
        armor['zones'] = zones

    for field in ['armourCit', 'armourCas', 'armourDeck', 'armourExtremities']:
        value = hull.get(field)
        # -1 means the value is not set, the zone dict is the source of truth
        if value not in (None, [-1, -1]):
            armor[field[len('armour'):].lower()] = value

    barbettes = hull.get('barbettes')
    if isinstance(barbettes, dict) and len(barbettes) > 0:
        armor['barbettes'] = barbettes

    return armor


def unpack_turret_armor(module: dict) -> list:
    """Extract turret armor from an artillery or secondary battery module.

    A turret entry is any ``HP*`` key in the module whose value carries an
    ``armor`` zone dict and a ``barrelDiameter`` (i.e. a gun, not a torpedo
    launcher or an air defense aura).
    """
    turrets = []
    for key, entry in module.items():
        if not isinstance(entry, dict):
            continue
        if 'HP' not in key:
            continue
        if 'armor' not in entry or 'barrelDiameter' not in entry:
            continue
        turrets.append({
            'name': key,
            'caliber': entry['barrelDiameter'],
            'barrels': entry.get('numBarrels'),
            'armor': entry['armor'],
        })
    return turrets
