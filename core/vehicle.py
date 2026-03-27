from typing import List, Union, Any, Optional
from dataclasses import dataclass
from numpy.typing import NDArray
from enum import Enum

class EngineStrokeType(Enum):
    """
    Enumeration representing engine stroke cycle types.

    Attributes
    ----------
    TWO_STROKE : int
        Represents a two-stroke engine cycle.
    FOUR_STROKE : int
        Represents a four-stroke engine cycle.
    """

    TWO_STROKE = 2
    FOUR_STROKE = 4


class Slope(Enum):
    """
    Enumeration representing torque curve slope characteristics.

    The values indicate how aggressively torque drops off
    as engine RPM increases. Lower values correspond to a
    steeper drop-off (heavier feel), while higher values
    indicate a flatter torque curve.

    Attributes
    ----------
    FLAT : float
        Minimal torque drop-off across RPM range.
    LIGHT : float
        Slight torque drop-off.
    MEDIUM : float
        Moderate torque drop-off.
    HEAVY : float
        Significant torque drop-off at higher RPM.
    EXTREME : float
        Massive torque drop-off at higher RPM.
    """

    FLAT = 0.70
    LIGHT = 0.55
    MEDIUM = 0.40
    HEAVY = 0.30
    EXTREME = 0.20

@dataclass
class Vehicle:
    """
    Data container representing vehicle specifications used in RPM simulation.

    Attributes
    ----------
    name : str
        Name of the vehicle.
    idle_rpm : int
        Engine idle speed in revolutions per minute.
    limiter_rpm : int
        Maximum RPM before limiter engages.
    strokes : EngineStrokeType
        Engine stroke type (e.g., two-stroke, four-stroke).
    cylinders : int
        Number of engine cylinders.
    timing : List[Union[int, float]]
        Crankshaft timing intervals for firing sequence.
    gears : List[float]
        Gear ratios for the transmission.
    stroke_length_mm : float
        Engine stroke length in millimeters.
    optimal_shift_rpm : int
        Recommended RPM for gear shifting.
    fire_sound : Optional[Any]
        Audio waveform for combustion events.
    between_fire_sound : Optional[Any]
        Audio waveform between combustion events.
    """
    name: str
    idle_rpm: int
    limiter_rpm: int
    strokes: EngineStrokeType
    cylinders: int
    timing: List[Union[int, float]]
    gears: List[float]
    stroke_length_mm: float
    optimal_shift_rpm: int
    fire_sound: Optional[NDArray] = None
    between_fire_sound: Optional[Any] = None
