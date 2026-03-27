"""
Engine Audio Simulation Runtime (Refactored for Vehicle)
"""

import time
import math
import random
from threading import Thread
from typing import List

import keyboard  # type: ignore

from core.audio_device import AudioDevice
from core.engine import Engine
from core.vehicle import Slope, Vehicle
import core.vehicle_factory as vehicle_factory


# Allowable RPM overshoot beyond limiter before cut-off is applied
ALLOWABLE_RPM_AFTER_LIMITER: int = 500

# Amount of RPM reduced when limiter is triggered
LIMITER_RPM_CUT_OFF_VALUE: int = 500


class VehicleSimulator:
    """
    RPM simulator driven entirely by a Vehicle instance.

    This class simulates:
    - Engine RPM dynamics
    - Gear shifting behavior
    - Engine limiter logic
    - Idle fluctuation (realistic lope)
    - Keyboard input handling
    - Real-time audio playback
    """

    def __init__(self, vehicle: Vehicle) -> None:
        """
        Initialize the simulator with a specific vehicle configuration.

        Parameters
        ----------
        vehicle : Vehicle
            Vehicle configuration used to drive the simulation.

        Raises
        ------
        ValueError
            If the vehicle configuration is missing required audio assets.
        """
        self.vehicle: Vehicle = vehicle

        if vehicle.fire_sound is None:
            raise ValueError("Vehicle must have a fire_sound defined for audio simulation.")

        if vehicle.between_fire_sound is None:
            raise ValueError("Vehicle must have a between_fire_sound defined for audio simulation.")

        # Build engine directly from vehicle specifications
        self.engine: Engine = Engine(
            idle_rpm=vehicle.idle_rpm,
            limiter_rpm=vehicle.limiter_rpm,
            strokes=int(vehicle.strokes.value),
            cylinders=vehicle.cylinders,
            timing=vehicle.timing,
            fire_sound=vehicle.fire_sound,
            between_fire_sound=vehicle.between_fire_sound,
        )

        # Transmission setup (gear 0 represents neutral)
        self.gears: List[float] = [0.0] + vehicle.gears
        self.current_gear: int = 1

        # RPM state tracking
        self.rpm: float = vehicle.idle_rpm
        self.last_time: float = time.time()

        # Idle fluctuation time accumulator
        self._idle_time: float = 0.0

        # Vehicle physical characteristics
        self.slope = Slope.HEAVY
        self.stroke_length_mm = vehicle.stroke_length_mm
        self.optimal_shift_rpm = vehicle.optimal_shift_rpm

        # Simulation state
        self.running: bool = True

        # Precompute engine acceleration response factor
        self.acceleration_power: float = self._compute_engine_response()

    def _compute_engine_response(self) -> float:
        """
        Compute a base engine acceleration factor.

        The calculation factors in the maximum RPM capacity, the stroke length 
        (shorter strokes rev faster), and the cylinder count.

        Returns
        -------
        float
            Engine acceleration scaling factor.
        """
        revolution_factor = self.vehicle.limiter_rpm / 10000
        stroke_factor = 60 / self.stroke_length_mm
        cylinder_factor = max(0.7, self.vehicle.cylinders / 4)

        return revolution_factor * stroke_factor * cylinder_factor * 9000

    def _gear_load_multiplier(self) -> float:
        """
        Calculate load applied to the engine based on current gear.

        Returns
        -------
        float
            Load multiplier applied to engine acceleration.
        """
        if self.current_gear == 0:
            return 1.05

        load = 1.0 / (1 + self.current_gear * 0.55)
        return load * self.slope.value

    def _rpm_acceleration_curve(self, spread: float = 0.1) -> float:
        """
        Compute RPM acceleration modifier based on proximity to optimal shift RPM.

        Parameters
        ----------
        spread : float, optional
            The percentage of total RPM range used to calculate the shift band.

        Returns
        -------
        float
            Acceleration multiplier based on the power band.
        """
        shift_band = spread * self.vehicle.limiter_rpm
        distance = abs(self.rpm - self.optimal_shift_rpm)
        normalized_distance = min(distance / shift_band, 1.0)

        return 0.5 + (normalized_distance * 0.7)

    def _apply_limiter(self) -> None:
        """
        Apply engine limiter behavior.

        Reduces RPM by a set value once the overshoot threshold is exceeded.
        """
        if self.rpm >= self.vehicle.limiter_rpm + ALLOWABLE_RPM_AFTER_LIMITER:
            self.rpm -= LIMITER_RPM_CUT_OFF_VALUE

    def _apply_idle_fluctuation(self, delta_time: float) -> float:
        """
        Generate a fluctuating idle RPM offset.

        Simulates real engine idle instability caused by combustion inconsistency,
        mechanical variation, and slight fueling differences.

        Parameters
        ----------
        delta_time : float
            Time delta since last update.

        Returns
        -------
        float
            RPM offset to apply to idle.
        """
        self._idle_time += delta_time

        # Smooth oscillation (engine lope)
        base_wave = math.sin(self._idle_time * 0.1)

        # Add slight randomness for realism
        noise = random.uniform(-0.5, 1)

        # Combined fluctuation (~±40 RPM)
        return (base_wave + noise) * 40

    def _update_rpm(self, throttle: float, delta_time: float) -> None:
        """
        Update engine RPM based on throttle input and elapsed time.

        Parameters
        ----------
        throttle : float
            The current throttle input percentage (0.0 to 1.0).
        delta_time : float
            Elapsed time since the last frame.
        """
        load = self._gear_load_multiplier()
        curve = self._rpm_acceleration_curve()

        acceleration = self.acceleration_power * load * curve

        # Apply throttle acceleration
        self.rpm += acceleration * throttle * delta_time

        # Engine braking
        if throttle == 0:
            self.rpm -= self.acceleration_power * 0.35 * delta_time

        self._apply_limiter()

        if throttle == 0:
            # Apply fluctuating idle instead of static clamp
            idle_offset = self._apply_idle_fluctuation(delta_time)
            target_idle = self.vehicle.idle_rpm + idle_offset

            if self.rpm < target_idle:
                self.rpm = target_idle
        else:
            # Ensure RPM does not fall below base idle during throttle
            if self.rpm < self.vehicle.idle_rpm:
                self.rpm = self.vehicle.idle_rpm

    def upshift(self) -> None:
        """
        Shift up one gear if possible.

        Reduces RPM to simulate transmission engagement load.
        """
        if self.current_gear >= len(self.gears) - 1:
            return

        self.current_gear += 1
        self.rpm = max(self.vehicle.idle_rpm, self.rpm - 1000)

    def downshift(self) -> None:
        """
        Shift down one gear if possible.

        Increases RPM to simulate rev-matching or engine drag.
        """
        if self.current_gear == 0:
            return

        self.current_gear -= 1

        if self.current_gear > 0:
            self.rpm += 1000

        if self.rpm > self.vehicle.limiter_rpm:
            self.rpm = self.vehicle.limiter_rpm

    def _keyboard_loop(self) -> None:
        """
        Handle keyboard input in a separate thread.

        Listens for shifting commands and exit signals.
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
        Run the main simulation loop.

        Initializes the audio stream, starts input threads, and updates 
        simulation physics in real-time.
        """
        audio_device = AudioDevice()
        stream = audio_device.play_stream(self.engine.generate_audio)

        # Start keyboard listener in a background daemon thread
        Thread(target=self._keyboard_loop, daemon=True).start()

        while self.running:
            current_now = time.time()
            delta_time = current_now - self.last_time
            self.last_time = current_now

            throttle = 1.0 if keyboard.is_pressed("up") else 0.0

            self._update_rpm(throttle, delta_time)

            calculated_rpm = self.engine.adjust_rpm(
                int(self.rpm),
                self.vehicle.limiter_rpm + ALLOWABLE_RPM_AFTER_LIMITER,
                self.vehicle.idle_rpm,
            )

            print(
                f"{self.vehicle.name} | RPM: {int(calculated_rpm)} | Gear: {self.current_gear} | Throttle: {throttle:.2f}",
                end="\r",
            )

            time.sleep(0.005)

        stream.stop_stream()
        stream.close()


if __name__ == "__main__":
    # Initialize and run simulation using the Kawasaki ZX4RR configuration
    simulator = VehicleSimulator(vehicle_factory.XSR155())
    simulator.run()