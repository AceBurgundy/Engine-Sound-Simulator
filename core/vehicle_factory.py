from core.vehicle import Vehicle, EngineStrokeType, Slope
import core.synthesisation as synthesisation
import core.audio_tools as audio_tools
from numpy.typing import NDArray


# Default synthesized fire sound configuration.
# Uses a 100 Hz sine wave for a smoother base tone.
_fire_sound: NDArray = synthesisation.sine_wave_note(
    frequency=10,
    duration=1
)

# Normalize volume to prevent clipping.
audio_tools.normalize_volume(_fire_sound)

# Apply fast exponential decay to simulate sharp combustion pulses.
audio_tools.exponential_volume_dropoff(
    _fire_sound,
    duration=0.01,
    base=20
)

class BaseVehicle(Vehicle):
    """
    Base vehicle class to reduce repetition in vehicle definitions.

    This class provides default values for:
    - fire_sound
    - between_fire_sound

    It allows derived classes to focus only on unique vehicle parameters.
    """

    def __init__(self, name: str, **kwargs):
        """
        Initialize a base vehicle with optional overrides.

        Parameters
        ----------
        name : str
            Name of the vehicle.
        **kwargs : dict
            Additional parameters passed to the Vehicle dataclass.
        """
        super().__init__(
            name=name,
            # Use provided fire sound or fallback to default
            fire_sound=kwargs.pop("fire_sound", _fire_sound),
            # Default silence between combustion events
            between_fire_sound=kwargs.pop(
                "between_fire_sound",
                synthesisation.silence(1)
            ),
            **kwargs
        )


class MT10_SP(BaseVehicle):
    """
    Yamaha MT-10 SP configuration.

    Inline-four engine with crossplane crank timing,
    producing uneven firing intervals for a distinctive sound.
    """

    def __init__(self, wave_sound: NDArray = _fire_sound):
        """
        Initialize Yamaha MT-10 SP configuration.

        Parameters
        ----------
        wave_sound : NDArray, optional
            Custom waveform for engine firing sound.
        """
        super().__init__(
            name="Yamaha MT-10 SP",
            idle_rpm=1300,
            limiter_rpm=11500,
            strokes=EngineStrokeType.FOUR_STROKE,
            cylinders=4,
            timing=[270, 180, 90, 180],
            gears=[2.600, 2.176, 1.842, 1.578, 1.381, 1.250],
            stroke_length_mm=50.9,
            optimal_shift_rpm=10500,
            fire_sound=wave_sound,
        )


class R1M(BaseVehicle):
    """
    Yamaha R1M configuration.

    High-revving inline-four with crossplane crankshaft,
    optimized for aggressive track performance.
    """

    def __init__(self, wave_sound: NDArray = _fire_sound):
        """
        Initialize Yamaha R1M configuration.

        Parameters
        ----------
        wave_sound : NDArray, optional
            Custom waveform for engine firing sound.
        """
        super().__init__(
            name="Yamaha R1M",
            idle_rpm=1300,
            limiter_rpm=14500,
            strokes=EngineStrokeType.FOUR_STROKE,
            cylinders=4,
            timing=[270, 180, 90, 180],
            gears=[2.600, 2.176, 1.842, 1.578, 1.381, 1.250],
            stroke_length_mm=50.9,
            optimal_shift_rpm=7000,
            fire_sound=wave_sound,
        )


class Ninja400(BaseVehicle):
    """
    Kawasaki Ninja 400 configuration.

    Parallel-twin engine with balanced performance and smooth delivery.
    """

    def __init__(self, wave_sound: NDArray = _fire_sound):
        """
        Initialize Kawasaki Ninja 400 configuration.

        Parameters
        ----------
        wave_sound : NDArray, optional
            Custom waveform for engine firing sound.
        """
        super().__init__(
            name="Kawasaki Ninja 400",
            idle_rpm=1200,
            limiter_rpm=12000,
            strokes=EngineStrokeType.FOUR_STROKE,
            cylinders=2,
            timing=[180, 540],
            gears=[2.929, 2.056, 1.619, 1.333, 1.154, 1.037],
            stroke_length_mm=51.8,
            optimal_shift_rpm=10500,
            fire_sound=wave_sound,
        )


class ZX4RR(BaseVehicle):
    """
    Kawasaki ZX-4RR configuration.

    High-revving inline-four engine with uniform firing intervals.
    Designed for precision and track-focused performance.
    """

    def __init__(self, wave_sound: NDArray = _fire_sound):
        """
        Initialize Kawasaki ZX-4RR configuration.

        Parameters
        ----------
        wave_sound : NDArray, optional
            Custom waveform for engine firing sound.
        """
        super().__init__(
            name="Kawasaki ZX-4RR",
            idle_rpm=1500,
            limiter_rpm=16000,
            strokes=EngineStrokeType.FOUR_STROKE,
            cylinders=4,
            timing=[180, 180, 180, 180],
            gears=[2.929, 2.056, 1.619, 1.333, 1.154, 1.037],
            stroke_length_mm=39.1,
            optimal_shift_rpm=14500,
            fire_sound=wave_sound,
        )


class XSR155(BaseVehicle):
    """
    Yamaha XSR155 configuration.

    Single-cylinder engine with a flat torque curve,
    suitable for smooth and predictable power delivery.
    """

    def __init__(self, wave_sound: NDArray = _fire_sound):
        """
        Initialize Yamaha XSR155 configuration.

        Parameters
        ----------
        wave_sound : NDArray, optional
            Custom waveform for engine firing sound.
        """
        super().__init__(
            name="Yamaha XSR155",
            idle_rpm=1500,
            limiter_rpm=10500,
            strokes=EngineStrokeType.FOUR_STROKE,
            cylinders=1,
            timing=[720],
            gears=[2.833, 1.875, 1.363, 1.143, 0.957, 0.840],
            stroke_length_mm=58.7,
            optimal_shift_rpm=8500,
            fire_sound=wave_sound,
        )