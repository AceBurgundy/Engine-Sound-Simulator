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

from typing import Callable, Tuple, Any
import core.configurations as configurations
import pyaudio  # type: ignore

class AudioDevice:
    """
    Wrapper around the PyAudio interface for managing audio playback devices.

    This class encapsulates initialization of the PyAudio system and provides
    a method for creating a playback stream using a user-defined callback.

    The playback stream uses a callback-based model where audio frames are
    generated dynamically during playback.

    The audio configuration is defined by the `configurations` module.
    """

    def __init__(self) -> None:
        """
        Initialize the audio device.

        Creates an instance of the PyAudio interface used to manage audio
        streams and hardware interaction.
        """
        self._pyaudio: Any = pyaudio.PyAudio()

    def close(self) -> None:
        """
        Close the audio device and release PyAudio resources.

        This should be called when audio playback is no longer required to
        properly terminate the underlying PyAudio system.
        """
        self._pyaudio.terminate()

    def play_stream(self, callback: Callable[[int], Any]) -> Any:
        """
        Create and return a playback audio stream using a callback.

        The provided callback is invoked whenever the audio system requests
        additional frames to play.

        Parameters
        ----------
        callback (callable):
            A function that receives `frame_count` and returns a buffer of
            audio data to be played.

        Returns
        -------
        pyaudio.Stream:
            A PyAudio stream configured for callback-based audio playback.
        """

        def callback_wrapped(
            input_data: bytes,
            frame_count: int,
            time_info: dict,
            status_flags: int
        ) -> Tuple[Any, int]:
            """
            Internal wrapper adapting the user callback to the PyAudio
            callback signature.

            PyAudio expects a callback returning a tuple containing:
            - audio data
            - stream status flag

            Parameters
            ----------
            input_data (bytes):
                Input audio data (unused for output streams).

            frame_count (int):
                Number of audio frames requested.

            time_info (dict):
                Timing information provided by PyAudio.

            status_flags (int):
                Status flags indicating stream conditions.

            Returns
            -------
            tuple:
                (audio_buffer, pyaudio.paContinue)
            """
            return (callback(frame_count), pyaudio.paContinue)

        return self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=configurations.sample_rate,
            output=True,
            stream_callback=callback_wrapped
        )