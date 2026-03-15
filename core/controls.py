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

from typing import Any

from pynput import keyboard
from threading import Lock, Thread
import time

class _BlockingInputThread(Thread):
    """
    Thread responsible for capturing keyboard input without blocking the main program.

    The keyboard input listener used here operates in a blocking manner. Running it in a
    dedicated thread ensures the rest of the program (such as audio processing or engine
    simulation) can continue running even when no keyboard events are occurring.

    This thread tracks whether a key is currently held down and exposes that state to
    other parts of the program through the `space_held` attribute.
    """

    def __init__(self, lock: Lock) -> None:
        """
        Initialize the input capture thread.

        Parameters
        ----------
        lock (threading.Lock):
            A lock used to synchronize shared state access between threads.
        """
        super(_BlockingInputThread, self).__init__(daemon=True)
        self.lock: Lock = lock
        self.space_held: bool = False

    def on_press(self, key: Any) -> None:
        """
        Callback executed when a key is pressed.

        Parameters
        ----------
        key (pynput.keyboard.Key | pynput.keyboard.KeyCode):
            The key that was pressed.
        """
        # Mark that a key is currently being held down
        self.space_held = True

    def on_release(self, key: Any) -> None:
        """
        Callback executed when a key is released.

        Parameters
        ----------
        key (pynput.keyboard.Key | pynput.keyboard.KeyCode):
            The key that was released.
        """
        # Mark that no key is currently held down
        self.space_held = False

    def run(self) -> None:
        """
        Start the keyboard listener inside the thread.

        The listener runs asynchronously and updates the `space_held`
        state whenever key events occur.
        """
        listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )

        # Start the listener in a non-blocking manner
        listener.start()


def capture_input(engine: Any) -> None:
    """
    Capture keyboard input and control the engine throttle.

    The throttle is engaged while a key is held down and released when
    no key is pressed.

    Parameters
    ----------
    engine (object):
        An engine-like object that exposes a `throttle(value)` method.
    """
    print('Press Ctrl+C to exit, any key to rev\n')

    lock: Lock = Lock()

    # Create and start the input monitoring thread
    blocking_input_thread: _BlockingInputThread = _BlockingInputThread(lock)
    blocking_input_thread.start()

    while True:
        with lock:
            # Apply throttle based on whether a key is currently held
            engine.throttle(1.0 if blocking_input_thread.space_held else 0.0)

        # Small sleep to reduce CPU usage while polling input state
        time.sleep(0.01)  # Normal delay
        # time.sleep(0.003)  # Alternative faster polling interval