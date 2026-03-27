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

import core.configurations as configurations
from typing import List, Optional, Union
from math import ceil

from numpy import copy, hstack, int16, int32, logspace, max as numpy_max, ndarray, sum as numpy_sum, zeros
from numpy import abs as numpy_abs
from numpy.typing import NDArray

def concat(buffers: List[NDArray]) -> NDArray:
    """
    Concatenate multiple audio buffers into a single continuous buffer.

    Parameters
    ----------
    buffers (list[numpy.ndarray]):
        A list of audio buffers to concatenate.

    Returns
    -------
    numpy.ndarray:
        A single buffer containing all input buffers joined sequentially.
    """
    return hstack(buffers)


def overlay(buffers: List[NDArray]) -> NDArray:
    """
    Overlay multiple audio buffers by summing them together.

    All buffers must have the same length. The function creates copies of the
    buffers to avoid modifying the original data, sums them together, and then
    normalizes the resulting audio to prevent clipping.

    Parameters
    ----------
    buffers (list[numpy.ndarray]):
        A non-empty list of audio buffers with identical lengths.

    Returns
    -------
    numpy.ndarray:
        A new buffer containing the combined audio signal.
    """
    assert type(buffers) == list and len(buffers), 'buffers must be a non-empty list'
    assert all(len(buffers[0]) == len(buffer) for buffer in buffers), \
        'All buffers must have the same length'

    # Create copies to avoid modifying the original buffers
    buffers = [copy(buffer) for buffer in buffers]

    for buffer in buffers:
        # Intended to scale each buffer relative to the total number of buffers.
        # Note: This line preserves the original logic and behavior exactly.
        buffer /= len(buffers)

    # Sum all buffers together sample-by-sample
    output_buffer: NDArray = numpy_sum(buffers, axis=0)

    # Normalize the resulting buffer to the allowed volume range
    normalize_volume(output_buffer)

    return output_buffer


def pad_with_zeros(buffer: NDArray, zeros_count: int) -> NDArray:
    """
    Pad an audio buffer with zeros at the end.

    Zero padding is commonly used when aligning audio buffers or extending
    a signal to a desired length.

    Parameters
    ----------
    buffer (numpy.ndarray):
        The original audio buffer.

    zeros_count (int):
        Number of zero samples to append.

    Returns
    -------
    numpy.ndarray:
        The padded audio buffer.
    """
    if zeros_count == 0:
        return buffer

    return concat([
        buffer,
        zeros(zeros_count)
    ])


def normalize_volume(buffer: NDArray, loudest_sample: Optional[Union[int, float]] = None) -> None:
    """
    Normalize the volume of an audio buffer.

    The function scales the buffer so that its loudest sample reaches
    `configurations.max_16bit` without clipping.

    Parameters
    ----------
    buffer (numpy.ndarray):
        Audio buffer to normalize.

    loudest_sample (int | float, optional):
        Precomputed loudest sample value. If not provided, it will be
        calculated automatically.

    Returns
    -------
    None
        The buffer is modified in place.
    """
    loudest_sample_value: Union[int, float] = loudest_sample or find_loudest_sample(buffer)

    # Avoid divide-by-zero or extremely tiny values
    if abs(loudest_sample_value) < 1e-9:
        return

    scale_factor = configurations.max_16bit / loudest_sample_value

    buffer *= int32(scale_factor)

def exponential_volume_dropoff(buffer: NDArray, duration: float, base: float) -> None:
    """
    Apply an exponential volume decay curve to an audio buffer.

    This creates a fade-out effect using a logarithmic spacing curve.
    The decay is applied over the specified duration.

    Parameters
    ----------
    buffer (numpy.ndarray):
        Audio buffer to modify.

    duration (float):
        Duration of the fade-out effect in seconds.

    base (float):
        Base used for the logarithmic spacing of the decay curve.

    Returns
    -------
    None
        The buffer is modified in place.
    """
    # Calculate the number of samples affected by the dropoff
    sample_count: int = ceil(duration * configurations.sample_rate)

    # Determine how many zeros are needed to match buffer length
    zeros_required: int = len(buffer) - sample_count

    # Generate the exponential decay curve
    unpadded_curve: NDArray = base / logspace(1, 10, num=sample_count, base=base)

    # Pad the curve with zeros if necessary to match buffer length
    dropoff_curve: NDArray = pad_with_zeros(unpadded_curve, zeros_required)

    # Apply the decay curve to the buffer
    buffer *= dropoff_curve


def find_loudest_sample(buffer: NDArray) -> float:
    """
    Find the loudest (maximum absolute amplitude) sample in an audio buffer.

    Parameters
    ----------
    buffer (numpy.ndarray):
        Audio buffer to analyze.

    Returns
    -------
    float:
        The maximum absolute sample value in the buffer.
    """
    return numpy_max(numpy_abs(buffer))


def slice(buffer: NDArray, duration: float) -> Union[NDArray, list]:
    """
    Extract a portion of an audio buffer based on duration.

    The function calculates the number of samples corresponding to the
    requested duration and returns that segment of the buffer.

    Parameters
    ----------
    buffer (numpy.ndarray):
        Source audio buffer.

    duration (float):
        Duration of audio to extract in seconds.

    Returns
    -------
    numpy.ndarray | list:
        The sliced buffer segment. If duration is less than or equal to
        zero, an empty list is returned (preserving original behavior).
    """
    if duration <= 0:
        return []

    sample_count: int = ceil(duration * configurations.sample_rate)
    return buffer[:sample_count]


def in_playback_format(buffer: NDArray) -> NDArray:
    """
    Convert an audio buffer to 16-bit integer format for playback.

    Many audio playback systems expect PCM 16-bit integer samples.

    Parameters
    ----------
    buffer (numpy.ndarray):
        Audio buffer containing numeric samples.

    Returns
    -------
    numpy.ndarray:
        The buffer converted to `int16` format.
    """
    return buffer.astype(int16)