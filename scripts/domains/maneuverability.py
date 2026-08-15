"""Maneuverability domain: speeds, acceleration params, submarine depth speeds.

Target data, mirroring ShipBuilder's ManeuverabilityDataContainer:
- max reverse speed (derived from max speed with the ShipBuilder formula)
- submarine speeds at surface / periscope / max depth (forward + reverse),
  max dive speed, diving plane shift time (submarines only)
- raw acceleration parameters used by the drag simulation (engine power,
  side drag, backward power/drag, cooling off speed)

Raw source: hull module fields such as ``maxSpeed``, ``backwardPowerCoef``,
``backwardMovementDragCoef``, ``buoyancyStates``, ``buoyancyRudderTime``,
``turningRadius``, ``rudderTime``, ``enginePower``, ``sideDragCoef``,
``maxBuoyancySpeed``, ``SubmarineBattery``.
"""


def _round_up(num, digits: int = 2) -> float:
    factor = 10 ** digits
    return round(num * factor) / factor


def _state_speed_coeff(states: dict, state: str):
    """Return the speed coefficient of a buoyancy state."""
    value = states.get(state)
    if isinstance(value, list) and len(value) > 1:
        return value[1]
    return None


def unpack_maneuverability(hull: dict) -> dict:
    """Extract maneuverability data from a raw hull module."""
    maneuverability = {}

    max_speed = hull.get('maxSpeed')
    if max_speed is not None:
        # base max reverse speed, ShipBuilder formula without the engine
        # speed coefficient (the app applies engine modifiers on top)
        maneuverability['maxReverseSpeed'] = _round_up(max_speed / 4 + 4.9)

    # rudder blast protection comes from the steering gear hit location
    steering = hull.get('SG')
    if isinstance(steering, dict) and 'armorCoeff' in steering:
        maneuverability['rudderBlastProtection'] = steering['armorCoeff']

    # submarine specific speeds, gated the same way as the existing
    # submarineBattery extraction (SubmarineBattery only exists on subs)
    if 'SubmarineBattery' in hull and max_speed is not None:
        states = hull.get('buoyancyStates')
        if isinstance(states, dict):
            reverse_speed = maneuverability.get('maxReverseSpeed', 0.0)

            def _speed_for(state):
                coeff = _state_speed_coeff(states, state)
                if coeff is None:
                    return None
                return _round_up(max_speed * coeff)

            def _reverse_for(state):
                coeff = _state_speed_coeff(states, state)
                if coeff is None:
                    return None
                return _round_up(reverse_speed * coeff)

            submarine = {}
            for state in ['SURFACE', 'PERISCOPE']:
                speed = _speed_for(state)
                reverse = _reverse_for(state)
                if speed is not None:
                    submarine['maxSpeedAt{}'.format(state.title())] = speed
                if reverse is not None:
                    submarine['maxReverseSpeedAt{}'.format(
                        state.title())] = reverse

            # max depth uses the DEEP_WATER states (INVUL is the actual max)
            deep_coeff = _state_speed_coeff(states, 'DEEP_WATER')
            if deep_coeff is None:
                deep_coeff = _state_speed_coeff(states, 'DEEP_WATER_INVUL')
            if deep_coeff is not None:
                submarine['maxSpeedAtMaxDepth'] = _round_up(
                    max_speed * deep_coeff)
                submarine['maxReverseSpeedAtMaxDepth'] = _round_up(
                    reverse_speed * deep_coeff)

            if 'maxBuoyancySpeed' in hull:
                submarine['maxDiveSpeed'] = hull['maxBuoyancySpeed']
            if 'buoyancyRudderTime' in hull:
                submarine['divingPlaneShiftTime'] = hull['buoyancyRudderTime']

            if len(submarine) > 0:
                maneuverability['submarine'] = submarine

    # raw acceleration parameters for the drag simulation (used by
    # ShipBuilder's AccelerationCalculator and wows-toolkit ballistics)
    raw = {}
    for key in ['enginePower', 'sideDragCoef', 'backwardMovementDragCoef',
                'backwardPowerCoef', 'coolingOffSpeed', 'speedCoef',
                'maxRudderAngle', 'rudderPower', 'underwaterMaxRudderAngle']:
        if key in hull:
            raw[key] = hull[key]
    if len(raw) > 0:
        maneuverability['raw'] = raw

    return maneuverability
