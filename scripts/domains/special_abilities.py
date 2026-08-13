"""Special abilities domain: structured rage / burst mode data.

Target data, mirroring ShipBuilder's SpecialAbilityDataContainer:
- duration, preparation, progress per action and progress name
- inactivity delay, progress loss interval/amount, auto usage
- trigger info (required count, sub ribbons, time limit, start enabled)
- modifiers and the raw mode name

Raw source: special module fields such as ``RageMode`` / ``BurstMode`` with
``boostDuration``, ``boostPreparation``, ``decrementCount``,
``decrementDelay``, ``decrementPeriod``, ``modifiers``.
"""


def _unpack_rage(rage: dict) -> dict:
    """Structure the raw rage mode module."""
    ability = {'mode': 'rage'}

    trigger = rage.get('GameLogicTrigger')
    if isinstance(trigger, dict):
        action = trigger.get('Action')
        if isinstance(action, dict):
            ability['progressPerAction'] = action.get('progress')
            ability['progressName'] = action.get('progressName')
        activator = trigger.get('Activator')
        if isinstance(activator, dict):
            ability['requiredCount'] = activator.get('requiredCount')
            ability['subRibbons'] = activator.get('subRibbons')
            ability['timeLimit'] = activator.get('timeLimit')
            ability['separateTracking'] = activator.get('separateTracking')
        ability['startEnabled'] = trigger.get('startEnabled')

    for raw, name in [('rageModeName', 'name'), ('boostDuration', 'duration'),
                      ('boostPreparation', 'preparation'),
                      ('decrementDelay', 'inactivityDelay'),
                      ('decrementPeriod', 'progressLossInterval'),
                      ('decrementCount', 'progressLossPerInterval'),
                      ('isAutoUsage', 'autoUsage'),
                      ('modifiers', 'modifiers')]:
        if raw in rage:
            ability[name] = rage[raw]

    return ability


def unpack_special_ability(module: dict) -> dict:
    """Extract special ability data from a raw ship module."""
    ability = {}

    rage = module.get('RageMode')
    if isinstance(rage, dict):
        ability['rage'] = _unpack_rage(rage)

    burst = module.get('BurstArtilleryModule')
    if isinstance(burst, dict):
        ability['burst'] = burst

    return ability
