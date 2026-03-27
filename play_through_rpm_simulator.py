"""
Engine Audio Simulation Runtime (Refactored for Vehicle)
"""

import time
from threading import Thread
from typing import List

import keyboard  # type: ignore

from core.audio_device import AudioDevice
from core.engine import Engine
from core.vehicle import Slope, Vehicle  # Central vehicle data model
import core.vehicle_factory as vehicle_factory  # Factory for creating vehicle instances

# Allowable RPM overshoot beyond limiter before cut-off is applied
ALLOWABLE_RPM_AFTER_LIMITER: int = 500

# Amount of RPM reduced when limiter is triggered
LIMITER_RPM_CUT_OFF_VALUE: int = 500

class VehicleSimulator:
    """
    RPM simulator driven entirely by a Vehicle instance.

    This class simulates engine behavior, including:
    - RPM acceleration and decay
    - Gear shifting
    - Engine limiter behavior
    - Real-time keyboard input handling
    - Audio playback based on engine state
    """

    def __init__(self, vehicle: Vehicle) -> None:
        """
        Initialize the simulator with a specific vehicle configuration.

        Parameters
        ----------
        vehicle : Vehicle
            Vehicle configuration used to drive the simulation.
        """
        self.vehicle: Vehicle = vehicle

        if vehicle.fire_sound is None:
            raise ValueError("Vehicle must have a fire_sound defined for audio simulation.")
        
        if vehicle.between_fire_sound is None:
            raise ValueError("Vehicle must have a fire_sound defined for audio simulation.")
        
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

        This combines multiple physical characteristics:
        - Rev range scaling
        - Stroke length influence
        - Cylinder count normalization

        Returns
        -------
        float
            Engine acceleration scaling factor.
        """
        # Higher limiter RPM increases responsiveness
        rev_factor = self.vehicle.limiter_rpm / 10000

        # Shorter stroke engines rev faster
        stroke_factor = 60 / self.stroke_length_mm

        # Normalize cylinder contribution (minimum baseline)
        cylinder_factor = max(0.7, self.vehicle.cylinders / 4)

        return rev_factor * stroke_factor * cylinder_factor * 9000

    def _gear_load_multiplier(self) -> float:
        """
        Calculate load applied to the engine based on current gear.

        Lower gears apply less load, allowing faster RPM increase.
        Higher gears increase load, reducing acceleration.

        Returns
        -------
        float
            Load multiplier applied to engine acceleration.
        """
        if self.current_gear == 0:
            # Neutral gear slightly increases responsiveness
            return 1.05

        load = 1.0 / (1 + self.current_gear * 0.55)

        # Apply torque curve slope characteristic
        return load * self.slope.value

    def _rpm_acceleration_curve(self, spread: float = 0.1) -> float:
        """
        Compute RPM acceleration modifier based on proximity to optimal shift RPM.

        This simulates reduced acceleration near the optimal shift band.

        Parameters
        ----------
        spread : float, optional
            Width of the optimal shift band as a fraction of limiter RPM.

        Returns
        -------
        float
            Acceleration multiplier.
        """
        shift_band = spread * self.vehicle.limiter_rpm

        # Distance from optimal shift RPM
        distance = abs(self.rpm - self.optimal_shift_rpm)

        # Normalize distance within shift band
        normalized = min(distance / shift_band, 1.0)

        return 0.5 + (normalized * 0.7)

    def _apply_limiter(self) -> None:
        """
        Apply engine limiter behavior.

        If RPM exceeds allowable threshold, reduce RPM sharply
        to simulate fuel cut or ignition cut.
        """
        if self.rpm >= self.vehicle.limiter_rpm + ALLOWABLE_RPM_AFTER_LIMITER:
            self.rpm -= LIMITER_RPM_CUT_OFF_VALUE

    def _update_rpm(self, throttle: float, dt: float) -> None:
        """
        Update engine RPM based on throttle input and elapsed time.

        Parameters
        ----------
        throttle : float
            Throttle input (0.0 to 1.0).
        dt : float
            Time delta since last update (seconds).
        """
        load = self._gear_load_multiplier()
        curve = self._rpm_acceleration_curve()

        # Compute acceleration force
        acceleration = self.acceleration_power * load * curve

        # Apply throttle-based acceleration
        self.rpm += acceleration * throttle * dt

        # Apply engine braking when throttle is released
        if throttle == 0:
            self.rpm -= self.acceleration_power * 0.35 * dt

        # Apply limiter logic
        self._apply_limiter()

        # Prevent RPM from dropping below idle
        if self.rpm < self.vehicle.idle_rpm:
            self.rpm = self.vehicle.idle_rpm

    def upshift(self) -> None:
        """
        Shift up one gear if possible.

        Reduces RPM slightly to simulate gear ratio change.
        """
        if self.current_gear >= len(self.gears) - 1:
            return

        self.current_gear += 1

        # Drop RPM after upshift
        self.rpm = max(self.vehicle.idle_rpm, self.rpm - 1000)

    def downshift(self) -> None:
        """
        Shift down one gear if possible.

        Increases RPM to simulate engine speed matching.
        """
        if self.current_gear == 0:
            return

        self.current_gear -= 1

        if self.current_gear > 0:
            self.rpm += 1000

        # Clamp RPM to limiter
        if self.rpm > self.vehicle.limiter_rpm:
            self.rpm = self.vehicle.limiter_rpm

    def _keyboard_loop(self) -> None:
        """
        Handle keyboard input in a separate thread.

        Controls:
        - Q: Upshift
        - Space: Downshift
        - Up Arrow: Throttle
        - ESC: Exit simulation
        """
        while self.running:

            if keyboard.is_pressed("q"):
                self.upshift()
                time.sleep(0.18)  # Debounce input

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

        This includes:
        - Audio streaming
        - RPM updates
        - Keyboard input handling
        - Console output
        """
        audio_device = AudioDevice()

        # Start audio stream using engine audio generator
        stream = audio_device.play_stream(self.engine.generate_audio)

        # Start keyboard input listener in background thread
        Thread(target=self._keyboard_loop, daemon=True).start()

        while self.running:
            now = time.time()
            dt = now - self.last_time
            self.last_time = now

            # Throttle input (binary for simplicity)
            throttle = 1.0 if keyboard.is_pressed("up") else 0.0

            # Update engine RPM
            self._update_rpm(throttle, dt)

            # Adjust RPM through engine model (clamping and smoothing)
            rpm = self.engine.adjust_rpm(
                int(self.rpm),
                self.vehicle.limiter_rpm + ALLOWABLE_RPM_AFTER_LIMITER,
                self.vehicle.idle_rpm,
            )

            # Display current simulation state
            print(
                f"{self.vehicle.name} | RPM: {int(rpm)} | Gear: {self.current_gear} | Throttle: {throttle:.2f}",
                end="\r",
            )

            time.sleep(0.005)

        # Cleanup audio stream
        stream.stop_stream()
        stream.close()

simulator = VehicleSimulator(vehicle_factory.R1M())
simulator.run()