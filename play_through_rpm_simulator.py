"""
Engine Audio Simulation Runtime
"""

import time
from threading import Thread
from typing import List, Optional, Any, Union

import keyboard  # type: ignore

import core.synthesisation as synthesisation
from core.audio_device import AudioDevice
from core.engine import Engine
from core import audio_tools

from enum import Enum

class Slope(Enum):
    """
    Represents simulated road resistance.

    Higher slope = more load on the engine.
    """

    FLAT = 1.0
    LIGHT = 0.85
    MEDIUM = 0.70
    HEAVY = 0.55
    EXTREME = 0.40

class EngineStrokeType(Enum):
    """
    Enumeration describing the number of strokes per engine cycle.

    Two-stroke engines complete a power cycle in two piston strokes,
    while four-stroke engines complete the cycle in four piston strokes.
    """

    TWO_STROKE = 2
    FOUR_STROKE = 4

ALLOWABLE_RPM_AFTER_LIMITER: int = 500
LIMITER_RPM_CUT_OFF_VALUE: int = 500

class VehicleSimulator:
    """
    RPM Builder that simulates throttle, gears and RPM physics.
    """

    def __init__(
        self, 
        idle_rpm: int,
        limiter_rpm: int,
        strokes: EngineStrokeType,
        cylinders: int,
        timing: List[Union[int, float]],
        fire_sound: Any,
        between_fire_sound: Any,
        gears: List[float],
        slope: Slope,
        stroke_length_mm: float,
        optimal_shift_rpm: Optional[int] = None,
    ) -> None:
        """
        Parameters
        ----------
        idle_rpm (int)
            Engine idle RPM.

        limiter_rpm (int)
            Maximum engine RPM before limiter.

        strokes (EngineStrokeType)
            Stroke type of the engine. Either 2 or 4 stroke.

        cylinders (int)
            Cylinder count.

        timing (List[Union[int, float]])
            Combustion timing list.

        fire_sound (Any)
            Sound played on combustion.

        between_fire_sound (Any)
            Sound played between combustion events.

        gears (List[float])
            Gear ratios list.

        slope (Slope)
            Simulated () road slope affecting engine load.

        stroke_length_mm (float)
            Used to determine RPM acceleration characteristics.

        optimal_shift_rpm (Optional[int] = None)
            Typical upshift RPM.
        """

        self.engine: Engine = Engine(
            idle_rpm=idle_rpm,
            limiter_rpm=limiter_rpm,
            strokes=int(strokes.value),
            cylinders=cylinders,
            timing=timing,
            fire_sound=fire_sound,
            between_fire_sound=between_fire_sound
        )

        # Neutral gear added automatically
        self.gears: List[float] = [0.0] + gears

        self.current_gear: int = 1

        self.idle_rpm: int = idle_rpm
        self.limiter_rpm: int = limiter_rpm

        self.rpm: float = idle_rpm

        self.slope: Slope = slope

        self.stroke_length_mm: float = stroke_length_mm
        self.optimal_shift_rpm: int = optimal_shift_rpm or int(limiter_rpm * 0.85)

        self.running: bool = True

        self.last_time: float = time.time()

        # Compute acceleration characteristics
        self.acceleration_power: float = self._compute_engine_response()

    def _compute_engine_response(self) -> float:
        """
        Calculate how quickly RPM increases.

        High revving engines accelerate faster.
        """

        rev_factor: float = self.limiter_rpm / 10000
        stroke_factor: float = 60 / self.stroke_length_mm
        cylinder_factor: float = max(0.7, self.engine.cylinders / 4)

        return rev_factor * stroke_factor * cylinder_factor * 9000

    def upshift(self) -> None:
        """
        Shift up a gear.
        """

        if self.current_gear >= len(self.gears) - 1:
            return

        self.current_gear += 1
        self.rpm -= 1000

        if self.rpm < self.idle_rpm:
            self.rpm = self.idle_rpm

    def downshift(self) -> None:
        """
        Shift down a gear.
        """

        if self.current_gear == 0:
            return

        self.current_gear -= 1

        # Only rev match if still in a drive gear
        if self.current_gear > 0:
            self.rpm += 1000

        if self.rpm > self.limiter_rpm:
            self.rpm = self.limiter_rpm

    def _gear_load_multiplier(self) -> float:
        """
        Simulates drivetrain load.

        Higher gears = heavier load = slower RPM climb.
        """

        if self.current_gear == 0:
            return 1.05

        # Non-linear load growth
        load = 1.0 / (1 + self.current_gear * 0.55)

        # Apply slope resistance
        return load * self.slope.value
    
    def _rpm_acceleration_curve(self, rpm_curve_spread: float = 0.1) -> float:
        """
        Compute RPM acceleration multiplier based on the current RPM band.

        RPM increases quickly at low RPM,
        slows near the optimal shift RPM,
        and slightly increases again approaching the limiter.

        Parameters
        ----------
        rpm_curve_spread (float):
            Fraction of limiter RPM used to define the width of the shift band.

        Returns
        -------
        float
            Acceleration multiplier applied to RPM change.
        """
        # Define a band around the optimal shift RPM where acceleration slows down
        shift_band: float = rpm_curve_spread * self.limiter_rpm
        # Calculate distance from optimal shift RPM
        distance_from_optimal: float = abs(self.rpm - self.optimal_shift_rpm)

        normalized_distance: float = min(distance_from_optimal / shift_band, 1.0)

        return 0.5 + (normalized_distance * 0.7)

    def _apply_limiter(self) -> None:
        """
        Simulate fuel cut limiter behaviour.

        Allows RPM to exceed limiter by a small amount,
        then cuts RPM sharply to simulate ignition cut.
        """

        limiter_threshold: float = self.limiter_rpm + ALLOWABLE_RPM_AFTER_LIMITER

        if self.rpm >= limiter_threshold:
            self.rpm -= LIMITER_RPM_CUT_OFF_VALUE

    def _update_rpm(self, throttle: float, deltatime: float) -> None:
        """
        Update engine RPM based on throttle input and physics.
        """
        load_multiplier: float = self._gear_load_multiplier()
        rpm_curve_multiplier: float = self._rpm_acceleration_curve()

        acceleration: float = self.acceleration_power * load_multiplier * rpm_curve_multiplier

        # Throttle acceleration
        self.rpm += acceleration * throttle * deltatime

        # Engine braking
        if throttle == 0:
            braking: float = self.acceleration_power * 0.35 * deltatime
            self.rpm -= braking

        # Apply limiter behaviour
        self._apply_limiter()

        # Prevent RPM falling below idle
        if self.rpm < self.idle_rpm:
            self.rpm = self.idle_rpm

    def _keyboard_loop(self) -> None:
        """
        Listen for keyboard input.
        """

        while self.running:

            if keyboard.is_pressed("q"):
                self.upshift()
                time.sleep(0.18)

            if keyboard.is_pressed("space"):
                self.downshift()
                time.sleep(0.18)

            if keyboard.is_pressed("esc"):
                self.running = False
                break

            time.sleep(0.01)

    def run(self) -> None:
        """
        Start the RPM simulation and audio playback.
        """

        audio_device: AudioDevice = AudioDevice()
        stream: Any = audio_device.play_stream(self.engine.generate_audio)

        keyboard_thread: Thread = Thread(target=self._keyboard_loop)
        keyboard_thread.daemon = True
        keyboard_thread.start()

        while self.running:

            current_time: float = time.time()
            delta_time: float = current_time - self.last_time
            self.last_time = current_time

            throttle: float = 1.0 if keyboard.is_pressed("up") else 0.0

            self._update_rpm(throttle, delta_time)

            rpm: float = self.engine.adjust_rpm(
                int(self.rpm),
                self.limiter_rpm + ALLOWABLE_RPM_AFTER_LIMITER,
                self.idle_rpm
            )

            print(
                f"RPM: {int(rpm)} | Gear: {self.current_gear} | Throttle: {throttle:.2f}",
                end="\r"
            )

            time.sleep(0.005)

        stream.stop_stream()
        stream.close()

_fire_sound = synthesisation.sine_wave_note(
    frequency=250,
    duration=1
)

audio_tools.normalize_volume(_fire_sound)

audio_tools.exponential_volume_dropoff(
    _fire_sound,
    duration=0.01,
    base=5
)

vehicle_simulator: VehicleSimulator = VehicleSimulator(

    idle_rpm=1500,
    limiter_rpm=11000,

    strokes=EngineStrokeType.FOUR_STROKE,
    cylinders=1,
    timing=[0],

    fire_sound=_fire_sound,
    between_fire_sound=synthesisation.silence(1),

    gears=[2.833, 1.875, 1.364, 1.143, 0.957, 0.840],

    slope=Slope.HEAVY,

    stroke_length_mm=58,
    optimal_shift_rpm=5000
)

vehicle_simulator.run()