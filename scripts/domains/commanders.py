"""Commander domain: legendary and regular commanders.

Extracts every raw Crew entry (regular, unique/legendary, collab and event
commanders) with all of its fields, in the shape the WoWSFT app's
``Commander`` model reads (``commanders.json``). Most crews share the same
82-skill tree, so the tree is kept once (the canonical entry) and the other
entries reference it via ``skillsRef`` instead of duplicating it. Consumers
resolve a reference by looking up ``commanders[skillsRef]['Skills']``;
canonical entries are always emitted before references so a single pass
works. The ``identifier`` follows the production convention:
- unique commanders (e.g. Isoroku Yamamoto, Halsey, Seagal):
  ``IDS_<PERSON_NAME>``;
- non-unique Common commanders: ``IDS_CREW_LASTNAME_DEFAULT``.
"""

import copy
import hashlib
import json


def _skills_hash(skills: dict) -> str:
    """Hash a skill tree so identical trees can share one copy."""
    return hashlib.md5(
        json.dumps(skills, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def default_skills_hash(item: dict) -> str:
    """Hash of the standard (default crew) skill tree used as the baseline."""
    return _skills_hash(item.get('Skills', {}))


def _is_special(item: dict, skills_hash: str, default_hash: str) -> bool:
    """Keep only commanders with special skills or a special modifier."""
    personality = item.get('CrewPersonality', {})
    if personality.get('isUnique'):
        return True
    if item.get('UniqueSkills'):
        return True
    if personality.get('peculiarity', 'default') != 'default':
        return True
    # a custom skill tree different from the standard one is special
    if skills_hash and skills_hash != default_hash:
        return True
    return False


def unpack_commander(item: dict, key: str, skill_sets: dict,
                     default_hash: str):
    """Return a special commander entry, or ``None`` for normal crews.

    ``skill_sets`` maps a skill tree hash to the canonical commander key and
    must be owned by the caller so repeated runs never share stale state.
    """
    nation = item.get('typeinfo', {}).get('nation')
    personality = item.get('CrewPersonality', {})
    unique = personality.get('isUnique')

    # keep every field of the raw entry; deep copy so later pipeline steps
    # (e.g. skill name enrichment) cannot mutate the shared skill trees
    commander = copy.deepcopy(item)

    skills = item.get('Skills', {})
    skills_hash = _skills_hash(skills) if len(skills) > 0 else ''
    if not _is_special(item, skills_hash, default_hash):
        return None

    if len(skills) > 0:
        canonical = skill_sets.get(skills_hash)
        if canonical is None:
            skill_sets[skills_hash] = key
        elif canonical != key:
            commander['skillsRef'] = canonical
            del commander['Skills']

    if unique:
        person_name = str(personality.get('personName', '')).upper()
        commander['identifier'] = 'IDS_' + person_name
    elif nation == 'Common':
        commander['identifier'] = 'IDS_CREW_LASTNAME_DEFAULT'
    return commander
