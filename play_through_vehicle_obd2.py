"""
Main runtime script for generating engine audio based on live OBD2 RPM data.

This script:
1. Connects to an OBD2 interface to read engine RPM.
2. Generates synthetic engine audio using the Engine simulation.
3. Plays the generated audio using a PyAudio output stream.
4. Dynamically adjusts simulated engine RPM based on the motorcycle RPM.
5. Controls system audio muting depending on whether the engine is running.
"""

from ctypes import POINTER, cast
import time
from typing import Optional

from comtypes import CLSCTX_ALL  # type: ignore
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore

import obd  # type: ignore
import synthesisation  # type: ignore
from core.audio_device import AudioDevice
from core.engine_factory import v2_45_degrees
from core.engine import Engine
from core import audio_tools

# Initialize the OBD connection.
# The port string is explicitly provided (COM3). Depending on the system,
# this may be auto-detected by the OBD library if omitted.
connection: obd.OBD = obd.OBD(portstr="COM3")


# Retrieve the default audio output device using PyCAW
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_,
    CLSCTX_ALL,
    None
)

volume: IAudioEndpointVolume = cast(interface, POINTER(IAudioEndpointVolume))

# Get the current system master volume level in decibels
current_volume_db: float = volume.GetMasterVolumeLevel()

# Generate the combustion sound used by the engine simulation
_fire_sound = synthesisation.sine_wave_note(frequency=250, duration=1)

# Normalize the generated waveform to the maximum allowed amplitude
audio_tools.normalize_volume(_fire_sound)

# Apply a short exponential drop-off to shape the combustion sound
audio_tools.exponential_volume_dropoff(
    _fire_sound,
    duration=0.01,
    base=5
)

# Initialize the engine simulation
engine: Engine = v2_45_degrees(wave_sound=_fire_sound)

# Initialize the audio device and start playback stream
audio_device: AudioDevice = AudioDevice()
stream = audio_device.play_stream(engine.generate_audio)

def get_obd_rpm() -> Optional[float]:
    """
    Retrieve the current engine RPM from the OBD2 interface.

    Returns
    -------
    int | None
        The RPM value reported by the OBD2 system.
        Returns None if the response is invalid or unavailable.
    """
    # OBD command for retrieving engine RPM
    command = obd.commands.RPM

    # Send the command and obtain the response
    response = connection.query(command)

    # Check if the response contains valid data
    if response.is_null():
        return None

    # RPM value is provided in the 'magnitude' attribute
    return response.value.magnitude

# Initialize a variable to hold the smoothed RPM value for audio generation
smoothed_rpm: float = 0

# Continuously poll the OBD2 system and update the simulated engine RPM
while True:
    # Read RPM from the OBD2 interface
    rpm_obd = float(get_obd_rpm() or 0)

    smoothed_rpm = (
        smoothed_rpm * 0.8
        + rpm_obd * 0.2
    )

    if smoothed_rpm is not None:
        # If RPM is zero, mute system audio (engine off)
        if smoothed_rpm == 0:
            volume.SetMute(1, None)

        else:
            # Unmute system audio when engine is running
            volume.SetMute(0, None)

            # Adjust the simulated engine RPM using motorcycle data
            adjusted_rpm: float = engine.adjust_rpm(
                int(smoothed_rpm),
                int(engine.limiter_rpm) + 500, # 500 is an arbitrary buffer to allow for some overshoot beyond the limiter
                int(engine.idle_rpm)
            )
    
    time.sleep(0.02)
