"""Concealment domain: detectability by sea/air, firing and smoke values.

Target data, mirroring ShipBuilder's ConcealmentDataContainer:
- detectability by sea and by air while firing (base * fire coefficient)
- detectability from submarines at periscope depth and the raw depth
  coefficient tables

Raw source: hull ``visibilityFactor``, ``visibilityFactorByPlane``,
``visibilityCoefFire``, ``visibilityCoefFireByPlane``,
``visibilityCoefGKInSmoke``, ``visibilityCoefGKByPlane``,
``visibilityFactorsBySubmarine``.
"""


def _round_up(num, digits: int = 1) -> float:
    factor = 10 ** digits
    return round(num * factor) / factor


def unpack_concealment(hull: dict) -> dict:
    """Extract concealment data from a raw hull module."""
    concealment = {}

    sea = hull.get('visibilityFactor')
    plane = hull.get('visibilityFactorByPlane')
    fire_coeff = hull.get('visibilityCoefFire')
    fire_coeff_plane = hull.get('visibilityCoefFireByPlane')

    if sea is not None and fire_coeff is not None:
        concealment['seaFire'] = _round_up(sea * fire_coeff)
    if plane is not None and fire_coeff_plane is not None:
        concealment['airFire'] = _round_up(plane * fire_coeff_plane)

    by_submarine = hull.get('visibilityFactorsBySubmarine')
    if isinstance(by_submarine, dict):
        periscope = by_submarine.get('PERISCOPE')
        if periscope is not None:
            concealment['fromSubsAtPeriscopeDepth'] = periscope
        concealment['bySubmarineDepth'] = by_submarine

    # raw coefficient tables for smoke and underwater depths, new data on
    # top of the existing sea/plane/smoke values
    for key in ['visibilityFactorInSmoke', 'visibilityCoefGKInSmoke',
                'visibilityCoefGKByPlane', 'visibilityCoeffUnderwaterDepths',
                'visibilityCoeffUnderwaterDepthsByPlane',
                'deepwaterVisionCoeff', 'deepwaterVisionToPlaneCoeff']:
        if key in hull:
            concealment[key] = hull[key]

    return concealment
