"""
Engine Sound Simulator+++

Derived from the original Engine Sound Simulator
created by jgardner8.

Original repository:
https://github.com/jgardner8/engine-sound-simulator

The original project did not include a license at the time
this fork was created. The original author retains copyright
over their work.

Modifications in this file:
- Code refactoring
- Documentation and comments
- Variable naming improvements
- Structural improvements

Copyright (c) 2026 AceBurgundy
"""

# Reference: https://en.wikipedia.org/wiki/Big-bang_firing_order

from typing import List, Union
import random as python_random
from numpy.typing import NDArray

import core.synthesisation as synthesisation  # type: ignore
import core.audio_tools as audio_tools
from core.engine import Engine

# Pre-generated combustion sound used by all engine configurations
_fire_sound = synthesisation.sine_wave_note(frequency=250, duration=1)
audio_tools.normalize_volume(_fire_sound)
audio_tools.exponential_volume_dropoff(_fire_sound, duration=0.01, base=5)

def single(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    Create a single-cylinder four-stroke engine configuration.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    return Engine(
        idle_rpm=2500,
        limiter_rpm=15000,
        strokes=4,
        cylinders=1,
        timing=[500],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def v2_90_degrees(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    90-degree V-twin configuration.

    Common examples:
    - Suzuki SV650 / SV1000
    - Yamaha MT-07

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    return Engine(
        idle_rpm=1000,
        limiter_rpm=10500,
        strokes=4,
        cylinders=2,
        timing=[270, 450],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def v2_60_degrees(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    60-degree V-twin configuration.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    return Engine(
        idle_rpm=1100,
        limiter_rpm=10500,
        strokes=4,
        cylinders=2,
        timing=[300, 420],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def v2_45_degrees(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    45-degree V-twin configuration typical of certain cruiser engines.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    return Engine(
        idle_rpm=800,
        limiter_rpm=7000,
        strokes=4,
        cylinders=2,
        timing=[315, 405],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )

def inline4(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    Standard inline-four engine configuration.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    return Engine(
        idle_rpm=800,
        limiter_rpm=7800,
        strokes=4,
        cylinders=4,
        timing=[180, 180, 180, 180],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )

def inline5(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    Inline-five engine configuration.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    cylinder_count: int = 5

    return Engine(
        idle_rpm=800,
        limiter_rpm=9000,
        strokes=4,
        cylinders=cylinder_count,
        timing=[720 / cylinder_count] * cylinder_count,
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )

def inline6(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    Inline-six engine configuration.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    return Engine(
        idle_rpm=800,
        limiter_rpm=7800,
        strokes=4,
        cylinders=6,
        timing=[120, 120, 120, 120, 120, 120],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )

def random_inline(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    Generic inline engine configuration using five cylinders.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    cylinder_count: int = 5

    return Engine(
        idle_rpm=800,
        limiter_rpm=9000,
        strokes=4,
        cylinders=cylinder_count,
        timing=[720 / cylinder_count] * cylinder_count,
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def inline5_crossplane(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    Inline-five cross-plane configuration.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    cylinder_count: int = 5

    return Engine(
        idle_rpm=800,
        limiter_rpm=9000,
        strokes=4,
        cylinders=cylinder_count,
        timing=[180, 90, 180, 90, 180],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def inline4_uneven_firing(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    Inline-four engine with randomized uneven firing intervals.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    cylinder_count: int = 4
    minimum_interval: int = 170
    maximum_interval: int = 190

    return Engine(
        idle_rpm=800,
        limiter_rpm=7800,
        strokes=4,
        cylinders=cylinder_count,
        timing=[
            python_random.uniform(minimum_interval, maximum_interval),
            python_random.uniform(minimum_interval, maximum_interval),
            python_random.uniform(minimum_interval, maximum_interval),
            python_random.uniform(minimum_interval, maximum_interval),
        ],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def boxer4_crossplane_custom(wave_sound: NDArray = _fire_sound, delay_offsets: List[int] = [0] * 4) -> Engine:
    """
    Boxer-four cross-plane configuration.

    Example application:
    Subaru WRX engine characteristics.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.

    delay_offsets : List[int]
        Custom delay offsets to create uneven firing intervals.
    """
    cylinder_count: int = 4
    base_angle: int = 180

    return Engine(
        idle_rpm=750,
        limiter_rpm=6700,
        strokes=4,
        cylinders=cylinder_count,
        timing=[base_angle, 360 - base_angle] * 2,
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
        unequal=delay_offsets,
    )


def boxer4_half(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    Two-cylinder boxer configuration representing half of a flat-four.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    cylinder_count: int = 2

    return Engine(
        idle_rpm=800,
        limiter_rpm=6700,
        strokes=4,
        cylinders=cylinder_count,
        timing=[180, 720 - 180],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def random(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    Generate a random firing timing configuration.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    cylinder_count: int = 4
    random_intervals: List[Union[int|float]]  = [
        python_random.randrange(
            int(360 / 5 / cylinder_count),
            int(1440 / 5 / cylinder_count),
        )
        * 5
        for _ in range(cylinder_count)
    ]

    return Engine(
        idle_rpm=800,
        limiter_rpm=9000,
        strokes=4,
        cylinders=cylinder_count,
        timing=random_intervals,
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def v4_45_degrees(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    45-degree V4 configuration.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    return Engine(
        idle_rpm=800,
        limiter_rpm=9000,
        strokes=4,
        cylinders=4,
        timing=[95, 255, 210, 345],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def v4_90_degrees(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    90-degree V4 configuration commonly used in high-performance motorcycles.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    return Engine(
        idle_rpm=1100,
        limiter_rpm=16500,
        strokes=4,
        cylinders=4,
        timing=[180, 90, 180, 270],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def fake_two_rotor_rotary(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    Simulated two-rotor rotary engine behavior.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    difference: int = 60

    return Engine(
        idle_rpm=800,
        limiter_rpm=8300,
        strokes=2,
        cylinders=2,
        timing=[difference, 720 - difference],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def inline4_with_one_spark_plug_disconnected(wave_sound: NDArray = _fire_sound) -> Engine:
    """
    Inline-four configuration simulating a disconnected spark plug.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.
    """
    return Engine(
        idle_rpm=800,
        limiter_rpm=7800,
        strokes=4,
        cylinders=3,
        timing=[180, 360, 180],
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
    )


def v12(wave_sound: NDArray = _fire_sound, delay_offsets: List[int] = [0] * 12) -> Engine:
    """
    v12 engine configuration with optional unequal firing adjustments.

    Parameters
    ----------
    wave_sound : NDArray
        The waveform to use for the combustion sound of the engine.

    delay_offsets : List[int]
        Custom delay offsets to create uneven firing intervals.
    """
    return Engine(
        idle_rpm=800,
        limiter_rpm=9000,
        strokes=4,
        cylinders=12,
        timing=[60] * 12,
        fire_sound=wave_sound,
        between_fire_sound=synthesisation.silence(1),
        unequal=delay_offsets,
    )