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

from numpy import (
    array,
    ones,
    zeros,
    arange,
    interp,
    convolve
)

from typing import List, Union, Optional, cast, Any
from random import uniform
from numpy.typing import NDArray

import core.configurations as configurations
import core.audio_tools as audio_tools

class Engine:
    """
    Unified engine simulation supporting two synthesis modes.

    1. Procedural engine cycle synthesis (original model)
    2. Granular combustion sample playback (pop mode)
    """

    def __init__(
        self,
        idle_rpm: Union[int, float],
        limiter_rpm: Union[int, float],
        strokes: int,
        cylinders: int,
        timing: List[Union[int, float]],
        fire_sound: NDArray,
        between_fire_sound: NDArray,
        unequal: List[int] = [],
        pop_sample: Optional[NDArray] = None,
        pop_mode: bool = False,
        exhaust_resonance: bool = False
    ) -> None:
        """
        Initialize the engine simulation model.

        Parameters
        ----------
        idle_rpm (Union[int, float]):
            Engine idle RPM.

        limiter_rpm (Union[int, float]):
            Maximum allowed RPM.

        strokes (int):
            Number of strokes in the engine cycle.

        cylinders (int):
            Number of engine cylinders.

        timing (List[Union[int, float]]):
            Firing timing offsets.

        fire_sound (NDArray):
            Audio sample representing the combustion event.

        between_fire_sound (NDArray):
            Audio sample used between combustion events.

        unequal (List[int]):
            Optional cylinder delay offsets in milliseconds.

        pop_sample (Optional[NDArray]):
            Combustion sample used for granular playback.

        pop_mode (bool):
            Enables granular combustion playback.

        exhaust_resonance (bool):
            Enables exhaust resonance filtering.
        """
        self._audio_buffer: NDArray = zeros([256])

        self.rpm: Union[int, float] = idle_rpm
        self.idle_rpm: Union[int, float] = idle_rpm
        self.limiter_rpm: Union[int, float] = limiter_rpm

        self.strokes: int = strokes
        self.cylinders: int = cylinders

        self.timing: List[Union[int, float]] = timing
        self._convert_timing_format(self.timing)

        self.fire_sound: NDArray = fire_sound
        self.between_fire_sound: NDArray = between_fire_sound

        if not unequal:
            unequal = [0] * cylinders

        self.unequal: List[int] = unequal

        self.unequal_more: NDArray = zeros([0])
        self.previous_ms: float = 0

        # Granular combustion mode parameters
        self.pop_sample: Optional[NDArray] = pop_sample
        self.pop_mode: bool = pop_mode
        self.exhaust_resonance: bool = exhaust_resonance

        # Active granular playback grains
        self.active_grains: List[List[Any]] = []
        self.time_since_last_fire: float = 0.0

        self.sample_rate: int = configurations.sample_rate

    def _convert_timing_format(self, timing: List[Union[int, float]]) -> None:
        """
        Convert cylinder timing offsets into cumulative format.

        Parameters
        ----------
        timing (List[Union[int, float]]):
            Cylinder timing offsets.
        """
        timing[0] = 0

        # Convert timing offsets into cumulative format for easier scheduling of fire events. Each timing value represents the offset from the previous cylinder's fire event, so we sum them up to get the absolute timing for each cylinder in the engine cycle. This allows us to easily determine when each cylinder should fire during the engine cycle based on the RPM and stroke timing.
        for index in range(1, len(timing)):
            timing[index] += timing[index - 1]

    def _spawn_grain(self) -> None:
        """
        Spawn a new combustion grain for granular playback.
        """
        if self.pop_sample is None:
            return

        # Apply random pitch and volume variations to each grain for a more natural sound. The pitch variation is subtle to avoid sounding unnatural, while the volume variation is slightly more pronounced to simulate the variability in combustion intensity.
        pitch: float = 1 + uniform(-0.02, 0.02)
        volume: float = 1 + uniform(-0.05, 0.05)

        # Calculate the indices for resampling the pop sample based on the desired pitch. We use linear interpolation to create a new grain that matches the pitch variation. The indices are spaced according to the pitch factor, which allows us to speed up or slow down the sample without changing its length.
        indices = arange(0, len(self.pop_sample), pitch)

        # Interpolate the pop sample to create the grain with the desired pitch. The interp function takes the calculated indices and maps them to the original sample values, effectively resampling the audio data to achieve the pitch variation. This allows us to create a more dynamic and realistic engine sound when using granular playback.
        grain = interp(
            indices,
            arange(len(self.pop_sample)),
            self.pop_sample
        )

        grain *= volume
        self.active_grains.append([grain, 0])

    def _generate_audio_pop_mode(self, sample_count: int) -> NDArray:
        """
        Generate audio using granular combustion playback.

        Parameters
        ----------
        sample_count (int):
            Number of audio samples to generate.

        Returns
        -------
        NDArray
            Generated audio buffer.
        """
        output: NDArray = zeros(sample_count)
        fires_per_second: float = (self.rpm / 60.0) * (self.cylinders / 2)

        if fires_per_second <= 0:
            return output

        interval: float = self.sample_rate / fires_per_second

        for index in range(sample_count):
            # Increment time since last fire and spawn new grains if it's time to fire
            self.time_since_last_fire += 1

            while self.time_since_last_fire >= interval:
                self._spawn_grain()
                self.time_since_last_fire -= interval

            sample_value: float = 0
            # Sum contributions from all active grains and remove grains that have finished playing
            for grain in list(self.active_grains):

                data, data_index = grain

                if data_index < len(data):
                    sample_value += data[data_index]
                    grain[1] += 1
                else:
                    self.active_grains.remove(grain)

            output[index] = sample_value

        # Apply a simple high-pass filter to simulate exhaust resonance if enabled
        if self.exhaust_resonance:
            output = convolve(output, [1, -0.97], mode="same")

        return audio_tools.in_playback_format(output)

    def _generate_audio_one_engine_cycle(self) -> NDArray:
        """
        Generate audio for one complete engine cycle using procedural synthesis.

        Returns
        -------
        NDArray
            Generated engine cycle audio buffer.
        """
        # Calculate timing parameters based on RPM and engine configuration
        strokes_per_minute: float = self.rpm * 2
        strokes_per_second: float = strokes_per_minute / 60

        # Calculate the total duration of one engine cycle in seconds, which is the time between the first and last fire events. This is determined by the number of strokes and the firing frequency.
        seconds_between_fires: float = self.strokes / strokes_per_second

        fire_duration: float = seconds_between_fires / self.strokes
        between_fire_duration: float = (
            seconds_between_fires / self.strokes * (self.strokes - 1)
        )

        equal_buffers: List[NDArray] = []
        unequal_buffers: List[NDArray] = []

        fire_sound: NDArray = cast(
            NDArray,
            audio_tools.slice(self.fire_sound, fire_duration)
        )

        # For each cylinder, calculate the timing of the fire sound and split the between-fire sound into before and after segments. If there is an unequal delay, place the fire sound in the unequal buffer and silence in the equal buffer, and vice versa if there is no delay. This allows us to overlay them later without timing issues.
        for cylinder_index in range(self.cylinders):

            unequal_delay_seconds: float = (
                self.unequal[cylinder_index] / 1000
                if self.unequal[cylinder_index] > 0
                else 0
            )

            before_fire_duration: float = (
                (self.timing[cylinder_index] / 180)
                / strokes_per_second
            )

            before_fire_sound: NDArray = cast(
                NDArray,
                audio_tools.slice(
                    self.between_fire_sound,
                    before_fire_duration + unequal_delay_seconds
                )
            )

            after_fire_duration: float = (
                between_fire_duration - before_fire_duration
            )

            after_fire_sound: NDArray = cast(
                NDArray,
                audio_tools.slice(
                    self.between_fire_sound,
                    after_fire_duration
                )
            )

            # If there is an unequal delay, place the fire sound in the unequal buffer and silence in the equal buffer, and vice versa if there is no delay. This allows us to overlay them later without timing issues.
            if unequal_delay_seconds:

                unequal_buffers.append(
                    audio_tools.concat([
                        before_fire_sound,
                        fire_sound,
                        after_fire_sound
                    ])
                )

                equal_buffers.append(
                    array([0] * len(unequal_buffers[-1]))
                )

            else:

                equal_buffers.append(
                    audio_tools.concat([
                        before_fire_sound,
                        fire_sound,
                        after_fire_sound
                    ])
                )

                unequal_buffers.append(
                    array([0] * len(equal_buffers[-1]))
                )

        # Determine the maximum length among equal buffers to ensure proper overlay
        max_equal_length: int = len(max(equal_buffers, key=len))

        # Pad equal buffers to the same length for proper overlay
        equal_buffers = [
            audio_tools.pad_with_zeros(
                buffer,
                max_equal_length - len(buffer)
            )
            for buffer in equal_buffers
        ]

        engine_sound: NDArray = audio_tools.overlay(equal_buffers)

        # Simple Low-Pass Filter (Moving Average)
        # This reduces the "tinny" high-end at high RPMs
        window_size = 3
        engine_sound = convolve(engine_sound, ones(window_size)/window_size, mode='same')

        return audio_tools.in_playback_format(engine_sound)

    def generate_audio(self, sample_count: int) -> NDArray:
        """
        Generate audio samples for the engine.

        Parameters
        ----------
        sample_count (int):
            Number of samples requested.

        Returns
        -------
        NDArray
            Generated audio buffer.
        """

        if self.pop_mode:
            return self._generate_audio_pop_mode(sample_count)

        if sample_count < len(self._audio_buffer):

            output_buffer: NDArray = self._audio_buffer[:sample_count]
            self._audio_buffer = self._audio_buffer[sample_count:]

            return output_buffer

        # Generate new engine cycle audio and concatenate until we have enough samples
        engine_sound: NDArray = self._generate_audio_one_engine_cycle()

        while len(self._audio_buffer) + len(engine_sound) < sample_count:
            engine_sound = audio_tools.concat([engine_sound, engine_sound])

        # Calculate how many new samples we need to fill the request after using the existing buffer
        new_samples_count: int = sample_count - len(self._audio_buffer)

        output_buffer = audio_tools.concat([
            self._audio_buffer,
            engine_sound[:new_samples_count]
        ])

        self._audio_buffer = engine_sound[new_samples_count:]

        return output_buffer

    def throttle(self, fraction: float) -> None:
        """
        Adjust RPM based on throttle input.

        Parameters
        ----------
        fraction (float):
            Throttle input fraction (0.0 or 1.0).
        """
        # If throttle is fully pressed, increase RPM towards limiter
        if fraction == 1.0:
            if self.rpm < self.limiter_rpm:
                self.rpm += (100 / 4)
            else:
                fraction = 0.0

        # If throttle is released, allow RPM to drop gradually towards idle
        if fraction == 0.0:
            if self.rpm > self.idle_rpm:
                self.rpm -= min(50, self.rpm - self.idle_rpm)

    def adjust_rpm(
        self,
        current_rpm: int,
        motorcycle_limit: int,
        motorcycle_idle: int
    ) -> float:
        """
        Adjust engine RPM based on external motorcycle RPM input.

        Parameters
        ----------
        current_rpm (int):
            Current motorcycle RPM.
        motorcycle_limit (int):
            Maximum motorcycle RPM.
        motorcycle_idle (int):
            Motorcycle idle RPM.

        Returns
        -------
        float
            Adjusted engine RPM.
        """

        if current_rpm == 0:
            return 0

        # Clamp the motorcycle RPM to the defined limits
        if current_rpm > motorcycle_limit:
            current_rpm = motorcycle_limit
        elif current_rpm < motorcycle_idle:
            current_rpm = motorcycle_idle

        # Calculate the scale factor based on the motorcycle RPM relative to its idle and limit
        scale_factor: float = (
            (current_rpm - motorcycle_idle)
            / (motorcycle_limit - motorcycle_idle)
        )

        # Interpolate the engine RPM based on the scale factor
        adjusted_rpm: float = (
            self.idle_rpm +
            scale_factor * (self.limiter_rpm - self.idle_rpm)
        )

        self.rpm = adjusted_rpm
        return self.rpm