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

"""Synthesisation of primitive audio building blocks."""

import core.configurations as configurations

from math import ceil
from numpy import array, linspace, pi, sin, zeros
from numpy.typing import NDArray
from numpy import float64


def sine_wave_note(frequency: float, duration: float) -> NDArray[float64]:
    """
    Generate a sine wave audio buffer.

    Parameters
    ----------
    frequency (float):
        Frequency of the sine wave in Hertz.

    duration (float):
        Duration of the generated sound in seconds.

    Returns
    -------
    numpy.ndarray
        Audio buffer representing a sine wave.
    """
    # Calculate the total number of audio samples required
    sample_count: int = ceil(duration * configurations.sample_rate)

    # Generate evenly spaced time steps across the duration
    timesteps: NDArray[float64] = linspace(start=0, stop=duration, num=sample_count, endpoint=False)

    # Generate sine wave values for each timestep
    return sin(frequency * timesteps * 2 * pi)


def sawtooth_wave_note(frequency: float, duration: float) -> NDArray[float64]:
    """
    Generate a sawtooth wave audio buffer.

    Parameters
    ----------
    frequency (float):
        Frequency of the sawtooth wave in Hertz.

    duration (float):
        Duration of the generated sound in seconds.

    Returns
    -------
    numpy.ndarray
        Audio buffer representing a sawtooth wave.
    """
    # Calculate the total number of samples required
    sample_count: int = ceil(duration * configurations.sample_rate)

    # Generate time steps for the waveform
    timesteps: NDArray[float64] = linspace(start=0, stop=duration, num=sample_count, endpoint=False)

    # Convert to Python list for element-wise processing
    timesteps_list: list[float] = timesteps.tolist()

    # Generate the sawtooth waveform values
    timesteps_list = [
        1 - ((time_value * frequency * 2 * pi) % 1)
        for time_value in timesteps_list
    ]

    # Convert the list back to a NumPy array
    timesteps_array: NDArray[float64] = array(timesteps_list)

    # Scale the waveform by frequency
    return frequency * timesteps_array * 2 * pi


def random_wave_note(frequency: float, duration: float) -> NDArray[float64]:
    """
    Generate a random waveform buffer.

    The generated waveform uses a simple repeating fractional pattern
    derived from the sample index.

    Parameters
    ----------
    frequency (float):
        Frequency parameter (retained for compatibility with other
        waveform generators, although not directly used).

    duration (float):
        Duration of the generated sound in seconds.

    Returns
    -------
    numpy.ndarray
        Audio buffer representing a pseudo-random waveform.
    """
    # Determine how many samples are required
    sample_count: int = ceil(duration * configurations.sample_rate)

    # Generate time steps (not directly used but preserved for structure consistency)
    timesteps: NDArray[float64] = linspace(start=0, stop=duration, num=sample_count, endpoint=False)

    # Generate waveform values based on index modulo behavior
    return array([
        float(index % 1) - 1
        for index in range(len(timesteps))
    ])


def silence(duration: float) -> NDArray[float64]:
    """
    Generate an audio buffer containing silence.

    Parameters
    ----------
    duration (float):
        Duration of silence in seconds.

    Returns
    -------
    numpy.ndarray
        Audio buffer filled with zeros.
    """
    # Calculate number of samples for the specified duration
    sample_count: int = ceil(duration * configurations.sample_rate)

    # Create a zero-filled array representing silence
    return zeros(sample_count)