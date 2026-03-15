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

"""
Audio configuration constants used across the audio processing system.

These settings define the playback sample rate, maximum amplitude for
16-bit audio, and how multiple audio buffers should be merged.
"""

# Standard audio sampling rate in Hertz (samples per second).
# 44,100 Hz is the common sampling rate used for CD-quality audio.
sample_rate: int = 44100


# Maximum amplitude value for signed 16-bit audio.
#
# Calculation:
# 2^(bits - 1) - 1
#
# For 16-bit audio:
# 2^(16 - 1) - 1 = 32767
#
# This value is used when normalizing audio buffers to prevent clipping.
max_16bit = 2 ** (16 - 1) - 1  # 32,767


# Defines the method used when merging multiple audio buffers.
#
# Possible values:
# - "max":   Use the maximum sample value across buffers
# - "average": Average the sample values across buffers
#
# Added by Omar.
sound_merge_method: str = "average"