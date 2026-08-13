"""Domain modules for the WoWs data generator.

Each domain extracts one aspect of a ship from the raw GameParams data.
Domains are implemented step by step, one file per domain (target 200-500
lines per file). Unimplemented domains keep a function signature and a TODO
list so the shape of the module is visible up front.

Implemented:
- survivability: HP sections, fire/flood stats, dive battery
- armor: hull armor zones, named armor values, barbettes, turret armor

Planned (in order):
- maneuverability, concealment, main_battery, shells, torpedoes, aircraft,
  anti_air, airstrike, depth_charges, special_abilities
"""

from domains.armor import unpack_armor, unpack_turret_armor
from domains.survivability import unpack_survivability

__all__ = [
    'unpack_armor',
    'unpack_survivability',
    'unpack_turret_armor',
]
