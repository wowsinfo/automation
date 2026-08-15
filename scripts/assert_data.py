"""Real-data assertions for the generated bundle.

Checks that key 15.7 mechanics are actually exposed by the generator:
- Datong's alternative (switchable) HE ammo is linked from its artillery
  module and the projectile carries more than 17 mm penetration;
- Zorky has the switchable mode (burst) module exposed.

Run after generate.py from the scripts folder; exits non-zero when any
assertion fails so missing data cannot silently ship.

Usage:
    python assert_data.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    with open(os.path.join(HERE, name), encoding='utf8') as f:
        return json.load(f)


def _find_ship(ships, index):
    for ship in ships.values():
        if ship.get('index') == index:
            return ship
    return None


def _find_switchable(ship):
    for component in ship.get('components', {}).values():
        if isinstance(component, dict) and 'switchable' in component:
            return component['switchable']
    return None


def main():
    errors = []
    ships = _load('ships.json')
    projectiles = _load('projectiles.json')

    alt_he = 'PZPA096_100MM_HE_DATONG_ALT'

    datong = _find_ship(ships, 'PZSD728')
    if datong is None:
        errors.append('Datong (PZSD728) is missing from ships.json')
    else:
        switchable = _find_switchable(datong)
        if switchable is None:
            errors.append(
                'Datong has no switchable ammo module; '
                'SwitchableModeArtilleryModule is not exposed')
        else:
            ammo = switchable.get('secondaryAmmoList') or []
            if alt_he not in ammo:
                errors.append(
                    'Datong alt HE {} not in secondaryAmmoList: {}'.format(
                        alt_he, ammo))

    alt_shell = projectiles.get(alt_he)
    if alt_shell is None:
        errors.append('Datong alt HE shell is missing from projectiles.json')
    else:
        pen = alt_shell.get('penHE') or 0
        if pen <= 17:
            errors.append(
                'Datong alt HE penetration is not above 17 mm: {}'.format(pen))

    zorky = _find_ship(ships, 'PRSD111')
    if zorky is None:
        errors.append('Zorky (PRSD111) is missing from ships.json')
    elif _find_switchable(zorky) is None:
        errors.append('Zorky has no switchable (burst) module exposed')

    if errors:
        for error in errors:
            print('FAIL: {}'.format(error))
        sys.exit(1)

    pen = alt_shell.get('penHE') if alt_shell else None
    print('OK: Datong alt HE exposed (pen {} mm) via switchable ammo; '
          'Zorky burst module present'.format(pen))


if __name__ == '__main__':
    main()
